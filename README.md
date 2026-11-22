# Telegram Video Downloader Bot

Windows one-click Telegram video downloader with RedNote/Xiaohongshu download service and Telegram channel join verification.

## Installation (Windows)
1. Install **Node.js 20+** and **Python 3**.
2. Download the repository ZIP or clone this repository.
3. Run `START_HERE.cmd` from the project folder.
4. Enter your **BotFather bot token only in the local terminal**, when requested. Do not post it to GitHub or this chat.
5. Keep the terminal running and send a supported video link to your Telegram bot.

The launcher uses a loopback local downloader server and the Python Telegram polling bot. Edit `channel.txt` to set the public channel username if necessary. See `READ_FIRST_MM.txt` and `README_LAPTOP_MM.md` for Burmese instructions.

## Tests
- `python -m pip install requests`
- `python -m unittest -v test_bot`
- `cd rednote-downloader && npm run check:syntax && npm test`

Local checks performed for the imported archive: **7/7 Python tests**, **96/96 JavaScript tests** and **13 JavaScript syntax files passed**. GitHub Actions checks are configured independently.

## Current validation boundary
**Real Telegram video delivery is not yet verified.** Passing offline tests does not confirm that RedNote's live site/CDNs, account restrictions, Telegram channel permissions, or the bot's remote upload work. Verify with a real authorized bot/account and a test video before declaring production readiness.

## Safety
This repository is **public**. Never commit `BOT_TOKEN`, cookies, session files, or private downloaded video files. They are not required for review or offline unit tests.
