import time
import yt_dlp
import os
import logging
from aiogram import F, Router, types, exceptions
from dotenv import load_dotenv

from handlers.modules.master import master_handler

router = Router()

# Load environment variables
load_dotenv()

def download_reddit_post(url: str, filename: str) -> str:
    logging.info(f"Downloading Reddit post from URL: {url}")
    
    final_filename = filename

    def postprocessor_hook(d):
        nonlocal final_filename
        if d['status'] == 'finished':
            final_filename = d['filename']
            logging.info(f"Final filename: {final_filename}")

    ydl_opts = {
        'outtmpl': filename,
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'postprocessor_hooks': [postprocessor_hook]
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except yt_dlp.utils.DownloadError as e:
        logging.error(f"Error downloading Reddit post: {e}")
        raise ValueError("Requested format is not available. Please try a different format.")
    
    if not os.path.isfile(final_filename):
        logging.error(f"File {final_filename} not found after download.")
        raise ValueError("File download failed. Please try again.")
    
    logging.info(f"File {final_filename} downloaded successfully.")
    return final_filename

links = [
    "https://www.reddit.com/r/",
]

@router.message(F.text.startswith(tuple(links)))
async def reddit(message: types.Message) -> None:
    try:
        filename = f"{time.time_ns()}-{message.from_user.id}.mp4" if "v.redd.it" in message.text else f"{time.time_ns()}-{message.from_user.id}.jpg"
        mention = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.full_name}</a>'
        await master_handler(
            message=message,
            send_function=message.answer_video if "v.redd.it" in message.text else message.answer_photo,
            download_function=lambda: download_reddit_post(message.text, filename),
            caption=f'<a href="{message.text}">Source</a>\n\nUploaded by {mention}'
        )
    except Exception as e:
        logging.error(f"Error downloading Reddit post: {e}")
        await message.answer(f"Error downloading Reddit post: {e}")
