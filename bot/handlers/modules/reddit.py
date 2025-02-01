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

def download_reddit_post(url: str, filename: str) -> tuple:
    logging.info(f"Downloading Reddit post from URL: {url}")
    
    common_filename = "downloaded_reddit_post.mp4"
    original_caption = ""

    ydl_opts = {
        'outtmpl': common_filename,
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4'
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            original_caption = info.get('description', '')
            ydl.download([url])
    except yt_dlp.utils.DownloadError as e:
        logging.error(f"Error downloading Reddit post: {e}")
        raise ValueError("Requested format is not available. Please try a different format.")
    
    if not os.path.isfile(common_filename):
        logging.error(f"File {common_filename} not found after download.")
        raise ValueError("File download failed. Please try again.")
    
    logging.info(f"File {common_filename} downloaded successfully.")
    return common_filename, original_caption

links = [
    "https://www.reddit.com/r/",
]

@router.message(
    F.text.startswith(tuple(links))
    & ~F.text.regexp(r'\.(jpg|jpeg|png|gif)')  # exclude common image patterns
)
async def reddit(message: types.Message) -> None:
    try:
        filename = "downloaded_reddit_post.mp4"
        mention = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.full_name}</a>'
        filename, original_caption = await master_handler(
            message=message,
            send_function=message.answer_video,
            download_function=lambda: download_reddit_post(message.text, filename),
            caption=f'{original_caption}\n\n<a href="{message.text}">Source</a>\n\nShared by {mention}'
        )
    except Exception as e:
        logging.error(f"Error downloading Reddit post: {e}")
        await message.answer(f"Error downloading Reddit post: {e}")
