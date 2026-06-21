from pathlib import Path

import pytest

from retrieve_channel import safe_path_name, telegram_config, write_post


def test_safe_path_name_replaces_unsafe_characters() -> None:
    assert safe_path_name("News/Updates: Today") == "News_Updates_ Today"


def test_write_post_creates_account_and_channel_directories(tmp_path: Path) -> None:
    post_path = write_post(tmp_path, 12345, "News/Updates", 42, "hello\nworld")

    assert post_path == tmp_path / "12345" / "News_Updates" / "42.txt"
    assert post_path.read_text(encoding="utf-8") == "hello\nworld"


def test_telegram_config_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_API_ID", "123")
    monkeypatch.setenv("TELEGRAM_API_HASH", "hash")
    monkeypatch.setenv("TELEGRAM_SESSION", "session-name")

    assert telegram_config() == (123, "hash", "session-name")


def test_telegram_config_requires_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TELEGRAM_API_ID", raising=False)
    monkeypatch.delenv("TELEGRAM_API_HASH", raising=False)

    with pytest.raises(SystemExit, match="Set TELEGRAM_API_ID and TELEGRAM_API_HASH"):
        telegram_config()
