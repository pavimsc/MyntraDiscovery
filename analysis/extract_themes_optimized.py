"""Optimized batch tagging with retry logic and progress tracking."""

import json
import os
import time
import sys
from io_utils import RAW_REVIEWS_PATH, THEMES_PATH, load_json, save_json
from prompts import build_extraction_prompt

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.1-8b-instant"
BATCH_SIZE = 8
MAX_RETRIES = 2


def chunked(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def call_groq_api(messages: list, api_key: str, retry=0) -> dict:
    """Call Groq API with retry logic."""
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
        error_text = e.read().decode("utf-8")
        if "rate_limit" in error_text.lower() and retry < MAX_RETRIES:
            wait = 5 * (retry + 1)
            print(f"(rate limited, waiting {wait}s)", end="", flush=True)
            time.sleep(wait)
            return call_groq_api(messages, api_key, retry + 1)
        raise Exception(f"HTTP {e.code}: {error_text}")
    except Exception as e:
        raise Exception(f"API call failed: {e}")


def main() -> None:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise SystemExit("GROQ_API_KEY environment variable is not set")

    print("=" * 70)
    print("MYNTRA FRICTION ANALYSIS - BATCH LLM TAGGING")
    print("=" * 70)
    print(f"Model: {MODEL} | Batch Size: {BATCH_SIZE}")
    print()

    # Load data
    raw_reviews = load_json(RAW_REVIEWS_PATH)
    themes = load_json(THEMES_PATH)

    # Convert list to dict if needed
    if isinstance(raw_reviews, list):
        raw_reviews_dict = {str(i): r for i, r in enumerate(raw_reviews)}
    else:
        raw_reviews_dict = raw_reviews

    # Find pending
    pending = [
        (idx, r)
        for idx, r in raw_reviews_dict.items()
        if idx not in themes and r.get("text")
    ]

    if not pending:
        print("✓ All reviews already tagged!")
        return

    print(f"Tagging {len(pending)} reviews in {len(list(chunked(pending, BATCH_SIZE)))} batches...\n")

    total_tagged = 0
    failed_count = 0
    batch_num = 0

    for batch in chunked(pending, BATCH_SIZE):
        batch_num += 1
        batch_data = [r for _, r in batch]
        messages = build_extraction_prompt(batch_data)

        # Progress indicator
        pct = (batch_num * BATCH_SIZE / len(pending)) * 100
        sys.stdout.write(f"\r[{pct:3.0f}%] Batch {batch_num:3d}: ")
        sys.stdout.flush()

        try:
            response = call_groq_api(messages, api_key)

            if "error" in response:
                err_msg = response["error"].get("message", "Unknown error")
                print(f"✗ {err_msg}")
                failed_count += 1
                continue

            # Parse response
            parsed = json.loads(response["choices"][0]["message"]["content"])
            batch_success = 0

            for result in parsed.get("results", []):
                batch_index = result.get("index")
                if batch_index is not None and batch_index < len(batch):
                    review_idx = batch[batch_index][0]
                    themes[review_idx] = result
                    batch_success += 1
                    total_tagged += 1

            # Save every batch for resilience
            save_json(THEMES_PATH, themes)
            print(f"✓ {batch_success}/{len(batch)}")

            # Rate limit friendly delay
            time.sleep(0.3)

        except Exception as exc:
            print(f"✗ {str(exc)[:50]}")
            failed_count += 1
            continue

    print("\n" + "=" * 70)
    print("TAGGING COMPLETE")
    print("=" * 70)
    print(f"Successfully tagged: {total_tagged}/{len(pending)} reviews")
    print(f"Failed batches: {failed_count}")
    print(f"Total in themes.json: {len(themes)}")
    print(f"Saved to: {THEMES_PATH}\n")

    # Show friction distribution
    friction_counts = {}
    for theme_data in themes.values():
        for f_obj in theme_data.get("friction_points", []):
            friction = f_obj.get("friction")
            if friction:
                friction_counts[friction] = friction_counts.get(friction, 0) + 1

    if friction_counts:
        print("Friction Distribution:")
        for friction, count in sorted(friction_counts.items(), key=lambda x: x[1], reverse=True):
            pct = (count / len(themes) * 100)
            bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
            print(f"  {friction:30s} {count:3d} ({pct:5.1f}%) {bar}")


if __name__ == "__main__":
    main()
