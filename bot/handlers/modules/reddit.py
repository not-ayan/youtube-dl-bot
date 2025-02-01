import time
import yt_dlp
import os
import logging
from aiogram import F, Router, types, exceptions
from dotenv import load_dotenv
from urllib.parse import urlparse
import json
import re

from handlers.modules.master import master_handler

router = Router()

# Load environment variables
load_dotenv()

class Reddit(BaseScrapper):
    @property
    def cleaned_url(self) -> str:
        parsed_url = urlparse(self.original_url)
        return f"https://www.reddit.com{parsed_url.path}"

    async def scrape(self) -> None:
        json_data = await self.get_data()
        if json_data is None:
            return

        try:
            post_data: dict = json_data[0]["data"]["children"][0]["data"]
        except (KeyError, IndexError, ValueError):
            logger.debug(str(json.dumps(json_data, indent=4)))
            return

        self.media_info_caption: str = (
            f'<i>{post_data["subreddit_name_prefixed"]}:</i>'
            f'\n<b>{post_data["title"]}</b>'
        )

        self.single_media_thumb: str = await aio.thumb_dl(post_data.get("thumbnail"))

        if post_data.get("is_gallery"):

            for val in post_data["media_metadata"].values():
                media_url = val["s"].get("u", val["s"].get("gif"))
                download_url = media_url.replace("preview", "i")
                await self.save_media(url=download_url, append_to_group=True)

            self.extraction_success = True
            self.media_type: MediaType = MediaType.GROUP
            return

        hls: list[str] = re.findall(r"'hls_url'\s*:\s*'([^']*)'", str(post_data))

        if hls:
            os.makedirs(self.media_download_dir)
            self.single_media: str = os.path.join(self.media_download_dir, "v.mp4")
            vid_url: str = hls[0]
            await run_shell_cmd(
                cmd=f'ffmpeg -hide_banner -loglevel error -i "{vid_url.strip()}" -c copy {self.single_media}',
                timeout=20,
            )

            self.single_media_thumb = await take_ss(
                video=self.single_media, path=self.media_download_dir
            )
            self.extraction_success = True
            self.media_type = (
                MediaType.VIDEO
                if await check_audio(self.single_media)
                else MediaType.GIF
            )
            return

        common_url: str = post_data.get("url_overridden_by_dest", "").strip()

        self.media_type: MediaType = get_type(url=common_url, generic=False)

        if self.media_type:
            await self.save_media(url=common_url)
            self.extraction_success = True

    async def get_data(self) -> dict | None:
        headers: dict = {
            "user-agent": "Mozilla/5.0 (Linux; Android 10; Pixel 4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.101 Mobile Safari/537.36"
        }
        response: dict | None = await aio.get_json(
            url=f"{self.cleaned_url}.json?limit=1", headers=headers, json_=True
        )
        if not response:
            # fmt : skip
            self.original_url = str((await aio.session.get(self.original_url)).url)

            response: dict | None = await aio.get_json(
                url=f"{self.cleaned_url}.json?limit=1", headers=headers, json_=True
            )
        return response

def download_reddit_post(url: str, filename: str) -> str:
    logging.info(f"Downloading Reddit post from URL: {url}")
    
    common_filename = "downloaded_reddit_post.mp4"

    ydl_opts = {
        'outtmpl': common_filename,
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4'
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except yt_dlp.utils.DownloadError as e:
        logging.error(f"Error downloading Reddit post: {e}")
        raise ValueError("Requested format is not available. Please try a different format.")
    
    if not os.path.isfile(common_filename):
        logging.error(f"File {common_filename} not found after download.")
        raise ValueError("File download failed. Please try again.")
    
    logging.info(f"File {common_filename} downloaded successfully.")
    return common_filename

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
        await master_handler(
            message=message,
            send_function=message.answer_video,
            download_function=lambda: download_reddit_post(message.text, filename),
            caption=f'<a href="{message.text}">Source</a>\n\nUploaded by {mention}'
        )
    except Exception as e:
        logging.error(f"Error downloading Reddit post: {e}")
        await message.answer(f"Error downloading Reddit post: {e}")
