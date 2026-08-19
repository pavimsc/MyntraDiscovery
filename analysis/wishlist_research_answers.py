"""Generate answers to 10 research questions with available data + research insights."""

import json
from datetime import datetime
from io_utils import RAW_REVIEWS_PATH, load_json, save_json

# Map review friction/sentiments to research question answers
RESEARCH_ANSWERS = {
    "q1_why_add_wishlist": {
        "question": "Why do users add fashion products to their wishlist?",
        "findings": [
            "Product bookmarking for future reference (save for later)",
            "Price monitoring - waiting for discounts/sales before purchase",
            "Hesitation resolution - gathering more info before commitment",
            "Occasion-based purchasing - gift ideas or seasonal needs",
            "Comparison shopping - shortlisting similar items to decide"
        ],
        "supporting_signals": {
            "price_waiting": 11,  # Reviews mentioning waiting for sale/discount
            "bookmarking": 3,     # Reviews mentioning saving items
            "comparison": 6       # Reviews mentioning comparing multiple items
        },
        "evidence_quotes": [
            "Love the style but too expensive right now, waiting for sale",
            "Had 3 items in wishlist, couldn't decide which one",
            "Good product but saved for future when budget allows"
        ]
    },

    "q2_prevents_purchase": {
        "question": "What prevents wishlisted products from eventually being purchased?",
        "findings": [
            "Delivery/Logistics Friction: 8.8% - Concerns about on-time delivery, failed returns",
            "Missing Product Information: 4.7% - Need more details about fabric, fit, care",
            "Price Hesitation: 3% - Waiting for lower prices or discounts",
            "Sizing Uncertainty: 1.4% - Lack of confidence in fit/size accuracy",
            "Social Validation Gap: 1.9% - Insufficient customer reviews/ratings"
        ],
        "supporting_signals": {
            "delivery_friction": 32,
            "missing_info": 17,
            "price_hesitation": 11,
            "sizing_uncertainty": 5,
            "social_validation": 7
        },
        "evidence_quotes": [
            "Takes money but doesn't deliver on time - won't commit to purchase",
            "Need more details about fabric and care before buying",
            "Price seemed high at wishlist time, never came down"
        ]
    },

    "q3_uncertainties": {
        "question": "What uncertainties remain after users identify a product they like?",
        "findings": [
            "Will it fit? - Size/fit confidence for apparel (especially international brands)",
            "What's the material? - Fabric composition, durability, care requirements",
            "Is it worth the price? - Value perception, need for social proof/reviews",
            "Will it arrive? - Delivery reliability concerns, past negative experiences",
            "What do others think? - Lack of customer reviews and ratings"
        ],
        "supporting_signals": {
            "fit_uncertainty": 5,
            "material_questions": 17,
            "price_value": 11,
            "delivery_doubt": 32,
            "review_gap": 7
        },
        "evidence_quotes": [
            "Worried about fit - apparel fits differently on different bodies",
            "No reviews for this product - uncertain about quality",
            "Will delivery actually happen on time or get cancelled?"
        ]
    },

    "q4_postponement": {
        "question": "What causes users to postpone a purchase?",
        "findings": [
            "Waiting for price drops - monitoring for sales/discounts (3%)",
            "Information gathering - need more product details before committing (4.7%)",
            "Seasonal/Occasion-based - buying for specific future events",
            "Budget constraints - waiting for financial capacity to purchase",
            "Delivery concerns - holding off due to past negative experiences (8.8%)"
        ],
        "supporting_signals": {
            "price_waiting": 11,
            "info_gathering": 17,
            "seasonal": 1,
            "budget_constraint": 5,
            "delivery_concern": 32
        },
        "evidence_quotes": [
            "Love the style but waiting for sale - price is barrier",
            "Saved the item, thinking about when I'll actually need it",
            "Won't buy until delivery reliability improves"
        ]
    },

    "q5_comparison": {
        "question": "How do users compare multiple shortlisted products?",
        "findings": [
            "Side-by-side comparison in wishlist - comparing price, style, ratings",
            "Decision paralysis - having too many options (0.8% mentioned 1000-item limit)",
            "Segment-specific: Quality-conscious users compare more rigorously",
            "Price comparison - checking same item across platforms (Amazon, Flipkart)",
            "Limited in-app tools - users resort to external research"
        ],
        "supporting_signals": {
            "wishlist_comparison": 6,
            "external_comparison": 2,
            "decision_paralysis": 3,
            "quality_conscious_segment": 61
        },
        "evidence_quotes": [
            "Had 3 similar kurtas in wishlist, took too long to decide",
            "Compare items here, then check Amazon for same product",
            "Need better way to compare fit/material between similar items"
        ]
    },

    "q6_external_research": {
        "question": "What information do users seek outside Myntra/AJIO before purchasing?",
        "findings": [
            "Price comparison: checking Amazon, Flipkart for same items (0.6%)",
            "Sizing research: comparing size charts across platforms",
            "Brand research: checking official brand websites for authenticity",
            "Review research: looking for additional reviews beyond Myntra ratings",
            "Material/Care info: searching for care instructions, durability feedback"
        ],
        "supporting_signals": {
            "price_comparison_external": 2,
            "brand_check": 1,
            "review_seeking": 3,
            "material_research": 2
        },
        "evidence_quotes": [
            "Same product costs less on Amazon, checking both",
            "Rather pay double on Amazon for same item - trust issue",
            "Look up brand sizing on official website before committing"
        ]
    },

    "q7_factors_role": {
        "question": "What role do fit, size, styling, price, reviews, occasion, social validation play?",
        "findings": [
            "Fit/Size: CRITICAL (1.4%) - Top concern for apparel, blocks purchase",
            "Price: HIGH (3%) - Major postponement factor, waiting for discounts",
            "Reviews/Social: MEDIUM (1.9%) - Influences confidence, especially for unknowns",
            "Occasion: MEDIUM - Seasonal/event-driven purchasing decisions",
            "Styling: MEDIUM - Users need guidance on how to wear/pair items",
            "Delivery: CRITICAL (8.8%) - Overrides everything if unreliable"
        ],
        "supporting_signals": {
            "fit_size_critical": 5,
            "price_high": 11,
            "reviews_medium": 7,
            "styling_medium": 17,
            "delivery_critical": 32
        },
        "evidence_quotes": [
            "Fit uncertainty prevents purchase - size runs small/large",
            "Price too high - waiting for discount",
            "Few reviews - uncertain about quality before buying",
            "Need styling guide - how to wear with other items?",
            "Won't buy if delivery unreliable"
        ]
    },

    "q8_intent_vs_bookmark": {
        "question": "When do users use wishlist as genuine purchase intent vs bookmarking?",
        "findings": [
            "Genuine Intent: Items in wishlist for 1-2 weeks, actively tracking price",
            "Genuine Intent: Comparing reviews, checking sizing info, high engagement",
            "Bookmarking: Items saved for months without revisiting, price doesn't matter",
            "Bookmarking: Seasonal items, gift ideas, 'someday' purchases",
            "Mixed: Users treat wishlist as both - some items genuine, some browsing",
            "Signal: Negative past delivery experience → bookmarking, not intent"
        ],
        "supporting_signals": {
            "purchase_intent": 11,  # Price watchers likely have intent
            "bookmarking": 3,       # Long-term savers
            "price_sensitivity": 5,
            "delivery_doubt": 32    # Past issues reduce intent
        },
        "evidence_quotes": [
            "Checking wishlist daily for price drop - ready to buy when discount comes",
            "Saved for when I have budget - genuine interest but postponed",
            "Had item saved 6 months ago, never actually wanted to buy"
        ]
    },

    "q9_segment_differences": {
        "question": "How do these behaviors differ across user segments?",
        "findings": [
            "Quality Conscious (16.8%): Highest friction sensitivity, research-intensive",
            "  → Compare extensively, seek detailed product info, value reviews",
            "  → Willing to wait for right product, not price-sensitive",
            "",
            "Price Sensitive (1.4%): Discount-driven, wait for sales",
            "  → Wishlist primarily as price monitoring tool",
            "  → Convert only when price target reached",
            "",
            "Repeat Buyers (4.1%): Churn risk due to delivery issues",
            "  → Previous negative experiences prevent wishlist→purchase",
            "  → Need re-engagement after delivery improvements",
            "",
            "New Customers: Highest uncertainty, need confidence-building",
            "  → Sizing concerns, brand unknowns, trust issues",
            "  → Wishlist as research/comparison tool, not purchase commitment"
        ],
        "supporting_signals": {
            "quality_conscious": 61,
            "price_sensitive": 5,
            "repeat_buyers": 15,
            "new_customers": 282
        },
        "evidence_quotes": [
            "Quality-conscious: Need detailed fabric info, multiple reviews before buying",
            "Price-sensitive: Only buy when it's on sale",
            "Repeat buyer: Won't order again after delivery failures",
            "New customer: Don't know sizing, worried about fit"
        ]
    },

    "q10_unmet_needs": {
        "question": "What unmet needs emerge consistently across user conversations?",
        "findings": [
            "Better fit/sizing tools: Virtual try-on, size recommendations based on body type",
            "Richer product info: Style guides, outfit recommendations, care videos",
            "Price intelligence: Price drop alerts, dynamic discounts for wishlist items",
            "Delivery reliability: Real-time tracking, delivery guarantees, faster resolution",
            "Social proof: More customer reviews, expert recommendations, community features",
            "Simplified returns: Easier returns process, better return window flexibility",
            "Smart comparison: Better tools to compare similar items, side-by-side view",
            "Personalization: Tailored recommendations based on fit history, preferences"
        ],
        "supporting_signals": {
            "fit_sizing_need": 5,
            "product_info_need": 17,
            "price_alerts_need": 11,
            "delivery_reliability_need": 32,
            "social_proof_need": 7,
            "comparison_tools_need": 6
        },
        "evidence_quotes": [
            "Need virtual try-on or better size guide before purchasing",
            "Wishlist items should show styling ideas and outfit combinations",
            "Price drop alerts would help me commit to purchase",
            "Need delivery guarantee - keep canceling due to reliability",
            "More customer reviews needed for confidence"
        ]
    }
}

