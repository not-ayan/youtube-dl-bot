import time

import yt_dlp
from aiogram import F, Router, types
from aiogram.types import InputMediaPhoto

from handlers.modules.master import master_handler

router = Router()


def download_tiktok(url: str, filename: str) -> str:
    opts = {
        "format": "best",
        "outtmpl": filename,
        "http_headers": {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36"},
    }
    with yt_dlp.YoutubeDL(opts) as yt:
        info = yt.extract_info(url, download=False)
        if not info.get("formats"):
            return "NO_VIDEO_FOUND"
        yt.download([url])
    return filename


links = [
    "https://www.tiktok.com/",
    "https://vt.tiktok.com/",
    "https://vm.tiktok.com/",
    "https://www.instagram.com/reel/",
    "https://instagram.com/reel/",
    "https://www.instagram.com/share/",
]


@router.message(F.text.startswith(tuple(links)))
async def tiktok(message: types.Message) -> None:
    filename = f"{time.time_ns()}-{message.from_user.id}.mp4"
    mention = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.full_name}</a>'
    result = download_tiktok(message.text, filename)

    if result == "NO_VIDEO_FOUND":
        # Fallback to images
        with yt_dlp.YoutubeDL() as yt:
            info = yt.extract_info(message.text, download=False)
            # If multiple photos
            if "entries" in info:
                info = info["entries"][0]  # Take first entry if multiple
            if "thumbnails" in info:
                media_list = [
                    InputMediaPhoto(t["url"], caption=(f'<a href="{message.text}">Source</a>\n\nUploaded by {mention}' if i == 0 else None))
                    for i, t in enumerate(info["thumbnails"])
                ]
                await message.answer_media_group(media_list)
            return

    await master_handler(
        message=message,
        send_function=message.answer_video,
        download_function=lambda: result,
        caption=f'<a href="{message.text}">Source</a>\n\nUploaded by {mention}'
    )
