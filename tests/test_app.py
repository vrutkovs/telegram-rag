from pathlib import Path

from app import (
    build_prompt,
    build_prompt_from_posts,
    load_posts,
    rank_posts,
    select_example_posts,
)


class ReverseSampler:
    def sample(self, posts: list, count: int) -> list:
        return list(reversed(posts))[:count]


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


def test_build_prompt_from_posts_uses_relevant_post_texts(tmp_path: Path) -> None:
    posts = [
        (tmp_path / "10.txt", "first relevant style"),
        (tmp_path / "11.txt", "second relevant style"),
    ]
    for path, text in posts:
        path.write_text(text, encoding="utf-8")

    prompt = build_prompt_from_posts("release notes", load_posts(tmp_path))

    assert "release notes" in prompt
    assert "first relevant style" in prompt
    assert "second relevant style" in prompt


def test_select_example_posts_randomly_samples_from_relevant_candidates(
    tmp_path: Path,
) -> None:
    posts = [
        ("1.txt", "alpha beta gamma delta"),
        ("2.txt", "alpha beta gamma"),
        ("3.txt", "alpha beta"),
        ("4.txt", "alpha"),
        ("5.txt", "unrelated note"),
        ("6.txt", "another unrelated note"),
    ]
    for name, text in posts:
        (tmp_path / name).write_text(text, encoding="utf-8")

    selected = select_example_posts(
        "alpha beta gamma delta",
        load_posts(tmp_path),
        count=2,
        rng=ReverseSampler(),
    )

    assert [post.text for post in selected] == ["alpha", "alpha beta"]


def test_select_example_posts_does_not_exceed_available_posts(tmp_path: Path) -> None:
    (tmp_path / "1.txt").write_text("only post", encoding="utf-8")

    selected = select_example_posts(
        "only",
        load_posts(tmp_path),
        count=10,
        rng=ReverseSampler(),
    )

    assert [post.text for post in selected] == ["only post"]
