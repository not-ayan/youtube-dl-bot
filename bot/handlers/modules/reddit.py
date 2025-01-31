import time
import praw
import requests
import os
from aiogram import F, Router, types, exceptions
from dotenv import load_dotenv

from handlers.modules.master import master_handler

router = Router()

# Load environment variables
load_dotenv()

# Initialize PRAW with your Reddit app credentials
reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent=os.getenv('REDDIT_USER_AGENT')
)

def download_reddit_post(url: str, filename: str) -> str:
    submission = reddit.submission(url=url)
    if submission.is_video:
        video_url = submission.media['reddit_video']['fallback_url']
        response = requests.get(video_url)
        with open(filename, 'wb') as f:
            f.write(response.content)
    else:
        image_url = submission.url
        response = requests.get(image_url)
        with open(filename, 'wb') as f:
            f.write(response.content)
    return filename

links = [
    "https://www.reddit.com/r/",
]

@router.message(F.text.startswith(tuple(links)))
async def reddit(message: types.Message) -> None:
    filename = f"{time.time_ns()}-{message.from_user.id}.mp4" if "v.redd.it" in message.text else f"{time.time_ns()}-{message.from_user.id}.jpg"
    mention = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.full_name}</a>'
    await master_handler(
        message=message,
        send_function=message.answer_video if "v.redd.it" in message.text else message.answer_photo,
        download_function=lambda: download_reddit_post(message.text, filename),
        caption=f'<a href="{message.text}">Source</a>\n\nUploaded by {mention}'
    )
