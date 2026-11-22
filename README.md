# Telegram Video Downloader Bot

> **Status: source import incomplete — do not deploy.** The audited ZIP source has not yet been transferred into this repository. This branch adds safeguards and a CI gate that deliberately fails rather than falsely reporting that the bot is ready.

## Scope
- Telegram getUpdates, required channel membership and real video delivery.
- RedNote download recovery for terminated, ReadTimeout, and aborted connections.
- Windows startup launcher.

## Security
This repository is **public**. Never commit Telegram bot tokens, session files or cookies. Set BOT_TOKEN through a local environment variable. The .gitignore protects common local secrets but does not replace a secret scan.

## Verification
The attached local archive passed 7 Python and 96 JavaScript tests in a separate runtime. Live Telegram delivery was not verified. GitHub CI intentionally blocks until source files bot.py and rednote-downloader/ are imported, and must pass before merge.
