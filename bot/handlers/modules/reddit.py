import time
import praw
import yt_dlp
import os
import logging
from aiogram import F, Router, types, exceptions
from dotenv import load_dotenv

from handlers.modules.master import master_handler

router = Router()

# Load environment variables
load_dotenv()

# Initialize PRAW with your Reddit app credentials
reddit_client_id = os.getenv('REDDIT_CLIENT_ID')
reddit_client_secret = os.getenv('REDDIT_CLIENT_SECRET')
reddit_user_agent = os.getenv('REDDIT_USER_AGENT')

logging.info(f"Reddit client ID: {reddit_client_id}")
logging.info(f"Reddit client secret: {reddit_client_secret}")
logging.info(f"Reddit user agent: {reddit_user_agent}")

reddit = praw.Reddit(
    client_id=reddit_client_id,
    client_secret=reddit_client_secret,
    user_agent=reddit_user_agent
)

def download_reddit_post(url: str, filename: str) -> str:
    logging.info(f"Downloading Reddit post from URL: {url}")
    submission = reddit.submission(url=url)
    media_url = submission.url if not submission.is_video else submission.media['reddit_video']['fallback_url']
    
    ydl_opts = {
        'outtmpl': filename,
        'format': 'best'
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([media_url])
    
    return filename

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
