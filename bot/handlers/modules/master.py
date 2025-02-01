import asyncio
import os
from typing import Any, Callable, Dict, List, Optional, Union
import requests
from aiogram import exceptions, types
from tenacity import retry, retry_if_exception_type, stop_after_attempt
from videoprops import get_video_properties
import aiohttp
import subprocess
import glob
import logging

ERROR_MESSAGES = {
    "size_limit": "Unfortunately, due to Telegram limitations, we cannot send videos larger than 50 megabytes. Attempting to upload the file to filebin.net",
    "general_error": "An error occurred. Please report the bug to the maintainer",
}

class BaseScrapper:
    def __init__(self, original_url: str):
        self.original_url = original_url
        self.media_download_dir = f"downloads/{time.time_ns()}"
        self.extraction_success = False
        self.media_type = None
        self.single_media = None
        self.grouped_media = []
        self.single_media_thumb = None
        self.grouped_media_thumbs = {}
        self.media_info_caption = ""

    async def scrape(self) -> None:
        raise NotImplementedError

    async def save_media(self, url: str, append_to_group: bool = False) -> None:
        os.makedirs(self.media_download_dir, exist_ok=True)
        filename = os.path.join(self.media_download_dir, os.path.basename(url))
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                with open(filename, 'wb') as f:
                    f.write(await response.read())
        if append_to_group:
            self.grouped_media.append(filename)
        else:
            self.single_media = filename

    def clean_downloads(self) -> None:
        if os.path.isdir(self.media_download_dir):
            import shutil
            shutil.rmtree(self.media_download_dir)

async def run_shell_cmd(cmd: str, timeout: int = 30) -> None:
    process = await asyncio.create_subprocess_shell(cmd)
    try:
        await asyncio.wait_for(process.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        process.kill()
        await process.communicate()

async def take_ss(video: str, path: str) -> str:
    thumbnail = os.path.join(path, "thumb.jpg")
    await run_shell_cmd(f"ffmpeg -i {video} -ss 00:00:01.000 -vframes 1 {thumbnail}")
    return thumbnail

async def check_audio(video: str) -> bool:
    result = await asyncio.create_subprocess_shell(
        f"ffprobe -i {video} -show_streams -select_streams a -loglevel error",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await result.communicate()
    return bool(stdout)

def get_type(url: str = "", path: str = "", generic: bool = True) -> Optional[str]:
    if url:
        if "video" in url:
            return "video"
        if "image" in url:
            return "image"
    if path:
        if path.lower().endswith((".mp4", ".mkv", ".webm")):
            return "video"
        if path.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
            return "image"
    return None

async def async_download(function: Callable) -> Any:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, function)

def publish(filename: str) -> str:
    with open(filename, "rb") as file:
        headers = {"filename": filename, "Content-Type": "application/octet-stream"}
        try:
            response = requests.post(
                "https://filebin.net",
                files={"file": file},
                data={"bin": "anekobtw"},
                headers=headers,
                timeout=30  # Add a timeout (in seconds)
            )
        except requests.exceptions.Timeout:
            print("Request timed out while uploading file.")
            return "Upload failed due to timeout."
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return "Upload failed due to a network error."
    res = response.json()
    return f"https://filebin.net/{res['bin']['id']}/{res['file']['filename']}"

@retry(retry=retry_if_exception_type(exceptions.TelegramNetworkError), stop=stop_after_attempt(3))
async def master_handler(
    message: types.Message,
    send_function: Callable,
    download_function: Callable,
    caption: str = ""
) -> None:
    status_msg = await message.answer("The file is being prepared. Please wait a moment.")

    try:
        filename = await async_download(download_function)

        if filename.endswith(".mp4"):
            props = get_video_properties(filename)
            await send_function(types.FSInputFile(filename), caption=caption, height=props["height"], width=props["width"])
        else:
            await send_function(message, filename)

    except exceptions.TelegramEntityTooLarge:
        await status_msg.edit_text(ERROR_MESSAGES["size_limit"])
        await status_msg.edit_text(publish(filename))
        await message.delete()

    except Exception as e:
        print(e)
        await status_msg.edit_text(ERROR_MESSAGES["general_error"])

    else:
        await message.delete()
        await status_msg.delete()
        if os.path.isfile(filename):
            os.remove(filename)
        elif os.path.isdir(filename):
            import shutil
            shutil.rmtree(filename)
