import asyncio
import os
from typing import Any, Callable

import requests
from aiogram import exceptions, types
from tenacity import retry, retry_if_exception_type, stop, stop_after_attempt
from videoprops import get_video_properties

ERROR_MESSAGES = {
    "size_limit": "Unfortunately, due to Telegram limitations, we cannot send videos larger than 50 megabytes. Attempting to upload the file to filebin.net",
    "general_error": "An error occurred. Please report the bug to @not_ayan99",
}


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
        os.remove(filename)
