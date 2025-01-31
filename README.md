# YouTube-DL Bot 🤖

A versatile Telegram bot for downloading media from various platforms, including YouTube, Instagram, Reddit, and more. Built with Python and `aiogram`, this bot makes it easy to download and share videos, photos, and other media directly in Telegram.

---

## Features ✨

- **YouTube Support**:
  - Download YouTube videos (including shorts) in high quality.

- **Instagram Support**:
  - Download Instagram photos and videos.
  - Works with both single posts and reels.

- **Reddit Support**:
  - Download Reddit videos.
  - *(Note: Reddit photos are not currently supported.)*

- **X (Twitter) Support**:
  - Download Twitter/x.com videos.
  - *(Note: X (Twitter) photos are not currently supported due to API limitations.)*

- **Multi-Platform Compatibility**:
  - Works seamlessly with multiple platforms, providing a unified interface for downloading media.

- **User-Friendly**:
  - Simple commands and intuitive interface.
  - Sends downloaded media directly to your Telegram chat.

---

## Installation 🛠️

Follow these steps to set up and run the bot on your local machine or server.

### Prerequisites

- Python 3.8 or higher
- `pip` (Python package manager)
- A Telegram bot token from [BotFather](https://t.me/BotFather)

### Steps

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/not-ayan/youtube-dl-bot.git
   cd youtube-dl-bot
   ```

2. **Install Dependencies**:
   - For most systems:
     ```bash
     pip install -r requirements.txt
     ```
   - If you encounter issues with system packages (e.g., on Linux):
     ```bash
     pip install -r requirements.txt --break-system-packages
     ```

3. **Configure the Bot**:
   - Rename the `.env.sample` file to `.env`:
     ```bash
     mv .env.sample .env
     ```
   - Open the `.env` file and add your Telegram bot token:
     ```
     TOKEN=your_bot_token_here
     ```

4. **Start the Bot**:
   - Run the bot using the following command:
     ```bash
     python3 bot/main.py
     ```

---

## Usage 🚀

Once the bot is running, simply send it a link to the media you want to download. Supported platforms include:

- **YouTube**: Send a YouTube video or shorts link.
- **Instagram**: Send an Instagram post or reel link.
- **Reddit**: Send a Reddit video link.
- **Twitter**: Send a Twitter video link.

The bot will automatically detect the platform and download the media for you.

---

## Supported Platforms ✅

| Platform       | Videos | Photos | Notes                          |
|----------------|--------|--------|--------------------------------|
| YouTube        | ✔️     | ❌     | Supports shorts and videos. |
| Instagram      | ✔️     | ✔️     | Works with posts and reels.    |
| Reddit         | ✔️     | ❌     | Photos not supported.          |
| X (Twitter)    | ✔️     | ❌     | Photos not supported.       |

---

## Known Issues ⚠️

- **X (Twitter)**: Photos and videos are not supported due to API limitations.
- **Reddit Photos**: Currently not supported.

---

## Contributing 🤝

Contributions are welcome! If you'd like to add new features, fix bugs, or improve the bot, feel free to open a pull request.

### Contributors

- [@not_ayan99](https://github.com/not-ayan) - Project maintainer.

---

## License 📄

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Support 💬

If you encounter any issues or have questions, feel free to open an issue on GitHub or contact [@not_ayan99](t.me/not_ayan99).

---

Enjoy downloading media with ease! 🎉