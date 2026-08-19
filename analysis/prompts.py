"""Prompt templates and friction-point taxonomy for Myntra wishlist-to-purchase conversion analysis."""

FRICTION_TAXONOMY = [
    "Fit & Sizing Uncertainty",
    "Price Hesitation",
    "Social Validation Gap",
    "Missing Product Information",
    "External Research Needed",
    "Inventory/Availability Anxiety",
    "Comparison Paralysis",
    "Payment/Delivery Friction",
    "Postponement Pattern",
]

RESEARCH_QUESTIONS = {
    "q1_add_to_wishlist": "Why do users add fashion products to Myntra wishlist?",
    "q2_purchase_blockers": "What prevents wishlisted products from being purchased?",
    "q3_uncertainties": "What uncertainties remain after users identify a product they like?",
    "q4_postponement": "What causes users to postpone a purchase?",
    "q5_comparison": "How do users compare multiple shortlisted products?",
    "q6_external_info": "What information do users seek outside Myntra before purchasing?",
    "q7_friction_factors": "What role do fit, size, styling, price, reviews, occasion, and social validation play?",
    "q8_segment_differences": "How do these behaviors differ across user segments?",
    "q9_unmet_needs": "What unmet needs emerge consistently?",
}


def build_extraction_prompt(batch: list[dict]) -> list[dict]:
    """Pass A: tag each review against friction-point schema."""
    friction_list = ", ".join(FRICTION_TAXONOMY)
    reviews_block = "\n".join(
        f'- idx: {idx} | sentiment: {r.get("sentiment", "unknown")} | text: "{r.get("text", "").strip()}"'
        for idx, r in enumerate(batch)
    )

    system = (
        "You are a UX research analyst studying why users add fashion products to "
        "Myntra wishlists but don't convert to purchase. For EACH review, extract "
        "structured friction signals.\n\n"
        "STRICT RULES for friction_points:\n"
        "1. Only tag friction if the review explicitly mentions hesitation, postponement, "
        "   comparison, doubt, or a barrier to purchase.\n"
        "2. Generic praise ('great app', 'good selection') gets EMPTY friction list.\n"
        "3. Service/delivery complaints not tied to a product get tagged as "
        "   'Payment/Delivery Friction' only if explicitly mentioned.\n"
        "4. Include AT MOST 2 friction points per review; if more, the review is likely "
        "   generic and should get an EMPTY list.\n\n"
        "Examples:\n"
        '- "Dress was beautiful but worried it won\'t fit as they show only pics, no try-on video" '
        "-> friction_points: [{friction: 'Fit & Sizing Uncertainty', quote: '...'}]\n"
        '- "Love the style but too expensive right now, waiting for sale" '
        "-> friction_points: [{friction: 'Price Hesitation', quote: '...'}]\n"
        '- "Had 3 items in wishlist, couldn\'t decide which one, finally didn\'t buy" '
        "-> friction_points: [{friction: 'Comparison Paralysis', quote: '...'}]\n"
        '- "Great app, love the collection" -> friction_points: [] (generic praise)\\n\\n'
        "For each friction point, set relationship to exactly one of:\\n"
        '  "blocker" — prevents purchase decision completely\n'
        '  "hesitation" — causes postponement but might convert later\n'
        '  "uncertainty" — user needs more info to decide\n\n'
        f"Only use friction points from this list (or 'Other' if truly none apply): {friction_list}\n"
        "Respond with strict JSON only, matching exactly this shape:\n"
        '{"results": [{'
        '"index": number, '
        '"friction_points": [{"friction": string, "relationship": string, "quote": string}], '
        '"primary_issue": string or null, '
        '"user_segment": one of ["new_customer", "repeat_buyer", "price_sensitive", "quality_conscious", "unclear"], '
        '"sentiment": one of ["positive", "negative", "neutral"], '
        '"likely_to_convert": boolean'
        "}]}"
    )
    user = f"Reviews to analyze:\n{reviews_block}"
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def build_synthesis_prompt(ranked_frictions: list[dict], aggregates: dict, sample_quotes: dict) -> list[dict]:
    """Pass B: narrate over Python-computed friction rankings."""
    system = (
        "You are a product research analyst writing findings for a fashion e-commerce PM. "
        "Friction points have ALREADY been selected and ranked by a system using real counts. "
        "Your job is to write a 1-2 sentence insight for each, using ONLY the provided quotes. "
        "Do not reorder, drop, or add friction points. Do not invent numbers.\n\n"
        "Respond with strict JSON only, matching exactly this shape:\n"
        '{"friction_insights": [{"friction": string, "insight": string}], '
        '"customer_cohorts": [{"name": string, "description": string, "size_percentage": number}], '
        '"top_recommendation": string}'
    )
    user = (
        "Friction points to write insights for, in order:\n"
        f"{ranked_frictions}\n\n"
        "Research questions to address:\n"
        + "\n".join(f"- {k}: {v}" for k, v in RESEARCH_QUESTIONS.items())
        + f"\n\nPre-computed aggregate data (ground truth, do not change):\n{aggregates}\n\n"
        f"Sample real quotes to cite:\n{sample_quotes}"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
