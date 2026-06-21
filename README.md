# telegram-rag

Retrieve text posts from a Telegram channel into `output/<channel name>/<post id>.txt`.

## Setup

Create Telegram API credentials at <https://my.telegram.org>, then export:

```sh
export TELEGRAM_API_ID=123456
export TELEGRAM_API_HASH=your_api_hash
```

## Usage

```sh
uv run retrieve_channel.py channel_username
```

Use public usernames without `@`, or any channel identifier Telethon accepts. First run may ask for Telegram login code.
