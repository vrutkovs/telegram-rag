import argparse
import asyncio
import os
import re
from pathlib import Path

from telethon import TelegramClient


def safe_path_name(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._ -]", "_", name).strip(" .")
    return cleaned or "channel"


def write_post(
    output_dir: Path, account_id: int, channel_name: str, post_id: int, text: str
) -> Path:
    channel_dir = output_dir / str(account_id) / safe_path_name(channel_name)
    channel_dir.mkdir(parents=True, exist_ok=True)

    post_path = channel_dir / f"{post_id}.txt"
    post_path.write_text(text, encoding="utf-8")
    return post_path


def telegram_config() -> tuple[int, str, str]:
    api_id = os.environ.get("TELEGRAM_API_ID")
    api_hash = os.environ.get("TELEGRAM_API_HASH")
    session = os.environ.get("TELEGRAM_SESSION", "telegram-rag")

    if not api_id or not api_hash:
        raise SystemExit("Set TELEGRAM_API_ID and TELEGRAM_API_HASH")

    try:
        return int(api_id), api_hash, session
    except ValueError as exc:
        raise SystemExit("TELEGRAM_API_ID must be an integer") from exc


async def retrieve_channel(channel: str, output_dir: Path) -> int:
    api_id, api_hash, session = telegram_config()

    count = 0
    async with TelegramClient(session, api_id, api_hash) as client:
        account = await client.get_me()
        entity = await client.get_entity(channel)
        channel_name = getattr(entity, "title", None) or getattr(entity, "username", None) or channel

        async for message in client.iter_messages(entity):
            text = message.raw_text
            if not text:
                continue

            write_post(output_dir, account.id, channel_name, message.id, text)
            count += 1

    return count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Retrieve Telegram channel text posts into output/<account id>/<channel>/<post id>.txt"
    )
    parser.add_argument("channel", help="Telegram channel username, URL, or identifier")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Base output directory (default: output)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    count = asyncio.run(retrieve_channel(args.channel, args.output_dir))
    print(f"wrote {count} posts")


if __name__ == "__main__":
    main()
