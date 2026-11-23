# Telegram Bot — Windows updated build

## Applied changes
- Windows PowerShell 5.1 startup script now checks node.exe version without fragile inline quoting.
- Downloader uses a dedicated local port 3107 so an older service on 3000 cannot silently serve stale code.
- Python bot uses local port 3107 and a longer HTTP read timeout for long media transfers.
- XHS media streaming now has a timeout for the **response body**, not just response headers. A stalled stream is cancelled, partial file is removed and a same-URL retry or fallback CDN URL is attempted.
- Existing RedNote video primary and backup URLs are retained. Existing channel join requirements remain.

## Quick Windows startup
1. Close the **old** PowerShell window running the previous Telegram bot to avoid two polling processes for the same bot token. Keep any existing data files safe; no deletion is needed.
2. Extract this ZIP into a NEW folder (e.g. Downloads\\TelegramBot_Updated_3107). Do not mix its files into the old Downloads project.
3. In that extracted folder, click the File Explorer address bar, type `powershell`, and press Enter.
4. Run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\start_windows.ps1
```

5. Type public channel handle (e.g. @FreeShareMM) and paste only a freshly revoked-and-reissued Telegram BotFather token when asked. Token is hidden. Do not share screenshot containing token. Bot must be a channel administrator for reliable getChatMember checks.
6. Telegram: send /start and test a link that is publicly accessible and you are permitted to download.

## Verification
- Python unittest: 5 passed.
- Node.js unit tests: 95 passed (including body-stall/retry test).
- Live RedNote access and real Telegram file delivery have **not** been verified in this environment. A remote CDN may still terminate connections or require authorized login; no code change guarantees bypassing site restrictions.
- Existing laptop browser/Phone need not be involved in the bot runtime when both server and bot run from the same folder on Windows.


## 2026-11-22 စစ်ဆေးမှု
- Startup သည် port အသစ်ကို အလိုအလျောက်ရွေးပြီး Project ထဲက Node server ကို အသစ်စတင်မည်။ Server အဟောင်းကို မတော်တဆ ချိတ်မိခြင်း မဖြစ်စေပါ။
- Bot ရပ်သွားလျှင် ယခု startup မှ ဖွင့်ထားသော Node server ကိုလည်း ရပ်ပါမည်။
- Offline/unit tests အောင်မြင်ခြင်းက RedNote အပြင်ဘက် CDN ထံမှ Live Video Download အောင်မြင်မည်ဟု အာမမခံနိုင်ပါ။
- Token ကို သိမ်းမထားပါ။ ပြသထားပြီးသား Token ကို BotFather တွင် Revoke လုပ်ပါ။