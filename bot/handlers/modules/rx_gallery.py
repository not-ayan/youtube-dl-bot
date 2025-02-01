import os
import time
import glob
import logging
import subprocess
from aiogram import F, Router, types
from urllib.parse import urlparse

from handlers.modules.master import master_handler
from handlers.modules.base_scrapper import BaseScrapper

router = Router()

def gallery_dl_download_images(url: str) -> list:
    timestamp_dir = f"gallery_{time.time_ns()}"
    os.makedirs(timestamp_dir, exist_ok=True)
    cmd = ["gallery-dl", "--dest", timestamp_dir, url]
    process = subprocess.run(cmd, capture_output=True, text=True)
    if process.returncode != 0:
        logging.error(f"gallery-dl failed: {process.stderr}")
        raise ValueError("Failed to download images with gallery-dl.")
    
    images = []
    for root, _, files in os.walk(timestamp_dir):
        for file in files:
            if file.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
                images.append(os.path.join(root, file))
    if not images:
        raise ValueError("No images were downloaded.")
    return images

def download_video(url: str, filename: str) -> str:
    try:
        with yt_dlp.YoutubeDL({"outtmpl": filename, "format": "best"}) as ydl:
            ydl.download([url])
    except yt_dlp.utils.DownloadError as e:
        logging.error(f"yt-dlp failed: {e}")
        raise ValueError("yt-dlp failed to download the media.")
    
    if not os.path.isfile(filename):
        raise ValueError("File download failed. Please try again.")
    
    return filename

@router.message(F.text.regexp(r"(https?://(www\.)?reddit\.com/r/.*(\.jpg|\.png|\.gif|/comments/|/r/|gallery))|(https?://(www\.)?x\.com/.*photo)"))
async def rx_gallery_images(message: types.Message) -> None:
    """
    This router looks for possible Reddit or X links containing images.
    The regex is a simplistic approach that you can adjust as needed.
    """
    try:
        mention = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.full_name}</a>'
        images = gallery_dl_download_images(message.text)
        # If multiple, send as a media group; otherwise just send a single image
        if len(images) > 1:
            media_group = []
            for i, img in enumerate(images):
                media_group.append(
                    types.InputMediaPhoto(
                        media=types.FSInputFile(img),
                        caption=f'<a href="{message.text}">Source</a>\nShared by {mention}' if i == 0 else ""
                    )
                )
            await message.answer_media_group(media_group)
        else:
            await master_handler(
                message=message,
                send_function=message.answer_photo,
                download_function=lambda: images[0],  # Already downloaded
                caption=f'<a href="{message.text}">Source</a>\nShared by {mention}'
            )
    except Exception as e:
        await message.answer(f"Error: {e}")

@router.message(F.text.regexp(r"(https?://(www\.)?reddit\.com/r/.*)|(https?://(www\.)?x\.com/.*)"))
async def rx_gallery_videos(message: types.Message) -> None:
    """
    This router looks for possible Reddit or X links containing videos.
    The regex is a simplistic approach that you can adjust as needed.
    """
    try:
        mention = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.full_name}</a>'
        filename = f"{time.time_ns()}-{message.from_user.id}.mp4"
        await master_handler(
            message=message,
            send_function=message.answer_video,
            download_function=lambda: download_video(message.text, filename),
            caption=f'<a href="{message.text}">Source</a>\nShared by {mention}'
        )
    except Exception as e:
        await message.answer(f"Error: {e}")

class GalleryDL(BaseScrapper):
    async def scrape(self):
        os.makedirs(self.media_download_dir)

        await shell.run_shell_cmd(
            cmd=f"gallery-dl -q --range '0-4' -D {self.media_download_dir} '{self.original_url}'",
            timeout=15,
            ret_val=0,
        )

        files_list: list[str] = glob.glob(f"{self.media_download_dir}/*")

        if not files_list:
            self.clean_downloads()
            return

        self.extraction_success = True

        if len(files_list) > 1:
            self.grouped_media = files_list
            self.media_type: MediaType = MediaType.GROUP

            for file in files_list:
                if get_type(path=file) in self.TO_SS_TYPES:
                    self.grouped_media_thumbs[file] = await take_ss(
                        video=file, path=self.media_download_dir
                    )

        else:
            self.media_type: MediaType = get_type(path=files_list[0])
            self.single_media = files_list[0]

            if self.media_type in self.TO_SS_TYPES:
                self.single_media_thumb = await take_ss(
                    video=self.single_media, path=self.media_download_dir
                )


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
