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
        raise ValueError("Failed to download media with gallery-dl.")
    
    downloaded_files = []
    for root, _, files in os.walk(timestamp_dir):
        for file in files:
            if file.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".mp4", ".mov", ".m4v")):
                downloaded_files.append(os.path.join(root, file))
    if not downloaded_files:
        raise ValueError("No media was downloaded. Perhaps the link is unsupported or private.")
    return downloaded_files

@router.message(
    F.text.regexp(
        r"(?:https?://)?(?:www\.)?(?:reddit\.com|redd\.it|x\.com|twitter\.com)/.*"
    )
)
async def rx_gallery_links(message: types.Message) -> None:
    """
    This router captures any Reddit or X link and attempts to download content using gallery-dl.
    """
    try:
        mention = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.full_name}</a>'
        downloaded_files = gallery_dl_download_images(message.text)

        # If multiple files, send them. Some may be images, others may be videos.
        if len(downloaded_files) > 1:
            media_group = []
            for i, fpath in enumerate(downloaded_files):
                mime = fpath.lower()
                if mime.endswith((".jpg", ".jpeg", ".png", ".gif")):
                    item = types.InputMediaPhoto(
                        media=types.FSInputFile(fpath),
                        caption=f'<a href="{message.text}">Source</a>\nShared by {mention}' if i == 0 else ""
                    )
                else:
                    item = types.InputMediaVideo(
                        media=types.FSInputFile(fpath),
                        caption=f'<a href="{message.text}">Source</a>\nShared by {mention}' if i == 0 else ""
                    )
                media_group.append(item)
            await message.answer_media_group(media_group)
        else:
            # Single downloaded file
            fpath = downloaded_files[0].lower()
            if fpath.endswith((".jpg", ".jpeg", ".png", ".gif")):
                await master_handler(
                    message=message,
                    send_function=message.answer_photo,
                    download_function=lambda: downloaded_files[0],  # Already downloaded
                    caption=f'<a href="{message.text}">Source</a>\nShared by {mention}'
                )
            else:
                await master_handler(
                    message=message,
                    send_function=message.answer_video,
                    download_function=lambda: downloaded_files[0],
                    caption=f'<a href="{message.text}">Source</a>\nShared by {mention}'
                )
    except Exception as e:
        await message.answer(f"Error: {e}")