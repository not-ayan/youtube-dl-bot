import time
import yt_dlp
from aiogram import F, Router, types

from handlers.modules.master import master_handler

router = Router()

def download_pinterest(url: str, filename: str) -> tuple:
    opts = {
        "format": "best",
        "outtmpl": filename,
    }
    original_caption = ""
    with yt_dlp.YoutubeDL(opts) as yt:
        info = yt.extract_info(url, download=False)
        original_caption = info.get('description', '')
        yt.download([url])
    return filename, original_caption

links = [
    "https://www.pinterest.com/",
    "https://pin.it/",
]

@router.message(F.text.startswith(tuple(links)))
async def pinterest(message: types.Message) -> None:
    filename = f"{time.time_ns()}-{message.from_user.id}.mp4"
    mention = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.full_name}</a>'
    filename, original_caption = await master_handler(
        message=message,
        send_function=message.answer_video,
        download_function=lambda: download_pinterest(message.text, filename),
        caption=f'{original_caption}\n\n<a href="{message.text}">Source</a>\nShared by {mention}'
    )
