import os
import time
import logging
import subprocess
import yt_dlp
from aiogram import F, Router, types, exceptions

from handlers.modules.master import master_handler

router = Router()

def gallery_dl_download(url: str, filename: str) -> str:
    dest_dir = os.path.dirname(filename)
    os.makedirs(dest_dir, exist_ok=True)
    cmd = ["gallery-dl", "--dest", dest_dir, url]
    process = subprocess.run(cmd, capture_output=True, text=True)
    if process.returncode != 0:
        logging.error(f"gallery-dl failed: {process.stderr}")
        raise ValueError("gallery-dl failed to download the media.")
    
    downloaded_files = []
    for root, _, files in os.walk(dest_dir):
        for file in files:
            if file.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".mp4")):
                downloaded_files.append(os.path.join(root, file))
    
    if not downloaded_files:
        raise ValueError("No files were downloaded with gallery-dl.")
    
    return downloaded_files[0]

def yt_dlp_download(url: str, filename: str) -> str:
    opts = {
        "format": "best",
        "outtmpl": filename,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])
    return filename

def download_x(url: str, filename: str) -> str:
    try:
        return gallery_dl_download(url, filename)
    except Exception as e:
        logging.error(f"gallery-dl failed: {e}. Trying yt-dlp...")
        return yt_dlp_download(url, filename)

links = [
    "https://x.com/",
    "https://twitter.com/",
]

def keyboard(number: int, url: str) -> types.InlineKeyboardMarkup:
    kb = [[types.InlineKeyboardButton(text=f"Video {i+1}", callback_data=f"{url}!{i}")] for i in range(number)]
    return types.InlineKeyboardMarkup(inline_keyboard=kb)

@router.message(F.text.startswith(tuple(links)))
async def x(message: types.Message) -> None:
    mention = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.full_name}</a>'
    count = vids_count(message.text)

    if count > 1:
        try:
            await message.delete()
        except exceptions.TelegramBadRequest:
            pass
        await message.answer("Multiple videos found in the post. Please select which one you want to download", reply_markup=keyboard(count, message.text))
    else:
        filename = f"{time.time_ns()}-{message.from_user.id}.mp4"
        await master_handler(
            message=message,
            send_function=message.answer_video,
            download_function=lambda: download_x(message.text, filename),
            caption=f'<a href="{message.text}">Source</a>\nShared by {mention}'
        )

@router.callback_query(lambda c: c.data.startswith(tuple(links)))
async def x2(callback: types.CallbackQuery) -> None:
    mention = f'<a href="tg://user?id={callback.from_user.id}">{callback.from_user.full_name}</a>'
    data = callback.data.split("!")
    filename = f"{time.time_ns()}-{callback.message.from_user.id}.mp4"

    await master_handler(
        message=callback.message,
        send_function=callback.message.answer_video,
        download_function=lambda: download_x(data[0], filename, int(data[-1])),
        caption=f'<a href="{data[0]}">Source</a>\nShared by {mention}'
    )