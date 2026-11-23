"""Telegram join-gated downloader using the existing local rednote-downloader API.

Requires BOT_TOKEN and CHANNEL_USERNAME environment variables.
The Node service must be running separately on 127.0.0.1:3000.
"""
import json
import os
import re
import time
from pathlib import Path

import requests

MAX_UPLOAD = 45 * 1024 * 1024
LOCAL_API = os.environ.get("REDNOTE_LOCAL_API", "http://127.0.0.1:3107")
URL_RE = re.compile(r"https?://[^\s<>]+", re.I)


def telegram_request(token, method, *, data=None, files=None, timeout=35):
    # Never include the token-bearing URL in errors shown to end users/logs.
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/{method}",
            data=data or {}, files=files, timeout=timeout,
        )
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise RuntimeError(f"Telegram {method} request failed ({type(exc).__name__})") from None
    if not response.ok or not payload.get("ok"):
        raise RuntimeError(f"Telegram {method}: {payload.get('description', 'request rejected')}")
    return payload.get("result")


class Bot:
    def __init__(self, token, channel, base_url=LOCAL_API):
        if not re.fullmatch(r"\d+:[A-Za-z0-9_-]{20,}", token):
            raise ValueError("BOT_TOKEN format invalid")
        if not re.fullmatch(r"@[A-Za-z0-9_]{5,}", channel):
            raise ValueError("CHANNEL_USERNAME must be @public_channel_username")
        self.token = token
        self.channel = channel
        self.base_url = base_url.rstrip("/")
        self.offset = 0

    def call(self, method, **data):
        return telegram_request(self.token, method, data=data)

    def send(self, chat_id, message, keyboard=None):
        data = {"chat_id": chat_id, "text": message}
        if keyboard:
            data["reply_markup"] = json.dumps(keyboard)
        return self.call("sendMessage", **data)

    def joined(self, user_id):
        member = self.call("getChatMember", chat_id=self.channel, user_id=user_id)
        status = member.get("status")
        return status in ("member", "administrator", "creator") or (
            status == "restricted" and member.get("is_member", False)
        )

    def join_prompt(self, chat_id):
        self.send(chat_id, "📢 Video Download အသုံးပြုရန် Channel ကို Join ပါ။", {
            "inline_keyboard": [
                [{"text": "📢 Join Channel", "url": "https://t.me/" + self.channel[1:]}],
                [{"text": "✅ Verify Join", "callback_data": "verify"}],
            ]
        })

    def resolve_download(self, url):
        # API stores the downloaded files on the SAME device as this Python bot.
        try:
            response = requests.post(
                self.base_url + "/api/resolve", json={"input": url, "download": True},
                timeout=(15, 420),
            )
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise RuntimeError(f"Local downloader request failed: {type(exc).__name__}; check server and RedNote CDN") from None
        if not response.ok or not payload.get("ok"):
            error = str(payload.get("error") or "Downloader could not resolve this link")
            if error.strip().lower() == "terminated":
                raise RuntimeError("RedNote media CDN closed the connection. All available video URLs will be retried; if this persists, try another accessible public link or your own authorized RedNote session.")
            raise RuntimeError(error[:180])
        media = payload.get("note", {}).get("media") or []
        if not media:
            raise RuntimeError("Downloader returned no media files")
        return media

    def upload_file(self, chat_id, item):
        # The server returns an absolute local file path after downloading.
        file_path = Path(str(item.get("absolutePath") or ""))
        base_dir = (Path(__file__).resolve().parent / "rednote-downloader" / "data").resolve()
        resolved = file_path.resolve()
        if not file_path.is_absolute() or not resolved.is_relative_to(base_dir) or not resolved.is_file():
            raise RuntimeError("Downloaded file not found in configured data directory")
        size = resolved.stat().st_size
        if size > MAX_UPLOAD:
            raise RuntimeError(f"File is too large for configured 45 MB limit ({size // (1024*1024)} MB)")
        if size <= 0:
            raise RuntimeError("Downloaded file is empty")
        # A failed connection before any HTTP response can be transient. Reopen the
        # stream on retry so Telegram receives the file from byte zero. A timeout
        # after upload is deliberately NOT retried: Telegram may have delivered it.
        for attempt in range(3):
            try:
                with resolved.open("rb") as stream:
                    return telegram_request(self.token, "sendDocument", data={"chat_id": chat_id},
                                            files={"document": (resolved.name, stream)}, timeout=200)
            except RuntimeError as exc:
                if "(ConnectionError)" not in str(exc) or attempt == 2:
                    raise
                time.sleep(2 ** attempt)

    def download_video(self, chat_id, url):
        self.send(chat_id, "⏳ Video Download လုပ်နေပါတယ်...")
        try:
            media = self.resolve_download(url)
            if len(media) > 10:
                raise RuntimeError("Too many files in post (max 10)")
            for item in media:
                self.upload_file(chat_id, item)
            self.send(chat_id, f"✅ Download အောင်မြင်ပါပြီ။ ဖိုင် {len(media)} ခု ပို့ပြီးပါပြီ။")
        except Exception as exc:
            message = str(exc)
            # Do not echo Telegram token, remote cookie, or long signed URLs.
            message = message.replace(self.token, "[TOKEN_REDACTED]")
            message = re.sub(r"https?://\S+", "[URL]", message)
            self.send(chat_id, "❌ Download မအောင်မြင်ပါ: " + message[:180])

    def process(self, update):
        if "callback_query" in update:
            callback = update["callback_query"]
            self.call("answerCallbackQuery", callback_query_id=callback["id"])
            chat_id = callback["message"]["chat"]["id"]
            if self.joined(callback["from"]["id"]):
                self.send(chat_id, "✅ Verified! Video Link ပို့ပါ။")
            else:
                self.join_prompt(chat_id)
            return
        message = update.get("message") or {}
        text = (message.get("text") or "").strip()
        if not text:
            return
        chat_id = message["chat"]["id"]
        user_id = message["from"]["id"]
        if not self.joined(user_id):
            self.join_prompt(chat_id)
        elif text.startswith("/start"):
            self.send(chat_id, "🎬 RedNote Video Link ပို့ပါ။")
        elif URL_RE.search(text):
            self.download_video(chat_id, URL_RE.search(text).group(0))
        else:
            self.send(chat_id, "🔗 Video Link ပို့ပေးပါ။")

    def run(self):
        me = self.call("getMe")
        print(f"Bot authenticated: @{me['username']}; downloader: {self.base_url}", flush=True)
        # The channel join check requires admin access to the channel.
        while True:
            try:
                updates = self.call("getUpdates", offset=self.offset, timeout=10)
                for update in updates:
                    self.offset = update["update_id"] + 1
                    try:
                        self.process(update)
                    except Exception as exc:
                        print(f"Update failed: {type(exc).__name__}: {str(exc).replace(self.token, '[TOKEN]')[:200]}", flush=True)
            except KeyboardInterrupt:
                print("Bot stopped", flush=True)
                return
            except Exception as exc:
                print(f"Polling error: {type(exc).__name__}: {str(exc).replace(self.token, '[TOKEN]')[:200]}", flush=True)
                time.sleep(5)


if __name__ == "__main__":
    Bot(os.environ.get("BOT_TOKEN", ""), os.environ.get("CHANNEL_USERNAME", "")).run()
