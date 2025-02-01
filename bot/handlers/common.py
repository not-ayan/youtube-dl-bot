from aiogram import F, Router, types
from aiogram.filters import Command

router = Router()

@router.message(F.text, Command("start"))
async def start(message: types.Message) -> None:
    await message.answer(text="Send a link to the media you want to download.\nFor usage instructions, type /howtouse\n\n<b>We do not collect any data about you!</b>")

@router.message(F.text, Command("howtouse"))
async def howtouse(message: types.Message) -> None:
    await message.answer(
        text="\n".join(
            (
                "This bot is an all-in-one media downloader, supporting various platforms.",
                "When you send a link, the bot automatically detects the platform and initiates the appropriate module.",
                "The bot may offer different download options (e.g., multiple quality levels). Just follow the instructions.",
                "If the download is successful, the bot will delete your message and send the file.",
                "Otherwise, the bot will send an error message.",
                "",
                "<b>Important:</b>",
                "Please avoid downloading very large video files, as this can take a lot of time and resources.",
                "For optimal performance, we recommend downloading YouTube videos up to 5-10 minutes in length.",
                "If the video is too large, consider choosing a lower quality.",
                "",
                "If a post on X (Twitter) contains multiple videos, specify the video number after the link (e.g., for the third video, use {link}/3).",
            )
        )
    )
