import time

import yt_dlp
from aiogram import F, Router, types, exceptions
from youthon import Video

from handlers.modules.master import master_handler

router = Router()


def get_ydl_opts(quality: str, filename: str) -> dict:
    formats = {
        "fhd": {"format": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]", "merge_output_format": "mp4", "postprocessor_args": ["-c:v", "h264", "-c:a", "aac"]},
        "hd": {"format": "best[height<=720][ext=mp4]"},
        "sd": {"format": "best[height<=480][ext=mp4]"},
        "audio": {"format": "bestaudio[ext=m4a]", "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}]},
    }
    opts = {"outtmpl": filename, "postprocessors": [{"key": "FFmpegFixupM4a"}, {"key": "FFmpegFixupStretched"}]}
    return {**opts, **formats[quality]}


def download_youtube(url: str, filename: str, quality: str) -> str:
    fname = filename[:-4] if quality in ["best", "fhd", "audio"] else filename
    with yt_dlp.YoutubeDL(get_ydl_opts(quality, fname)) as ydl:
        ydl.download([url])
    return filename


links = [
    "https://www.youtube.com/watch?v=",
    "https://youtu.be/",
    "https://www.youtube.com/shorts/",
    "https://youtube.com/shorts/",
]


def keyboard(url: str) -> types.InlineKeyboardMarkup:
    kb = [
        [types.InlineKeyboardButton(text="📹 Full HD (1080p) (Slow)", callback_data=f"{url}!fhd")],
        [types.InlineKeyboardButton(text="📹 HD (720p) (Fast)", callback_data=f"{url}!hd")],
        [types.InlineKeyboardButton(text="📹 SD (480p) (Fast)", callback_data=f"{url}!sd")],
        [types.InlineKeyboardButton(text="🎵 Audio only", callback_data=f"{url}!audio")],
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=kb)


@router.message(F.text.startswith(tuple(links)))
async def youtube(message: types.Message) -> None:
    try:
        mention = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.full_name}</a>'
        if any(short in message.text for short in ["https://www.youtube.com/shorts/", "https://youtube.com/shorts/"]):
            filename = f"{time.time_ns()}-{message.from_user.id}.mp4"
            await master_handler(
                message=message,
                send_function=message.answer_video,
                download_function=lambda: download_youtube(message.text, filename, "fhd"),
                caption=f'<a href="{message.text}">Source</a>\n\nUploaded by {mention}'
            )
        else:
            await message.answer_photo(
                photo=Video(message.text).thumbnail_url,
                caption="Select download quality:",
                reply_markup=keyboard(message.text),
            )
        try:
            await message.delete()
        except exceptions.TelegramBadRequest:
            pass
    except Exception as e:
        await message.answer(f"Error retrieving video information: {str(e)}")


@router.callback_query(lambda c: c.data.startswith(tuple(links)))
async def process_download(callback: types.CallbackQuery) -> None:
    url, quality = callback.data.split("!")
    mention = f'<a href="tg://user?id={callback.from_user.id}">{callback.from_user.full_name}</a>'
    extension = "mp3" if quality == "audio" else "mp4"
    filename = f"{time.time_ns()}-{callback.message.from_user.id}.{extension}"

    await master_handler(
        message=callback.message,
        send_function=callback.message.answer_video if quality != "audio" else callback.message.answer_audio,
        download_function=lambda: download_youtube(url, filename, quality),
        caption=f'<a href="{url}">Source</a>\nUploaded by {mention}'
    )
