import time
import yt_dlp
from aiogram import F, Router, types

from handlers.modules.master import master_handler

router = Router()

def download_pinterest(url: str, filename: str) -> str:
    opts = {
        "format": "best",
        "outtmpl": filename,
    }
    with yt_dlp.YoutubeDL(opts) as yt:
        yt.download([url])
    return filename

links = [
    "https://www.pinterest.com/",
    "https://pin.it/",
]

@router.message(F.text.startswith(tuple(links)))
async def pinterest(message: types.Message) -> None:
    filename = f"{time.time_ns()}-{message.from_user.id}.mp4"
    mention = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.full_name}</a>'
    await master_handler(
        message=message,
        send_function=message.answer_video,
        download_function=lambda: download_pinterest(message.text, filename),
        caption=f'<a href="{message.text}">Source</a>\nShared by {mention}'
    )
