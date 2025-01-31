import time
import instaloader
from aiogram import F, Router, types, exceptions

from handlers.modules.master import master_handler

router = Router()

def download_instagram_post(url: str, filename: str) -> str:
    L = instaloader.Instaloader(download_videos=False, download_video_thumbnails=False, download_comments=False)
    post = instaloader.Post.from_shortcode(L.context, url.split("/")[-2])
    L.download_post(post, target=filename)
    return filename

links = [
    "https://www.instagram.com/p/",
]

@router.message(F.text.startswith(tuple(links)))
async def instagram(message: types.Message) -> None:
    filename = f"{time.time_ns()}-{message.from_user.id}"
    mention = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.full_name}</a>'
    await master_handler(
        message=message,
        send_function=message.answer_photo,
        download_function=lambda: download_instagram_post(message.text, filename),
        caption=f'<a href="{message.text}">Source</a>\n\nUploaded by {mention}'
    )
