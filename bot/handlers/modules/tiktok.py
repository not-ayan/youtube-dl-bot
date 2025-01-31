import time

import yt_dlp
from aiogram import F, Router, types

from handlers.modules.master import master_handler

router = Router()


def download_tiktok(url: str, filename: str) -> str:
    opts = {
        "format": "best",
        "outtmpl": filename,
        "http_headers": {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36"},
    }
    with yt_dlp.YoutubeDL(opts) as yt:
        yt.download([url])
    return filename


def download_instagram_images(url: str) -> list:
    with yt_dlp.YoutubeDL() as ydl:
        info = ydl.extract_info(url, download=False)
        if "entries" in info:
            return [entry["url"] for entry in info["entries"] if "url" in entry]
        elif "url" in info:
            return [info["url"]]
        else:
            raise yt_dlp.utils.DownloadError("No image could be found in this Instagram post.")


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
    try:
        await master_handler(
            message=message,
            send_function=message.answer_video,
            download_function=lambda: download_tiktok(message.text, filename),
            caption=f'<a href="{message.text}">Source</a>\n\nUploaded by {mention}'
        )
    except yt_dlp.utils.DownloadError:
        image_urls = download_instagram_images(message.text)
        media = [types.InputMediaPhoto(url) for url in image_urls]
        await message.answer_media_group(media)
