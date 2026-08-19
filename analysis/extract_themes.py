"""Pass A: Tag each review for friction points using Groq (Llama 3.1 8B)."""

import json
import os
from groq import Groq
from io_utils import RAW_REVIEWS_PATH, THEMES_PATH, load_json, save_json
from prompts import build_extraction_prompt

MODEL = "llama-3.1-8b-instant"
BATCH_SIZE = 15


def chunked(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def main() -> None:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise SystemExit("GROQ_API_KEY environment variable is not set")

    client = Groq(api_key=api_key)

    # Load raw reviews (as list) and themes (as dict)
    raw_reviews = load_json(RAW_REVIEWS_PATH)
    themes = load_json(THEMES_PATH)

    # Convert raw_reviews to indexed dict if it's a list
    if isinstance(raw_reviews, list):
        raw_reviews_dict = {str(i): r for i, r in enumerate(raw_reviews)}
    else:
        raw_reviews_dict = raw_reviews

    # Find pending reviews (not yet tagged)
    pending = [
        (idx, r)
        for idx, r in raw_reviews_dict.items()
        if idx not in themes and r.get("text")
    ]

    if not pending:
        print("No new reviews to tag — themes.json is already up to date.")
        return

    print(f"Tagging {len(pending)} reviews...")
    tagged_count = 0

    for batch in chunked(pending, BATCH_SIZE):
        batch_data = [r for _, r in batch]
        messages = build_extraction_prompt(batch_data)

        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0,
            )
            parsed = json.loads(response.choices[0].message.content)
        except Exception as exc:
            print(f"Skipping batch of {len(batch)} reviews due to error: {exc}")
            continue

        for result in parsed.get("results", []):
            batch_index = result.get("index")
            if batch_index is not None and batch_index < len(batch):
                review_idx = batch[batch_index][0]
                themes[review_idx] = result
                tagged_count += 1

        save_json(THEMES_PATH, themes)
        print(f"  Saved {tagged_count}/{len(pending)} reviews...")

    print(f"\nTagged {tagged_count} reviews. {len(themes)} total in {THEMES_PATH}")


if __name__ == "__main__":
    main()
