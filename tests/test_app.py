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


def text_with_words(*words: str) -> str:
    fillers = [f"word{index}" for index in range(20 - len(words))]
    return " ".join([*words, *fillers])


def test_load_posts_reads_text_files_from_exact_folder(tmp_path: Path) -> None:
    first_post = text_with_words("first", "post")
    (tmp_path / "1.txt").write_text(first_post, encoding="utf-8")
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "2.txt").write_text("ignore nested", encoding="utf-8")
    (tmp_path / "ignored.md").write_text("ignore me", encoding="utf-8")

    posts = load_posts(tmp_path)

    assert [post.text for post in posts] == [first_post]


def test_load_posts_skips_posts_shorter_than_twenty_words(tmp_path: Path) -> None:
    long_post = text_with_words("long", "post")
    (tmp_path / "1.txt").write_text("too short", encoding="utf-8")
    (tmp_path / "2.txt").write_text(long_post, encoding="utf-8")

    posts = load_posts(tmp_path)

    assert [post.text for post in posts] == [long_post]


def test_rank_posts_prefers_topic_matches_and_adds_representative_posts(
    tmp_path: Path,
) -> None:
    posts = [
        (
            tmp_path / "1.txt",
            text_with_words(
                "VictoriaMetrics", "release", "improves", "log", "search", "performance"
            ),
        ),
        (tmp_path / "2.txt", text_with_words("short", "channel", "style", "note")),
        (
            tmp_path / "3.txt",
            text_with_words("another", "compact", "update", "in", "channel", "voice"),
        ),
    ]
    for path, text in posts:
        path.write_text(text, encoding="utf-8")

    ranked = rank_posts("log search release", load_posts(tmp_path), limit=2)

    assert ranked[0].text == text_with_words(
        "VictoriaMetrics", "release", "improves", "log", "search", "performance"
    )
    assert len(ranked) == 2


def test_build_prompt_includes_topic_examples_and_copy_guard() -> None:
    prompt = build_prompt("new product launch", ["example style post"])

    assert "new product launch" in prompt
    assert "example style post" in prompt
    assert "Do not copy" in prompt
    assert "at least 20 words" in prompt
    assert "Output only the post text" in prompt


def test_build_prompt_from_posts_uses_relevant_post_texts(tmp_path: Path) -> None:
    posts = [
        (tmp_path / "10.txt", text_with_words("first", "relevant", "style")),
        (tmp_path / "11.txt", text_with_words("second", "relevant", "style")),
    ]
    for path, text in posts:
        path.write_text(text, encoding="utf-8")

    prompt = build_prompt_from_posts("release notes", load_posts(tmp_path))

    assert "release notes" in prompt
    assert text_with_words("first", "relevant", "style") in prompt
    assert text_with_words("second", "relevant", "style") in prompt


def test_select_example_posts_randomly_samples_from_relevant_candidates(
    tmp_path: Path,
) -> None:
    posts = [
        ("1.txt", text_with_words("alpha", "beta", "gamma", "delta")),
        ("2.txt", text_with_words("alpha", "beta", "gamma")),
        ("3.txt", text_with_words("alpha", "beta")),
        ("4.txt", text_with_words("alpha")),
        ("5.txt", text_with_words("unrelated", "note")),
        ("6.txt", text_with_words("another", "unrelated", "note")),
    ]
    for name, text in posts:
        (tmp_path / name).write_text(text, encoding="utf-8")

    selected = select_example_posts(
        "alpha beta gamma delta",
        load_posts(tmp_path),
        count=2,
        rng=ReverseSampler(),
    )

    assert [post.text for post in selected] == [
        text_with_words("alpha"),
        text_with_words("alpha", "beta"),
    ]


def test_select_example_posts_does_not_exceed_available_posts(tmp_path: Path) -> None:
    only_post = text_with_words("only", "post")
    (tmp_path / "1.txt").write_text(only_post, encoding="utf-8")

    selected = select_example_posts(
        "only",
        load_posts(tmp_path),
        count=10,
        rng=ReverseSampler(),
    )

    assert [post.text for post in selected] == [only_post]
