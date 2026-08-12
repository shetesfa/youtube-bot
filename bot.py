"""
Personal-use YouTube downloader Telegram bot.
Downloads single videos or full playlists using yt-dlp and sends
the files back to you in Telegram.

SETUP:
1. Create a bot with @BotFather on Telegram, get your bot token.
2. pip install python-telegram-bot yt-dlp
3. Set the BOT_TOKEN environment variable (or paste it below).
4. Run: python bot.py

NOTES:
- Telegram bots can only send files up to 50MB via the Bot API.
  Larger files are saved to the `downloads/` folder instead, and
  the bot tells you where to find them.
- This is intended for personal/private use only.
"""

import os
import logging
import asyncio
from pathlib import Path

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import yt_dlp

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "8947851594:AAEbygJcMz0wuubBbTcnzKtgITK5MVTHSHI")
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

TELEGRAM_FILE_LIMIT = 50 * 1024 * 1024  # 50 MB


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Send me a YouTube video or playlist link and I'll download it.\n\n"
        "Playlists are downloaded video-by-video and sent one at a time "
        "(or saved locally if too large for Telegram)."
    )


def _extract_info(url: str, download_dir: Path) -> list[dict]:
    """Runs yt-dlp synchronously; called in a background thread."""
    outtmpl = str(download_dir / "%(playlist_index|)s%(playlist_index& - |)s%(title)s.%(ext)s")
    ydl_opts = {
        "format": "best[ext=mp4]/best",
        "outtmpl": outtmpl,
        "noplaylist": False,
        "ignoreerrors": True,
        "quiet": True,
        "no_warnings": True,
    }
    results = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        entries = info.get("entries") if info and "entries" in info else [info]
        for entry in entries or []:
            if not entry:
                continue
            filepath = None
            if entry.get("requested_downloads"):
                filepath = entry["requested_downloads"][0].get("filepath")
            if not filepath:
                filepath = ydl.prepare_filename(entry)
            results.append({"title": entry.get("title", "video"), "path": filepath})
    return results


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    url = update.message.text.strip()
    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text("Please send a valid YouTube video or playlist link.")
        return

    status_msg = await update.message.reply_text("Downloading... this may take a while for playlists.")

    user_dir = DOWNLOAD_DIR / str(update.effective_user.id)
    user_dir.mkdir(exist_ok=True)

    try:
        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(None, _extract_info, url, user_dir)
    except Exception as e:
        logger.exception("Download failed")
        await status_msg.edit_text(f"Download failed: {e}")
        return

    if not results:
        await status_msg.edit_text("Nothing was downloaded — check the link and try again.")
        return

    await status_msg.edit_text(f"Downloaded {len(results)} item(s). Sending now...")

    for item in results:
        path = Path(item["path"])
        if not path.exists():
            continue
        size = path.stat().st_size
        if size <= TELEGRAM_FILE_LIMIT:
            try:
                with open(path, "rb") as f:
                    await update.message.reply_video(
                        video=f, caption=item["title"], read_timeout=120, write_timeout=120
                    )
            except Exception:
                # Fall back to sending as a document if video upload fails
                with open(path, "rb") as f:
                    await update.message.reply_document(document=f, filename=path.name)
        else:
            await update.message.reply_text(
                f"'{item['title']}' is {size / (1024*1024):.1f}MB — too large for Telegram. "
                f"Saved locally at: {path}"
            )


def main() -> None:
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        raise SystemExit("Set the BOT_TOKEN environment variable or edit bot.py with your token.")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot starting...")
    app.run_polling()


if __name__ == "__main__":
    main()