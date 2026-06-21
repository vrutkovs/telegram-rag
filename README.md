# telegram-rag

Retrieve text posts from a Telegram channel into `output/<account id>/<channel name>/<post id>.txt`.

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

## Generate Posts

Set Gemini API key and exact folder containing existing channel `.txt` posts:

```sh
export GEMINI_API_KEY=your_gemini_api_key
export POSTS_FOLDER="output/<account id>/<channel name>"
```

Run Streamlit app:

```sh
uv run streamlit run app.py
```

The app retrieves relevant existing posts from `POSTS_FOLDER`, sends them as style examples to Gemini, and displays a new original post for the entered topic.

## License

Apache-2.0. See [LICENSE](LICENSE).
