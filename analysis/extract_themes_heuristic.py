"""Heuristic-based friction point detection (keyword matching) - fast alternative to LLM."""

import json
import re
from io_utils import RAW_REVIEWS_PATH, THEMES_PATH, load_json, save_json

# Friction point keyword patterns
FRICTION_PATTERNS = {
    "Fit & Sizing Uncertainty": [
        r"\bfit\b", r"\bsize\b", r"\bsizing\b", r"\bfits\b", r"\bfitting\b",
        r"runs\s+(small|large|tight|loose)", r"worried.*fit", r"concerned.*size",
        r"material.*feel", r"length\b", r"width\b", r"\btry\s+on\b",
        r"accurate.*size", r"true.*size", r"fit\s+guide", r"size\s+chart"
    ],
    "Price Hesitation": [
        r"\bprice\b", r"\bexpensive\b", r"\bcost\b", r"\bcostly\b", r"too\s+much\s+money",
        r"waiting.*sale", r"waiting.*discount", r"\bdiscount\b", r"\bsale\b",
        r"afford\b", r"budget", r"reduce.*price", r"overpriced", r"pricey"
    ],
    "Social Validation Gap": [
        r"\breview", r"\bratings?\b", r"\brating\b", r"few\s+reviews", r"no\s+reviews",
        r"customer\s+feedback", r"buyer\s+reviews", r"user\s+feedback", r"testimonial",
        r"what.*others.*say", r"others\s+bought", r"social\s+proof"
    ],
    "Missing Product Information": [
        r"care\s+instruction", r"material", r"composition", r"fabric", r"wash",
        r"style\s+guide", r"how\s+to.*wear", r"occasion", r"pairing",
        r"description", r"detail", r"specification", r"\binfo\b", r"information",
        r"more.*details", r"product\s+info", r"need.*know"
    ],
    "External Research Needed": [
        r"checked\s+online", r"check.*elsewhere", r"other.*sites?", r"google",
        r"search.*online", r"compare.*other", r"other.*platform", r"flipkart",
        r"amazon", r"justdial", r"outside", r"external", r"elsewhere"
    ],
    "Inventory/Availability Anxiety": [
        r"\bstock\b", r"available", r"sold\s+out", r"out\s+of\s+stock",
        r"availability", r"when.*available", r"back\s+in\s+stock", r"limited\s+stock",
        r"will.*available", r"inventory"
    ],
    "Comparison Paralysis": [
        r"can't\s+decide", r"couldn't.*decide", r"hard\s+to.*choose", r"couldn't.*choose",
        r"multiple\s+choices", r"choose\s+between", r"compare", r"options",
        r"which\s+one", r"shortlist", r"wishlist"
    ],
    "Payment/Delivery Friction": [
        r"\bpayment\b", r"\bdelivery\b", r"\bship", r"\bfree\s+shipping", r"delivery.*time",
        r"delivery.*fee", r"cash\s+on\s+delivery", r"COD", r"address\b", r"location",
        r"return.*policy", r"exchange", r"refund"
    ],
    "Postponement Pattern": [
        r"later\b", r"maybe\s+later", r"postpone", r"think.*about", r"thinking",
        r"wait.*and\s+see", r"seasonal", r"occasion\s+later", r"gift.*later",
        r"someday", r"future", r"saved", r"bookmark"
    ],
}

# User segment indicators
SEGMENT_PATTERNS = {
    "new_customer": [
        r"first.*time", r"first\s+buy", r"never\s+bought", r"new\s+to", r"first\s+purchase"
    ],
    "repeat_buyer": [
        r"again", r"another", r"repeat", r"always", r"regular", r"long.*customer"
    ],
    "price_sensitive": [
        r"budget", r"cheap", r"affordable", r"discount", r"sale", r"save\s+money", r"expensive"
    ],
    "quality_conscious": [
        r"quality", r"durability", r"premium", r"high\s+quality", r"best", r"excellent"
    ],
}


def detect_frictions(text: str) -> list[dict]:
    """Detect friction points in review text using keyword patterns."""
    if not text:
        return []

    text_lower = text.lower()
    frictions = []

    for friction, patterns in FRICTION_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                # Extract quote: find the sentence containing the match
                sentences = re.split(r'[.!?]\s+', text)
                quote = None
                for sentence in sentences:
                    if re.search(pattern, sentence.lower()):
                        quote = sentence.strip()
                        if len(quote) > 100:
                            quote = quote[:100] + "..."
                        break

                frictions.append({
                    "friction": friction,
                    "relationship": "hesitation",  # Default to hesitation for heuristic
                    "quote": quote or text[:80] + "..."
                })
                break  # One match per friction point is enough

    # Deduplicate
    seen = set()
    unique_frictions = []
    for f in frictions:
        if f["friction"] not in seen:
            unique_frictions.append(f)
            seen.add(f["friction"])

    return unique_frictions[:2]  # Max 2 friction points per review


def detect_segment(text: str) -> str:
    """Detect user segment from review text."""
    text_lower = text.lower()

    for segment, patterns in SEGMENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return segment

    return "unclear"


def main() -> None:
    print("Loading reviews...")
    raw_reviews = load_json(RAW_REVIEWS_PATH)

    if not raw_reviews:
        print("ERROR: No reviews found in raw_reviews.json")
        return

    print(f"Processing {len(raw_reviews)} reviews with heuristic friction detection...\n")

    themes = {}
    friction_counts = {}

    for idx, review in enumerate(raw_reviews):
        text = review.get("text", "")
        sentiment = review.get("sentiment", "Neutral").lower()

        frictions = detect_frictions(text)
        segment = detect_segment(text)

        # Count friction occurrences
        for f in frictions:
            friction_name = f["friction"]
            friction_counts[friction_name] = friction_counts.get(friction_name, 0) + 1

        themes[str(idx)] = {
            "index": idx,
            "friction_points": frictions,
            "primary_issue": frictions[0]["friction"] if frictions else None,
            "user_segment": segment,
            "sentiment": "positive" if "positive" in sentiment else (
                "negative" if "negative" in sentiment else "neutral"
            ),
            "likely_to_convert": True if frictions else False,
        }

    save_json(THEMES_PATH, themes)
    print(f"✓ Tagged {len(themes)} reviews")
    print(f"\nFriction point distribution:")
    for friction, count in sorted(friction_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / len(raw_reviews) * 100)
        print(f"  {friction}: {count} ({pct:.1f}%)")

    print(f"\n✓ Saved to {THEMES_PATH}")


if __name__ == "__main__":
    main()
