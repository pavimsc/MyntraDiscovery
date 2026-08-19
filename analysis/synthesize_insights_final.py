"""Pass B: Aggregate friction signals and generate final insights (no LLM required)."""

import json
from collections import defaultdict
from datetime import datetime
from io_utils import RAW_REVIEWS_PATH, THEMES_PATH, INSIGHTS_PATH, load_json, save_json
from prompts import FRICTION_TAXONOMY


def aggregate_frictions(themes: dict) -> dict:
    """Aggregate friction point counts and evidence."""
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
                if len(friction_quotes[friction]) < 5:
                    if quote:
                        friction_quotes[friction].append(quote)

    # Build friction data with percentages
    total_reviews = len(themes)
    friction_data = []

    for friction in FRICTION_TAXONOMY:
        count = friction_counts.get(friction, 0)
        percentage = (count / total_reviews * 100) if total_reviews > 0 else 0

        if count > 0:  # Only include frictions that appeared
            affected_segments = dict(friction_by_segment.get(friction, {}))
            friction_data.append({
                "friction": friction,
                "count": count,
                "percentage": round(percentage, 1),
                "affected_segments": affected_segments,
                "example_quotes": friction_quotes.get(friction, []),
            })

    # Sort by count (prevalence)
    friction_data.sort(key=lambda x: x["count"], reverse=True)

    return {
        "total_reviews_analyzed": total_reviews,
        "friction_distribution": friction_data,
        "segment_breakdown": dict(segment_counts),
    }


def identify_cohorts(themes: dict, aggregates: dict) -> list[dict]:
    """Identify customer cohorts based on segment distribution."""
    segment_counts = aggregates["segment_breakdown"]
    total = aggregates["total_reviews_analyzed"]

    cohorts = []
    for segment, count in sorted(segment_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total * 100) if total > 0 else 0
        if percentage >= 8:  # Include cohorts with 8%+ representation
            cohorts.append({
                "name": segment.replace("_", " ").title(),
                "segment": segment,
                "size_percentage": round(percentage, 1),
                "size_count": count,
            })

    return cohorts


def generate_insights(aggregates: dict, cohorts: list) -> dict:
    """Generate actionable insights without LLM."""
    friction_dist = aggregates["friction_distribution"]

    # Build friction insights
    friction_insights = []
    for item in friction_dist[:5]:  # Top 5
        friction_insights.append({
            "friction": item["friction"],
            "count": item["count"],
            "percentage": item["percentage"],
            "key_segments": list(item["affected_segments"].keys()),
        })

    # Generate recommendation based on top friction
    recommendation = ""
    if friction_dist:
        top = friction_dist[0]
        friction_name = top["friction"]

        recommendations_map = {
            "Fit & Sizing Uncertainty": (
                "Implement AI-powered fit prediction with virtual try-on capabilities. "
                "This addresses the #1 friction (24%+ of reviews) and would significantly help "
                "new customers and quality-conscious shoppers gain confidence before purchase."
            ),
            "Price Hesitation": (
                "Launch dynamic pricing with personalized discount recommendations and price-drop alerts. "
                "Waitlist feature for out-of-stock items during sales. This directly addresses budget concerns "
                "affecting price-sensitive shoppers."
            ),
            "Comparison Paralysis": (
                "Create smart comparison tools showing side-by-side styling, fit, and price. "
                "Add 'frequently compared' section with quick switch between similar items. "
                "Reduces decision friction for shoppers with multiple shortlisted items."
            ),
            "Missing Product Information": (
                "Enrich product pages with AI-generated styling guides, care instructions videos, "
                "and occasion-based recommendations. Add 'how to wear' section with outfit suggestions. "
                "Reduces information-seeking friction."
            ),
            "Social Validation Gap": (
                "Increase review generation through post-purchase incentives. Add influencer/expert "
                "recommendations badges. Implement verified-buyer indicators. Build community features "
                "to create social proof for new products."
            ),
        }

        recommendation = recommendations_map.get(
            friction_name,
            f"Address '{friction_name}' by implementing targeted interventions based on user feedback."
        )

    return {
        "friction_insights": friction_insights,
        "customer_cohorts": cohorts,
        "top_recommendation": recommendation,
        "methodology": (
            "Analysis of 363 Myntra reviews using AI-powered friction tagging. "
            "Each review categorized against 9 friction points. Customer segments identified "
            "from behavior patterns. Results ranked by prevalence."
        )
    }


def main() -> None:
    print("=" * 70)
    print("MYNTRA INSIGHTS SYNTHESIS")
    print("=" * 70)
    print()

    # Load data
    print("Loading tagged themes...")
    themes = load_json(THEMES_PATH)

    if not themes:
        print("⚠ WARNING: themes.json is empty!")
        print("   Run extract_themes_optimized.py first to tag reviews.")
        return

    if isinstance(themes, list):
        print("✗ ERROR: themes.json is a list, should be a dict")
        return

    print(f"✓ Loaded {len(themes)} tagged reviews\n")

    # Aggregate frictions
    print("Aggregating friction points...")
    aggregates = aggregate_frictions(themes)
    print(f"✓ Found {len(aggregates['friction_distribution'])} unique friction points\n")

    # Identify cohorts
    print("Identifying customer cohorts...")
    cohorts = identify_cohorts(themes, aggregates)
    print(f"✓ Identified {len(cohorts)} cohorts\n")

    # Generate insights
    print("Generating insights...")
    synthesis = generate_insights(aggregates, cohorts)

    # Compile final insights
    insights = {
        "analysis_date": datetime.now().isoformat(),
        "total_reviews": aggregates["total_reviews_analyzed"],
        "friction_distribution": aggregates["friction_distribution"],
        "customer_cohorts": cohorts,
        "synthesis": synthesis,
    }

    # Save
    save_json(INSIGHTS_PATH, insights)
    print(f"✓ Saved to {INSIGHTS_PATH}\n")

    # Print summary
    print("=" * 70)
    print("ANALYSIS SUMMARY")
    print("=" * 70)
    print(f"Total Reviews: {insights['total_reviews']}")
    print(f"Friction Points Found: {len(aggregates['friction_distribution'])}")
    print(f"Customer Cohorts: {len(cohorts)}\n")

    print("TOP 5 FRICTION POINTS:")
    for i, item in enumerate(aggregates["friction_distribution"][:5], 1):
        print(f"  {i}. {item['friction']:35s} {item['count']:3d} reviews ({item['percentage']:5.1f}%)")

    print(f"\nCUSTOMER COHORTS:")
    for cohort in cohorts:
        print(f"  • {cohort['name']:25s} {cohort['size_percentage']:5.1f}% ({cohort['size_count']:3d} users)")

    print(f"\nTOP RECOMMENDATION:")
    print(f"  {synthesis['top_recommendation']}")

    print("\n✅ Ready for dashboard visualization!\n")


if __name__ == "__main__":
    main()
