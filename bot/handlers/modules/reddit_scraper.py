import os
import re
import json
from urllib.parse import urlparse
from typing import Optional, Union, Dict, List

import aiohttp
from aiogram import types, F, Router
from aiogram.utils.exceptions import TelegramNetworkError
from tenacity import retry, retry_if_exception_type, stop_after_attempt

from handlers.modules.master import master_handler

router = Router()

@router.message(F.text.startswith("https://www.reddit.com/r/"))
async def reddit_scraper(message: types.Message) -> None:
    reddit = Reddit(message.text)
    await reddit.scrape()
    if reddit.extraction_success:
        if reddit.media_type == "group":
            # Handle group media
            pass
        elif reddit.media_type == "video":
            await master_handler(
                message=message,
                send_function=message.answer_video,
                download_function=lambda: reddit.single_media,
                caption=reddit.media_info_caption
            )
        elif reddit.media_type == "gif":
            await master_handler(
                message=message,
                send_function=message.answer_animation,
                download_function=lambda: reddit.single_media,
                caption=reddit.media_info_caption
            )
        else:
            await master_handler(
                message=message,
                send_function=message.answer_photo,
                download_function=lambda: reddit.single_media,
                caption=reddit.media_info_caption
            )
    else:
        await message.answer("Failed to extract media from the Reddit post.")

class Reddit:
    def __init__(self, original_url: str):
        self.original_url = original_url
        hls: List[str] = re.findall(r"'hls_url'\s*:\s*'([^']*)'", str(post_data))
        self.media_info_caption = ""
        self.single_media_thumb = ""
        self.single_media = ""
        self.media_type = None
        self.extraction_success = False
        self.media_download_dir = "downloads"

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
            print(str(json.dumps(json_data, indent=4)))
            return
        self.media_info_caption = (
            f'<i>{post_data["subreddit_name_prefixed"]}:</i>'
            f'\n<b>{post_data["title"]}</b>'
        )
        self.single_media_thumb = await self.thumb_dl(post_data.get("thumbnail"))
        if post_data.get("is_gallery"):
            for val in post_data["media_metadata"].values():
                media_url = val["s"].get("u", val["s"].get("gif"))
                download_url = media_url.replace("preview", "i")
                await self.save_media(url=download_url, append_to_group=True)
            self.extraction_success = True
            self.media_type = "group"
            return
        if hls:
            os.makedirs(self.media_download_dir, exist_ok=True)
            self.single_media = os.path.join(self.media_download_dir, "v.mp4")
            vid_url: str = hls[0]
            await self.run_shell_cmd(
                cmd=f'ffmpeg -hide_banner -loglevel error -i "{vid_url.strip()}" -c copy {self.single_media}',
                timeout=20,
            )
            self.single_media_thumb = await self.take_ss(
                video=self.single_media, path=self.media_download_dir
            )
            self.extraction_success = True
            self.media_type = (
                "video"
                if await self.check_audio(self.single_media)
                else "gif"
            )
            return
        common_url: str = post_data.get("url_overridden_by_dest", "").strip()
        self.media_type = self.get_type(url=common_url, generic=False)

    async def check_audio(self, video: str) -> bool:
        # Implement audio checking logic here
        pass

    def get_type(self, url: str, generic: bool = False) -> str:
        # Implement type detection logic here
        pass

        if self.media_type:
            await self.save_media(url=common_url)
            self.extraction_success = True

    async def get_data(self) -> Optional[Dict]:
        headers = {
            "user-agent": "Mozilla/5.0 (Linux; Android 10; Pixel 4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.101 Mobile Safari/537.36"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.cleaned_url}.json?limit=1", headers=headers) as response:
                if response.status != 200:
                    self.original_url = str((await session.get(self.original_url)).url)
                    async with session.get(f"{self.cleaned_url}.json?limit=1", headers=headers) as retry_response:
                        if retry_response.status != 200:
                            return None
                        return await retry_response.json()
                return await response.json()

    async def thumb_dl(self, url: str) -> str:
        # Implement thumbnail download logic here
        pass

    async def save_media(self, url: str, append_to_group: bool = False) -> None:
        # Implement media saving logic here

    async def run_shell_cmd(self, cmd: str, timeout: int) -> None:
        # Implement shell command execution logic here
        pass

    async def take_ss(self, video: str, path: str) -> str:
        # Implement screenshot taking logic here
        pass
        pass