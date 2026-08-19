"""Pass B: Aggregate friction signals and synthesize insights."""

import json
import os
from collections import defaultdict
from groq import Groq
from io_utils import RAW_REVIEWS_PATH, THEMES_PATH, INSIGHTS_PATH, load_json, save_json
from prompts import build_synthesis_prompt, FRICTION_TAXONOMY

MODEL = "llama-3.1-70b-versatile"


def aggregate_frictions(themes: dict, raw_reviews: list) -> dict:
    """Aggregate friction point counts and build evidence."""
    friction_counts = defaultdict(int)
    friction_quotes = defaultdict(list)
    segment_counts = defaultdict(int)
    friction_by_segment = defaultdict(lambda: defaultdict(int))

    for idx_str, theme_data in themes.items():
        frictions = theme_data.get("friction_points", [])
        segment = theme_data.get("user_segment", "unclear")

        segment_counts[segment] += 1

        for friction_obj in frictions:
            friction = friction_obj.get("friction")
            quote = friction_obj.get("quote", "")
            if friction:
                friction_counts[friction] += 1
                friction_by_segment[friction][segment] += 1
                if quote and len(friction_quotes[friction]) < 5:  # Keep top 5 quotes per friction
                    friction_quotes[friction].append(quote)

    # Calculate percentages
    total_reviews = len(themes)
    friction_data = []

    for friction in FRICTION_TAXONOMY:
        count = friction_counts.get(friction, 0)
        percentage = (count / total_reviews * 100) if total_reviews > 0 else 0
        affected_segments = dict(friction_by_segment.get(friction, {}))

        friction_data.append(
            {
                "friction": friction,
                "count": count,
                "percentage": round(percentage, 1),
                "affected_segments": affected_segments,
                "example_quotes": friction_quotes.get(friction, []),
            }
        )

    # Sort by count descending
    friction_data.sort(key=lambda x: x["count"], reverse=True)

    return {
        "total_reviews_analyzed": total_reviews,
        "friction_distribution": friction_data,
        "segment_breakdown": dict(segment_counts),
        "friction_by_segment": {
            k: dict(v) for k, v in friction_by_segment.items()
        },
    }


def identify_cohorts(themes: dict, aggregates: dict) -> list[dict]:
    """Identify customer cohorts based on friction patterns."""
    segment_counts = aggregates["segment_breakdown"]
    total = aggregates["total_reviews_analyzed"]

    cohorts = []
    for segment, count in sorted(segment_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total * 100) if total > 0 else 0
        if percentage >= 10:  # Only include cohorts with 10%+ of reviews
            cohorts.append({
                "name": segment.replace("_", " ").title(),
                "segment": segment,
                "size_percentage": round(percentage, 1),
                "size_count": count,
            })

    return cohorts


def main() -> None:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise SystemExit("GROQ_API_KEY environment variable is not set")

    print("Loading themes...")
    raw_reviews = load_json(RAW_REVIEWS_PATH)
    themes = load_json(THEMES_PATH)

    if not themes:
        print("ERROR: No themes found. Run extract_themes.py first.")
        return

    if isinstance(themes, list):
        print("ERROR: themes.json should be a dict, not a list.")
        return

    print(f"Aggregating {len(themes)} tagged reviews...")
    aggregates = aggregate_frictions(themes, raw_reviews)

    print("\nFriction points ranked by prevalence:")
    for item in aggregates["friction_distribution"]:
        print(f"  {item['friction']}: {item['count']} ({item['percentage']}%)")

    cohorts = identify_cohorts(themes, aggregates)
    print(f"\nIdentified {len(cohorts)} customer cohorts")

    # Prepare inputs for synthesis prompt
    ranked_frictions = [
        {
            "friction": item["friction"],
            "count": item["count"],
            "percentage": item["percentage"],
        }
        for item in aggregates["friction_distribution"][:5]  # Top 5
    ]

    sample_quotes = {}
    for item in aggregates["friction_distribution"]:
        sample_quotes[item["friction"]] = item["example_quotes"][:3]

    print("\nCalling Groq for synthesis...")
    client = Groq(api_key=api_key)

    messages = build_synthesis_prompt(
        ranked_frictions,
        aggregates,
        sample_quotes,
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0,
        )
        synthesis = json.loads(response.choices[0].message.content)
    except Exception as exc:
        print(f"Warning: Synthesis call failed ({exc}), using basic structure")
        synthesis = {
            "friction_insights": [],
            "customer_cohorts": [],
            "top_recommendation": "See raw friction distribution",
        }

    # Compile final insights
    insights = {
        "analysis_date": __import__("datetime").datetime.now().isoformat(),
        "total_reviews": aggregates["total_reviews_analyzed"],
        "friction_distribution": aggregates["friction_distribution"],
        "customer_cohorts": cohorts,
        "synthesis": synthesis,
    }

    save_json(INSIGHTS_PATH, insights)
    print(f"\nInsights saved to {INSIGHTS_PATH}")
    print("\nTop 3 Friction Points:")
    for i, item in enumerate(aggregates["friction_distribution"][:3], 1):
        print(
            f"{i}. {item['friction']} ({item['count']} reviews, {item['percentage']}%)"
        )


if __name__ == "__main__":
    main()
