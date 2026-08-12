# YouTube Downloader Bot — Advanced Version

`bot_advanced.py` adds on top of the basic bot:

- **Quality choice**: 1080p / 720p / 480p / MP3 (audio-only)
- **Subtitles**: optional, downloaded as `.srt` alongside the video
- **Progress updates**: "Downloading X/Y..." message updates live
- **Parallel downloads**: up to 3 videos download at once (playlists finish faster)
- **Selective playlist picking**: tap exactly which videos you want from a
  playlist instead of downloading all of them

## Setup

Same as the basic bot, plus **ffmpeg** is required for MP3 conversion and
merging separate video/audio streams into one file:

```bash
# Debian/Ubuntu
sudo apt install ffmpeg

# macOS (Homebrew)
brew install ffmpeg
```

Then:
```bash
pip install python-telegram-bot yt-dlp
export BOT_TOKEN="123456:ABC-DEF..."
python bot_advanced.py
```

## How it works

1. Send a YouTube link.
2. **If it's a playlist**: you'll see a list of videos with checkboxes
   (tap to select/deselect, or "Select All"). Tap "Done" when finished.
3. **Either way**: pick a quality (1080p/720p/480p/MP3), optionally tap
   "+ Subtitles", then "Start Download ▶️".
4. The bot downloads up to 3 videos in parallel, updating you with
   progress, and sends each one back as it finishes.

## Limits & notes

- Playlist picker shows up to the first 50 videos (Telegram keyboard
  size limits) — for longer playlists, that's an easy follow-up change
  (e.g. paging, or a "download all" shortcut for huge lists).
- Files over 50MB (Telegram's bot upload limit) are saved locally
  instead, with the path reported back to you.
- Session state (your video picks, quality choice) is kept in memory
  only — restarting the bot clears any in-progress selections.
- This is still meant for personal/private use, same as the basic version.
