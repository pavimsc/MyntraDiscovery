"""Analyze reviews specifically for wishlist behavior and answer 10 research questions."""

import json
import re
from collections import defaultdict
from io_utils import RAW_REVIEWS_PATH, load_json, save_json

# Research question keywords and patterns
RESEARCH_PATTERNS = {
    "q1_why_add_wishlist": {
        "question": "Why do users add fashion products to their wishlist?",
        "keywords": [
            r"wishlist", r"bookmark", r"save", r"later", r"future", r"remember",
            r"keep.*in.*mind", r"favorite", r"store.*item", r"saved.*for"
        ],
        "examples": []
    },
    "q2_prevents_purchase": {
        "question": "What prevents wishlisted products from eventually being purchased?",
        "keywords": [
            r"can't.*buy", r"didn't.*buy", r"never.*bought", r"hesit", r"doubt",
            r"not.*sure", r"concerned", r"worried", r"skeptical", r"won't.*purchase"
        ],
        "examples": []
    },
    "q3_uncertainties": {
        "question": "What uncertainties remain after identifying a product they like?",
        "keywords": [
            r"uncertain", r"unsure", r"not.*sure", r"confused", r"doubt",
            r"need.*know", r"need.*info", r"hesitant", r"worried", r"concerned about"
        ],
        "examples": []
    },
    "q4_postponement": {
        "question": "What causes users to postpone a purchase?",
        "keywords": [
            r"wait", r"later", r"postpone", r"defer", r"delay", r"soon", r"someday",
            r"think.*about", r"consider", r"maybe", r"next.*time", r"come.*back"
        ],
        "examples": []
    },
    "q5_comparison": {
        "question": "How do users compare multiple shortlisted products?",
        "keywords": [
            r"compare", r"versus", r"vs\b", r"choose.*between", r"both", r"similar",
            r"shortlist", r"multiple", r"decide", r"options", r"which.*one"
        ],
        "examples": []
    },
    "q6_external_research": {
        "question": "What information do users seek outside Myntra before purchasing?",
        "keywords": [
            r"amazon", r"flipkart", r"ajio", r"google", r"search.*online",
            r"check.*elsewhere", r"other\s+site", r"other\s+app", r"compare\s+price"
        ],
        "examples": []
    },
    "q7_factors_role": {
        "question": "What role do fit, size, styling, price, reviews, occasion, social validation play?",
        "keywords": [
            r"\bfit\b", r"\bsize\b", r"style", r"occasion", r"price", r"review",
            r"rating", r"validation", r"opinion", r"feedback", r"social"
        ],
        "examples": []
    },
    "q8_intent_vs_bookmark": {
        "question": "When do users use wishlist as genuine intent vs bookmarking?",
        "keywords": [
            r"bookmark", r"save.*later", r"just.*like", r"reference", r"idea",
            r"purchase.*intent", r"want.*buy", r"plan.*to.*buy", r"seriously.*considering"
        ],
        "examples": []
    },
    "q9_segment_differences": {
        "question": "How do these behaviors differ across user segments?",
        "keywords": [
            r"first.*time", r"repeat", r"regular", r"always", r"never", r"new.*user",
            r"budget", r"premium", r"casual", r"dedicated"
        ],
        "examples": []
    },
    "q10_unmet_needs": {
        "question": "What unmet needs emerge consistently?",
        "keywords": [
            r"need", r"wish", r"want", r"should.*have", r"missing", r"lack",
            r"can't.*find", r"not.*available", r"suggestion", r"improvement"
        ],
        "examples": []
    }
}

def analyze_review_for_questions(text, sentiment):
    """Extract signals for each research question from a review."""
    if not text:
        return {}

    text_lower = text.lower()
    findings = {}

    for q_id, q_data in RESEARCH_PATTERNS.items():
        for keyword_pattern in q_data["keywords"]:
            if re.search(keyword_pattern, text_lower, re.IGNORECASE):
                if q_id not in findings:
                    findings[q_id] = []
                # Extract the sentence containing this keyword
                sentences = re.split(r'[.!?]\s+', text)
                for sentence in sentences:
                    if re.search(keyword_pattern, sentence.lower()):
                        quote = sentence.strip()
                        if len(quote) > 150:
                            quote = quote[:150] + "..."
                        findings[q_id].append(quote)
                        break
                break  # One quote per question per review

    return findings

