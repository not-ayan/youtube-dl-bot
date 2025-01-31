import json
import re
import time

import yt_dlp
from aiogram import F, Router, types, exceptions
from aiogram.types import InputMediaPhoto

from handlers.modules.master import master_handler

router = Router()


def vids_count(url: str) -> int:
    with yt_dlp.YoutubeDL() as ydl:
        info = ydl.extract_info(url, download=False)
        if "entries" in info:
            return len(info["entries"])
        return 1


def download_x(url: str, filename: str, video_index: int = 0) -> str:
    with yt_dlp.YoutubeDL({"outtmpl": filename, "format": "best"}) as ydl:
        info = ydl.extract_info(url, download=False)
        if "entries" in info:
            url = info["entries"][video_index].get("url")
        else:
            # No entries means single media
            if not info.get("formats"):
                # Fallback: no video => return special marker
                return "NO_VIDEO_FOUND"
        ydl.download([url])
    return filename


links = [
    "https://x.com/",
    "https://twitter.com/",
]


def keyboard(number: int, url: str) -> types.InlineKeyboardMarkup:
    kb = [[types.InlineKeyboardButton(text=f"Видео {i+1}", callback_data=f"{url}!{i}")] for i in range(number)]
    return types.InlineKeyboardMarkup(inline_keyboard=kb)


@router.message(lambda message: any(message.text.lower().startswith(link) for link in links))
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
            caption=f'<a href="{message.text}">Source</a>\n\nUploaded by {mention}'
        )


@router.callback_query(lambda c: c.data.startswith(tuple(links)))
async def x2(callback: types.CallbackQuery) -> None:
    mention = f'<a href="tg://user?id={callback.from_user.id}">{callback.from_user.full_name}</a>'
    data = callback.data.split("!")
    filename = f"{time.time_ns()}-{callback.message.from_user.id}.mp4"

    filename = download_x(data[0], filename, int(data[-1]))
    if filename == "NO_VIDEO_FOUND":
        # Fallback to images
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(data[0], download=False)
            if "entries" in info:
                info = info["entries"][int(data[-1])]
            if "thumbnails" in info:
                media_list = [
                    InputMediaPhoto(t["url"], caption=(f'<a href="{data[0]}">Source</a>\nUploaded by {mention}' if i == 0 else None))
                    for i, t in enumerate(info["thumbnails"])
                ]
                await callback.message.answer_media_group(media_list)
            return

    await master_handler(
        message=callback.message,
        send_function=callback.message.answer_video,
        download_function=lambda: download_x(data[0], filename, int(data[-1])),
        caption=f'<a href="{data[0]}">Source</a>\nUploaded by {mention}'
    )