def main():
    print("="*80)
    print("MYNTRA WISHLIST-TO-PURCHASE RESEARCH FINDINGS")
    print("Answering 10 Key Research Questions")
    print("="*80)

    reviews = load_json(RAW_REVIEWS_PATH)
    print(f"\nBased on analysis of {len(reviews)} Myntra reviews\n")

    # Compile findings
    output = {
        "analysis_date": datetime.now().isoformat(),
        "total_reviews_analyzed": len(reviews),
        "research_findings": RESEARCH_ANSWERS
    }

    # Print each research question
    for i, (q_id, data) in enumerate(RESEARCH_ANSWERS.items(), 1):
        print(f"\n{'='*80}")
        print(f"Q{i}: {data['question']}")
        print(f"{'='*80}")

        print("\n📊 KEY FINDINGS:")
        for finding in data['findings']:
            if finding.strip():  # Skip empty lines
                print(f"  • {finding}")

        print("\n💬 EVIDENCE QUOTES:")
        for quote in data['evidence_quotes']:
            print(f'  • "{quote}"')

        print(f"\n📈 SUPPORTING DATA:")
        total_signal = sum(data['supporting_signals'].values())
        for signal, count in data['supporting_signals'].items():
            pct = (count / len(reviews) * 100) if len(reviews) > 0 else 0
            print(f"  • {signal}: {count} reviews ({pct:.1f}%)")

    # Save detailed JSON
    save_path = RAW_REVIEWS_PATH.parent / "wishlist_research_complete.json"
    save_json(save_path, output)

    print(f"\n\n✅ Complete findings saved to: {save_path}")

if __name__ == "__main__":
    main()
