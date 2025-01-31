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

def get_instagram_images(filename: str) -> list:
    import os
    images = []
    for file in os.listdir(filename):
        if file.endswith(".jpg"):
            images.append(os.path.join(filename, file))
    return images

links = [
    "https://www.instagram.com/p/",
]

async def send_instagram_images(message: types.Message, images: list, caption: str) -> None:
    media = [types.InputMediaPhoto(types.FSInputFile(image), caption=caption if i == 0 else "") for i, image in enumerate(images)]
    await message.answer_media_group(media)

@router.message(F.text.startswith(tuple(links)))
async def instagram(message: types.Message) -> None:
    filename = f"{time.time_ns()}-{message.from_user.id}"
    mention = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.full_name}</a>'
    await master_handler(
        message=message,
        send_function=lambda msg, fn: send_instagram_images(msg, get_instagram_images(fn), f'<a href="{message.text}">Source</a>\n\nUploaded by {mention}'),
        download_function=lambda: download_instagram_post(message.text, filename),
    )
