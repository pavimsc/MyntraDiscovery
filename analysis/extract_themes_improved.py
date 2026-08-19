"""Improved friction detection focused on wishlist-to-purchase decision friction."""

import json
import re
from io_utils import RAW_REVIEWS_PATH, THEMES_PATH, load_json, save_json

# More aggressive friction patterns focusing on purchase decision hesitation
FRICTION_PATTERNS = {
    "Fit & Sizing Uncertainty": [
        r"\b(fit|size|sizing|fits|fitting|sized?)\b", r"runs?\s+(small|large|tight|loose)",
        r"worried.*fit", r"concerned.*size", r"material.*feel", r"length", r"width",
        r"(try.?on|true.?size|accurate.*size|size.*guide|fits?.*like)", r"measurements?"
    ],
    "Price Hesitation": [
        r"\b(price|expensive|costly|cost|overpriced|pricey)\b", r"too\s+much\s+(money|cost)",
        r"wait(?:ing)?.*sale", r"wait(?:ing)?.*discount", r"\b(discount|sale|offer)\b",
        r"afford", r"budget", r"(reduce|lower).*price", r"worth.*price"
    ],
    "Comparison Paralysis": [
        r"can't.*decide", r"couldn't.*decide", r"hard.*choose", r"couldn't.*choose",
        r"multiple\s+(choices|options|items)", r"choose\s+between", r"compare",
        r"which\s+(one|item)", r"shortlist", r"wishlist", r"similar\s+styles?", r"torn\s+between"
    ],
    "Missing Product Information": [
        r"\b(care|wash|fabric|material|composition|details?)\b", r"how\s+to\s+(wear|style)",
        r"styling.*guide", r"occasion", r"pairing", r"(wear|use)\s+it", r"description",
        r"information.*need", r"more.*details", r"need.*know"
    ],
    "Social Validation Gap": [
        r"\b(review|rating|ratings?)\b", r"(few|no)\s+reviews?", r"customer\s+feedback",
        r"buyer\s+reviews?", r"user\s+feedback", r"(not.*trusted|trust|confidence)",
        r"others\s+(say|bought|think)", r"social\s+proof"
    ],
    "External Research Needed": [
        r"check(?:ed)?.*online", r"check.*elsewhere", r"(google|search).*online",
        r"compare.*other", r"other\s+(sites?|platforms?|stores?)", r"amazon|flipkart|ajio",
        r"outside.*myntra", r"on\s+(other|different)\s+sites?"
    ],
    "Inventory/Availability Anxiety": [
        r"\b(stock|available|out.?of.?stock)\b", r"sold.*out", r"when.*available",
        r"(back|come)\s+in\s+stock", r"limited.*stock", r"inventory", r"will.*be.*available"
    ],
    "Postponement Pattern": [
        r"\blater\b", r"maybe.*later", r"think.*about\s+it", r"thinking", r"wait.*and.*see",
        r"seasonal", r"occasion.*later", r"gift.*later", r"someday", r"future", r"saved",
        r"bookmark", r"remind.*me", r"come\s+back"
    ],
    "Payment/Delivery Friction": [
        r"\b(payment|deliver|ship|return|refund)\b", r"delivery.*time", r"free.*ship",
        r"cash.*deliver", r"exchange", r"return.*policy", r"address", r"location"
    ],
}

SEGMENT_PATTERNS = {
    "new_customer": [
        r"first\s+(time|buy|purchase)", r"never\s+bought", r"new\s+to", r"not.*bought.*before"
    ],
    "repeat_buyer": [
        r"\bagain\b", r"another", r"repeat", r"always", r"regular", r"(long|loyal).*customer"
    ],
    "price_sensitive": [
        r"\b(budget|cheap|affordable|expensive|costly|discount|sale)\b",
        r"save.*money", r"cost.*concern", r"price.*conscious"
    ],
    "quality_conscious": [
        r"\b(quality|durable|premium|excellent|best|high.*quality)\b",
        r"(look for|want).*quality", r"worth.*money", r"invest.*good"
    ],
}


def detect_frictions(text: str, sentiment: str) -> list[dict]:
    """Detect friction points with sentiment weighting."""
    if not text:
        return []

    text_lower = text.lower()
    frictions = []

    # Weight negative sentiment reviews more (they show actual friction)
    is_negative = "negative" in (sentiment or "").lower()

    for friction, patterns in FRICTION_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                # Skip Payment/Delivery for positive reviews (it's not a purchase decision friction)
                if friction == "Payment/Delivery Friction" and not is_negative:
                    continue

                # Extract quote
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
                    "relationship": "hesitation",
                    "quote": quote or text[:80] + "..."
                })
                break  # One per friction point

    # Return top 2, but for negative reviews, all frictions if they exist
    if is_negative:
        return frictions[:3]
    else:
        return frictions[:1]


def detect_segment(text: str) -> str:
    """Detect user segment from review text."""
    text_lower = text.lower()
    scores = {seg: 0 for seg in SEGMENT_PATTERNS.keys()}

    for segment, patterns in SEGMENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                scores[segment] += 1

    # Return highest scoring segment, or default to unclear
    if max(scores.values()) > 0:
        return max(scores.items(), key=lambda x: x[1])[0]
    return "unclear"


def main() -> None:
    print("Loading reviews...")
    raw_reviews = load_json(RAW_REVIEWS_PATH)

    if not raw_reviews:
        print("ERROR: No reviews in raw_reviews.json")
        return

    print(f"Processing {len(raw_reviews)} reviews with improved friction detection...\n")

    themes = {}
    friction_counts = {}
    segment_counts = {}

    for idx, review in enumerate(raw_reviews):
        text = review.get("text", "")
        sentiment = review.get("sentiment", "Neutral")

        frictions = detect_frictions(text, sentiment)
        segment = detect_segment(text)

        # Count
        for f in frictions:
            fname = f["friction"]
            friction_counts[fname] = friction_counts.get(fname, 0) + 1
        segment_counts[segment] = segment_counts.get(segment, 0) + 1

        themes[str(idx)] = {
            "index": idx,
            "friction_points": frictions,
            "primary_issue": frictions[0]["friction"] if frictions else None,
            "user_segment": segment,
            "sentiment": "positive" if "positive" in sentiment.lower() else (
                "negative" if "negative" in sentiment.lower() else "neutral"
            ),
            "likely_to_convert": True if not frictions else False,
        }

    save_json(THEMES_PATH, themes)
    print(f"✓ Tagged {len(themes)} reviews")
    print(f"\nFriction Point Distribution:")
    for friction, count in sorted(friction_counts.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            pct = (count / len(raw_reviews) * 100)
            bar = "█" * int(pct / 3) + "░" * (20 - int(pct / 3))
            print(f"  {friction:35s} {count:3d} ({pct:5.1f}%) {bar}")

    print(f"\nSegment Distribution:")
    for segment, count in sorted(segment_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / len(raw_reviews) * 100)
        print(f"  {segment:20s} {count:3d} ({pct:5.1f}%)")

    print(f"\n✓ Saved to {THEMES_PATH}")


if __name__ == "__main__":
    main()