def main():
    print("="*80)
    print("MYNTRA WISHLIST BEHAVIOR ANALYSIS")
    print("Answering 10 Research Questions")
    print("="*80)

    reviews = load_json(RAW_REVIEWS_PATH)

    if not reviews:
        print("ERROR: No reviews loaded")
        return

    print(f"\nAnalyzing {len(reviews)} reviews for wishlist-specific behavior...\n")

    # Aggregate findings by research question
    research_findings = {}
    for q_id in RESEARCH_PATTERNS.keys():
        research_findings[q_id] = {
            "question": RESEARCH_PATTERNS[q_id]["question"],
            "count": 0,
            "quotes": [],
            "sentiment_breakdown": {"positive": 0, "negative": 0, "neutral": 0},
            "affected_segments": defaultdict(int)
        }

    # Segment detection for reviews
    def detect_segment(text):
        text_lower = text.lower()
        if re.search(r"first.*time|never.*bought|new", text_lower):
            return "new_customer"
        elif re.search(r"always|regular|repeat|long.*customer", text_lower):
            return "repeat_customer"
        elif re.search(r"budget|cheap|discount|affordable", text_lower):
            return "price_sensitive"
        elif re.search(r"quality|premium|excellent|best", text_lower):
            return "quality_conscious"
        return "general"

    # Analyze each review
    for review in reviews:
        text = review.get("text", "")
        sentiment = review.get("sentiment", "Neutral").lower()
        segment = detect_segment(text)

        findings = analyze_review_for_questions(text, sentiment)

        for q_id, quotes in findings.items():
            research_findings[q_id]["count"] += 1
            research_findings[q_id]["quotes"].extend(quotes)

            # Track sentiment
            if "positive" in sentiment:
                research_findings[q_id]["sentiment_breakdown"]["positive"] += 1
            elif "negative" in sentiment:
                research_findings[q_id]["sentiment_breakdown"]["negative"] += 1
            else:
                research_findings[q_id]["sentiment_breakdown"]["neutral"] += 1

            # Track segments
            research_findings[q_id]["affected_segments"][segment] += 1

    # Deduplicate quotes and keep top 3 per question
    for q_id in research_findings:
        unique_quotes = []
        seen = set()
        for quote in research_findings[q_id]["quotes"]:
            if quote not in seen:
                unique_quotes.append(quote)
                seen.add(quote)
                if len(unique_quotes) >= 3:
                    break
        research_findings[q_id]["quotes"] = unique_quotes
        research_findings[q_id]["affected_segments"] = dict(research_findings[q_id]["affected_segments"])
        research_findings[q_id]["percentage"] = round(
            (research_findings[q_id]["count"] / len(reviews) * 100), 1
        )

    # Print summary
    print("\n" + "="*80)
    print("RESEARCH QUESTION FINDINGS")
    print("="*80)

    for i, (q_id, data) in enumerate(research_findings.items(), 1):
        print(f"\n{i}. {data['question']}")
        print(f"   Evidence: {data['count']} reviews ({data['percentage']}%)")
        print(f"   Sentiment: +{data['sentiment_breakdown']['positive']} / -{data['sentiment_breakdown']['negative']} / ±{data['sentiment_breakdown']['neutral']}")
        if data['quotes']:
            print(f"   Sample quotes:")
            for quote in data['quotes'][:2]:
                print(f"   • \"{quote}\"")

    # Save to JSON
    output = {
        "analysis_date": __import__("datetime").datetime.now().isoformat(),
        "total_reviews": len(reviews),
        "research_questions": research_findings
    }

    save_path = RAW_REVIEWS_PATH.parent / "wishlist_research_findings.json"
    save_json(save_path, output)

    print(f"\n✅ Detailed findings saved to: {save_path}")
    print("\n" + "="*80)

if __name__ == "__main__":
    main()
