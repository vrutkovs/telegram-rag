from pathlib import Path

from app import build_prompt, load_posts, rank_posts


def test_load_posts_reads_text_files_from_exact_folder(tmp_path: Path) -> None:
    (tmp_path / "1.txt").write_text("first post", encoding="utf-8")
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "2.txt").write_text("ignore nested", encoding="utf-8")
    (tmp_path / "ignored.md").write_text("ignore me", encoding="utf-8")

    posts = load_posts(tmp_path)

    assert [post.text for post in posts] == ["first post"]


def test_rank_posts_prefers_topic_matches_and_adds_representative_posts(
    tmp_path: Path,
) -> None:
    posts = [
        (tmp_path / "1.txt", "VictoriaMetrics release improves log search performance"),
        (tmp_path / "2.txt", "short channel style note"),
        (tmp_path / "3.txt", "another compact update in channel voice"),
    ]
    for path, text in posts:
        path.write_text(text, encoding="utf-8")

    ranked = rank_posts("log search release", load_posts(tmp_path), limit=2)

    assert ranked[0].text == "VictoriaMetrics release improves log search performance"
    assert len(ranked) == 2


def test_build_prompt_includes_topic_examples_and_copy_guard() -> None:
    prompt = build_prompt("new product launch", ["example style post"])

    assert "new product launch" in prompt
    assert "example style post" in prompt
    assert "Do not copy" in prompt
    assert "Output only the post text" in prompt
