"""Pass A: Tag each review for friction points using Groq API (direct HTTP calls)."""

import json
import os
import sys
import time
from io_utils import RAW_REVIEWS_PATH, THEMES_PATH, load_json, save_json
from prompts import build_extraction_prompt

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.1-8b-instant"
BATCH_SIZE = 10


def chunked(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def call_groq_api(messages: list, api_key: str) -> dict:
    """Call Groq API via HTTP."""
    import urllib.request
    import urllib.error

    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        req = urllib.request.Request(
            GROQ_API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result
    except urllib.error.HTTPError as e:
        error_data = e.read().decode("utf-8")
        raise Exception(f"HTTP {e.code}: {error_data}")
    except Exception as e:
        raise Exception(f"API call failed: {e}")


def main() -> None:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise SystemExit("GROQ_API_KEY environment variable is not set")

    print("Loading reviews...")
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

    print(f"Tagging {len(pending)} reviews with Groq Llama 3.1...")
    tagged_count = 0
    failed_batches = 0

    for batch_num, batch in enumerate(chunked(pending, BATCH_SIZE), 1):
        batch_data = [r for _, r in batch]
        messages = build_extraction_prompt(batch_data)

        print(f"  Batch {batch_num}: ", end="", flush=True)

        try:
            response = call_groq_api(messages, api_key)

            if "error" in response:
                print(f"ERROR - {response['error'].get('message', 'Unknown error')}")
                failed_batches += 1
                continue

            parsed = json.loads(response["choices"][0]["message"]["content"])

            for result in parsed.get("results", []):
                batch_index = result.get("index")
                if batch_index is not None and batch_index < len(batch):
                    review_idx = batch[batch_index][0]
                    themes[review_idx] = result
                    tagged_count += 1

            save_json(THEMES_PATH, themes)
            print(f"✓ {tagged_count}/{len(pending)}")

            # Rate limiting
            time.sleep(0.5)

        except Exception as exc:
            print(f"FAILED - {exc}")
            failed_batches += 1
            continue

    print(f"\n{'=' * 60}")
    print(f"Tagging complete!")
    print(f"  Successfully tagged: {tagged_count}/{len(pending)} reviews")
    print(f"  Failed batches: {failed_batches}")
    print(f"  Total in themes.json: {len(themes)}")
    print(f"  Saved to: {THEMES_PATH}")


if __name__ == "__main__":
    main()
