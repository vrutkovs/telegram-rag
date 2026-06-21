import os
import random
import re
from dataclasses import dataclass
from pathlib import Path

import streamlit as st


@dataclass(frozen=True)
class Post:
    path: Path
    text: str


STOP_WORDS = {
    "about",
    "after",
    "again",
    "also",
    "and",
    "are",
    "but",
    "for",
    "from",
    "has",
    "have",
    "into",
    "new",
    "not",
    "that",
    "the",
    "this",
    "with",
    "you",
    "your",
}


def load_posts(folder: Path) -> list[Post]:
    if not folder.exists():
        raise ValueError(f"POSTS_FOLDER does not exist: {folder}")
    if not folder.is_dir():
        raise ValueError(f"POSTS_FOLDER must be a directory: {folder}")

    posts = []
    for path in sorted(folder.glob("*.txt")):
        text = path.read_text(encoding="utf-8").strip()
        if text:
            posts.append(Post(path=path, text=text))
    return posts


def tokenize(text: str) -> set[str]:
    words = re.findall(r"[\w]+", text.lower())
    return {word for word in words if len(word) > 2 and word not in STOP_WORDS}


def rank_posts(topic: str, posts: list[Post], limit: int = 8) -> list[Post]:
    if not posts:
        return []

    topic_words = tokenize(topic)
    topic_phrase = topic.strip().lower()
    lengths = sorted(len(post.text) for post in posts)
    median_length = lengths[len(lengths) // 2]

    def score(post: Post) -> tuple[float, str]:
        post_words = tokenize(post.text)
        overlap = len(topic_words & post_words)
        phrase_bonus = 3 if topic_phrase and topic_phrase in post.text.lower() else 0
        length_distance = abs(len(post.text) - median_length)
        representative_bonus = 1 / (1 + length_distance)
        return overlap + phrase_bonus + representative_bonus, post.path.name

    return [post for post in sorted(posts, key=score, reverse=True)[:limit]]


def select_random_posts(posts: list[Post], count: int, rng=random) -> list[Post]:
    if count <= 0 or not posts:
        return []
    return rng.sample(posts, min(count, len(posts)))


def build_prompt(topic: str, examples: list[str]) -> str:
    formatted_examples = "\n\n".join(
        f"Example {index}:\n{text}" for index, text in enumerate(examples, start=1)
    )
    return f"""You are writing a new Telegram channel post.

Study examples only for style:
- language
- tone
- structure
- sentence length
- paragraph breaks
- emoji and hashtag habits
- punctuation and capitalization
- call-to-action style

Do not copy sentences, facts, claims, or specific wording from examples.
Write an original post about: {topic}

Examples:
{formatted_examples}

Output only the post text."""


def build_prompt_from_posts(topic: str, examples: list[Post]) -> str:
    return build_prompt(topic, [post.text for post in examples])


def generate_post(prompt: str, temperature: float) -> str:
    from google import genai
    from google.genai import types

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Set GEMINI_API_KEY")

    model = os.environ.get("GEMINI_MODEL", "gemini-3.1-pro-preview")
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=temperature),
    )
    return (response.text or "").strip()


def main() -> None:
    st.set_page_config(page_title="Telegram post generator")
    st.title("Telegram post generator")

    posts_folder = os.environ.get("POSTS_FOLDER")
    if not posts_folder:
        st.error("Set POSTS_FOLDER to exact folder with existing .txt posts")
        st.stop()

    try:
        posts = load_posts(Path(posts_folder))
    except ValueError as exc:
        st.error(str(exc))
        st.stop()

    st.caption(f"Loaded {len(posts)} posts from {posts_folder}")
    topic = st.text_input("Topic", placeholder="What should the new post be about?")
    post_count_column, temperature_column = st.columns(2)
    with post_count_column:
        post_count = st.number_input(
            "Posts to fetch",
            min_value=1,
            max_value=max(1, len(posts)),
            value=min(10, max(1, len(posts))),
            step=1,
        )
    with temperature_column:
        temperature = st.slider(
            "Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1
        )

    generated = ""
    examples: list[Post] = []
    prompt = ""
    if st.button("Generate", type="primary", disabled=not topic.strip() or not posts):
        with st.status("Generating post...", expanded=True) as status:
            try:
                status.write("Fetching random posts")
                examples = select_random_posts(posts, int(post_count))
                for post in examples:
                    st.markdown(f"**{post.path.name}**")
                    st.text_area(
                        f"Retrieved contents of {post.path.name}",
                        value=post.text,
                        height=140,
                        disabled=True,
                        label_visibility="collapsed",
                        key=f"status-post-{post.path}",
                    )
                prompt = build_prompt_from_posts(topic, examples)
                status.write("Sending prompt to Gemini")
                generated = generate_post(prompt, temperature)
                status.write("Displaying post contents")
                status.write("Showing prompt")
                status.update(label="Post generated", state="complete")
            except ValueError as exc:
                status.update(label="Generation failed", state="error")
                st.error(str(exc))
            except Exception as exc:  # noqa: BLE001
                status.update(label="Generation failed", state="error")
                st.error(f"Gemini request failed: {exc}")

    st.text_area("Generated post", value=generated, height=320)

    if examples:
        with st.expander("Fetched posts"):
            for post in examples:
                st.markdown(f"**{post.path.name}**")
                st.text_area(
                    f"Contents of {post.path.name}",
                    value=post.text,
                    height=180,
                    disabled=True,
                    label_visibility="collapsed",
                    key=f"post-{post.path}",
                )

    if prompt:
        with st.expander("Prompt"):
            st.text_area(
                "Prompt sent to Gemini",
                value=prompt,
                height=320,
                disabled=True,
                label_visibility="collapsed",
                key="prompt",
            )


if __name__ == "__main__":
    main()
