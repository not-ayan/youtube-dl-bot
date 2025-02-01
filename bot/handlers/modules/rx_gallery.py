import os
import time
import logging
import subprocess
from aiogram import F, Router, types

from handlers.modules.master import master_handler

router = Router()

def gallery_dl_download_images(url: str) -> list:
    timestamp_dir = f"gallery_{time.time_ns()}"
    os.makedirs(timestamp_dir, exist_ok=True)
    cmd = ["gallery-dl", "--dest", timestamp_dir, url]
    process = subprocess.run(cmd, capture_output=True, text=True)
    if process.returncode != 0:
        logging.error(f"gallery-dl failed: {process.stderr}")
        raise ValueError("Failed to download images with gallery-dl.")
    
    images = []
    for root, _, files in os.walk(timestamp_dir):
        for file in files:
            if file.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
                images.append(os.path.join(root, file))
    if not images:
        raise ValueError("No images were downloaded.")
    return images

# ...existing code...
@router.message(F.text.regexp(r'(reddit\.com/.*(\.jpg|\.png|\.gif|gallery))|(x\.com/.*photo)'))
async def rx_gallery_images(message: types.Message) -> None:
    """
    This router looks for possible Reddit or X links containing images.
    The regex is a simplistic approach that you can adjust as needed.
    """
    try:
        mention = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.full_name}</a>'
        images = gallery_dl_download_images(message.text)
        # If multiple, send as a media group; otherwise just send a single image
        if len(images) > 1:
            media_group = []
            for i, img in enumerate(images):
                media_group.append(
                    types.InputMediaPhoto(
                        media=types.FSInputFile(img),
                        caption=f'<a href="{message.text}">Source</a>\nShared by {mention}' if i == 0 else ""
                    )
                )
            await message.answer_media_group(media_group)
        else:
            await master_handler(
                message=message,
                send_function=message.answer_photo,
                download_function=lambda: images[0],  # Already downloaded
                caption=f'<a href="{message.text}">Source</a>\nShared by {mention}'
            )
    except Exception as e:
        await message.answer(f"Error: {e}")