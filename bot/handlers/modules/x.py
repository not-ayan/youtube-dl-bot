import os
import time
import logging
import subprocess
import glob
import yt_dlp
from aiogram import F, Router, types, exceptions

from handlers.modules.master import master_handler

router = Router()

class GalleryDL:
    def __init__(self, url: str, download_dir: str):
        self.url = url
        self.download_dir = download_dir
        self.extraction_success = False
        self.grouped_media = []
        self.single_media = None

    async def scrape(self):
        os.makedirs(self.download_dir, exist_ok=True)
        cmd = f"gallery-dl -q --range '0-4' -D {self.download_dir} '{self.url}'"
        process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if process.returncode != 0:
            logging.error(f"gallery-dl failed: {process.stderr}")
            raise ValueError("gallery-dl failed to download the media.")

        files_list = glob.glob(f"{self.download_dir}/*")
        if not files_list:
            self.clean_downloads()
            return

        self.extraction_success = True
        if len(files_list) > 1:
            self.grouped_media = files_list
        else:
            self.single_media = files_list[0]

    def clean_downloads(self):
        if os.path.exists(self.download_dir):
            for file in os.listdir(self.download_dir):
                os.remove(os.path.join(self.download_dir, file))
            os.rmdir(self.download_dir)

def yt_dlp_download(url: str, filename: str) -> str:
    opts = {
        "format": "best",
        "outtmpl": filename,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])
    return filename

def download_x(url: str, filename: str) -> str:
    download_dir = os.path.dirname(filename)
    gallery_dl = GalleryDL(url, download_dir)
    try:
        gallery_dl.scrape()
        if gallery_dl.extraction_success:
            if gallery_dl.single_media:
                return gallery_dl.single_media
            elif gallery_dl.grouped_media:
                return gallery_dl.grouped_media[0]  # Return the first file for simplicity
    except Exception as e:
        logging.error(f"gallery-dl failed: {e}. Trying yt-dlp...")
        return yt_dlp_download(url, filename)

links = [
    "https://x.com/",
    "https://twitter.com/",
]

@router.message(F.text.startswith(tuple(links)))
async def x(message: types.Message) -> None:
    mention = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.full_name}</a>'
    filename = f"downloads/{time.time_ns()}-{message.from_user.id}.mp4"
    await master_handler(
        message=message,
        send_function=message.answer_video,
        download_function=lambda: download_x(message.text, filename),
        caption=f'<a href="{message.text}">Source</a>\n\nUploaded by {mention}'
    )

@router.callback_query(lambda c: c.data.startswith(tuple(links)))
async def x2(callback: types.CallbackQuery) -> None:
    mention = f'<a href="tg://user?id={callback.from_user.id}">{callback.from_user.full_name}</a>'
    data = callback.data.split("!")
    filename = f"downloads/{time.time_ns()}-{callback.message.from_user.id}.mp4"

    await master_handler(
        message=callback.message,
        send_function=callback.message.answer_video,
        download_function=lambda: download_x(data[0], filename),
        caption=f'<a href="{data[0]}">Source</a>\nUploaded by {mention}'
    )