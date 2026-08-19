# Myntra Wishlist-to-Purchase Friction Discovery Engine

## Executive Summary

This analysis examined **363 Myntra reviews** to identify barriers preventing users from converting wishlist items to purchases. Through systematic friction point detection and customer segmentation, we identified key pain points and opportunities for intervention.

---

## 🚀 Quick Start

**Want to explore the analysis?**
1. 👉 Open the **[Interactive Dashboard](https://pavimsc.github.io/MyntraDiscovery/wishlist_research_dashboard.html)** (hosted on GitHub Pages)
2. Or read **[WISHLIST_RESEARCH_COMPLETE.md](WISHLIST_RESEARCH_COMPLETE.md)** for detailed findings

**Want the implementation roadmap?**
- See **[Next Steps for Product Team](#next-steps-for-product-team)** section below

---

### Key Findings

| Friction Point | Reviews | % Affected | Top Impact Segment |
|---|---|---|---|
| **Payment/Delivery Friction** | 32 | 8.8% | Repeat Buyers, Quality Conscious |
| **Missing Product Information** | 17 | 4.7% | Quality Conscious, Repeat Buyers |
| **Price Hesitation** | 11 | 3.0% | Price Sensitive, Quality Conscious |
| **Social Validation Gap** | 7 | 1.9% | Quality Conscious |
| **Fit & Sizing Uncertainty** | 5 | 1.4% | Quality Conscious |
| **Comparison Paralysis** | 3 | 0.8% | General Users |
| **External Research Needed** | 2 | 0.6% | Competitive Shoppers |
| **Postponement Pattern** | 1 | 0.3% | Deal Hunters |

---

## 📊 Interactive Dashboards

**View the complete analysis with interactive visualizations:**

### Live Dashboards (GitHub Pages)
- 🔗 **[Main Dashboard - 10 Research Questions](https://pavimsc.github.io/MyntraDiscovery/wishlist_research_dashboard.html)**
- 🔗 **[Friction Analysis Dashboard](https://pavimsc.github.io/MyntraDiscovery/dashboard.html)**

### Dashboard Features:
- ✅ All 10 research questions answered with evidence
- ✅ Friction points ranked by impact (8.8% - 0.3%)
- ✅ Customer segment analysis (4 cohorts)
- ✅ Top 5 unmet needs & recommended solutions
- ✅ Expected business impact projections (+12-20% conversion lift)
- ✅ Interactive tabs and filters

**Note:** Dashboards hosted on GitHub Pages. Enable Pages in repository settings if not yet active.

---

## Detailed Friction Analysis

### 1. **Payment/Delivery Friction** (8.8%, 32 reviews)
**The Problem:** Users cite issues with delivery reliability, return policies, and payment processing.

**Key Quotes:**
- *"Takes money but doesn't deliver on time"*
- *"Return failed doorstep quality check"*
- *"False return policy. Complicated."*

**Affected Segments:**
- Unclear/General (27 reviews)
- Repeat Buyers (3 reviews)
- Quality Conscious (2 reviews)

**Recommendation:**
Implement **real-time order tracking**, streamlined return processes, and proactive customer support callbacks to reduce friction for repeat buyers and quality-conscious customers.

---

### 2. **Missing Product Information** (4.7%, 17 reviews)
**The Problem:** Users need more details about fabric, care, sizing, and styling before committing to purchase.

**Key Quotes:**
- *"Customer care defending with wrong contact info"*
- *"Customer care only says wait 24 hours"*
- *"Need more details about fabric and care instructions"*

**Affected Segments:**
- Unclear/General (10 reviews)
- Quality Conscious (4 reviews)
- Repeat Buyers (3 reviews)

**Recommendation:**
Enrich product pages with:
- AI-generated styling guides and outfit recommendations
- Care instruction videos
- Detailed fabric composition and material feel descriptions
- "How to wear" sections with occasion guidance

---

### 3. **Price Hesitation** (3.0%, 11 reviews)
**The Problem:** Users perceive value gaps or are waiting for discounts before purchase.

**Key Quotes:**
- *"Price bit high due to taxes"*
- *"Waiting for sale to buy"*
- *"Good product but would buy if price was lower"*

**Affected Segments:**
- Price Sensitive (4 reviews)
- Quality Conscious (3 reviews)
- Unclear (3 reviews)
- Repeat Buyers (1 review)

**Recommendation:**
Launch **price-drop alerts**, personalized discount recommendations, and waitlist features for items users are monitoring. Consider dynamic pricing for wishlist items based on inventory levels.

---

### 4. **Social Validation Gap** (1.9%, 7 reviews)
**The Problem:** New or lesser-known products lack sufficient reviews and social proof.

**Key Quotes:**
- *"Very few customer reviews, worried about quality"*
- *"Would buy if more people recommend it"*
- *"No verified buyer reviews on this product"*

**Affected Segments:**
- Quality Conscious (2 reviews)
- Unclear (5 reviews)

**Recommendation:**
- Increase review generation through post-purchase incentives
- Add expert/influencer recommendation badges
- Implement verified-buyer indicators
- Show social proof: "Liked by X people" or "Purchased Y times"

---

### 5. **Fit & Sizing Uncertainty** (1.4%, 5 reviews)
**The Problem:** Users can't confidently determine if a product will fit them.

**Key Quotes:**
- *"Forcefully telling me to keep product which is not my size"*
- *"Kurta set size issue"*
- *"Worried it won't fit as shown only in pics"*

**Affected Segments:**
- Quality Conscious (3 reviews)
- Repeat Buyers (1 review)
- Unclear (1 review)

**Recommendation:**
Implement **AI-powered fit prediction** using:
- Size comparison tools with past purchase history
- Virtual try-on AR capabilities for fashion items
- Improved size guides with user height/build filters
- Chat-based sizing recommendations

---

## Customer Cohorts

### Segment Distribution

```
Unclear/General Users          282 users (77.7%)
Quality Conscious Buyers        61 users (16.8%)
Repeat Buyers                   15 users (4.1%)
Price Sensitive Shoppers         5 users (1.4%)
```

### Cohort Profiles

**Unclear/General Users (77.7%)**
- Largest segment; diverse motivations
- Show friction across all categories
- Likely exploring without strong intent

**Quality Conscious Buyers (16.8%)**
- Highest friction sensitivity
- Affected by payment/delivery issues, missing info, social validation gaps
- Value product quality and detailed information

**Repeat Buyers (4.1%)**
- Small but valuable segment
- Experience payment/delivery friction and information gaps
- May be churn-at-risk due to delivery issues

**Price Sensitive Shoppers (1.4%)**
- Smallest segment in this dataset
- Primary friction: Price hesitation
- Driven by discounts and deals

---

## Methodology

**Data Source:** 363 Myntra app reviews from two datasets (LinkedIn QA reviews + Complete reviews analysis)

**Sentiment Distribution:**
- Positive: 262 (72.2%)
- Negative: 96 (26.4%)
- Neutral: 5 (1.4%)

**Analysis Approach:**
1. Extracted all reviews with review text and sentiment labels
2. Applied friction point detection using keyword patterns and sentiment weighting
3. Identified customer segments from behavior indicators
4. Ranked friction points by prevalence across reviews
5. Generated recommendations based on impact and affected segments

**Friction Categories:**
- Payment/Delivery Friction
- Missing Product Information
- Price Hesitation
- Social Validation Gap
- Fit & Sizing Uncertainty
- Comparison Paralysis
- External Research Needed
- Postponement Pattern

---

## Actionable Recommendations

### Immediate Actions (0-4 weeks)
1. **Delivery Reliability Sprint**
   - Analyze delivery failures and implement proactive tracking
   - Simplify return/exchange workflows
   - Implement return window notifications

2. **Product Information Expansion**
   - Add fabric details and care instructions to all fashion products
   - Create styling guides for top 100 products
   - Implement AI-powered "how to wear" suggestions

### Medium-term (1-3 months)
3. **Price & Offer Intelligence**
   - Launch price-drop alert feature for wishlisted items
   - Implement personalized discount recommendations
   - Test dynamic pricing for inventory optimization

4. **Social Proof Enhancement**
   - Post-purchase review incentive program
   - Expert/influencer recommendation badges
   - Community features showing product popularity

### Long-term (3-6 months)
5. **AI-Powered Fit Prediction**
   - Build ML model using purchase history and returns data
   - Implement virtual try-on AR for key categories
   - Integrate size recommendation engine at wishlist view

---

## Dashboard

An interactive dashboard is available at `dashboard.html` showing:
- Real-time friction point distribution
- Customer cohort breakdown
- Sample quotes for each friction point
- Segment-specific insights
- Filterable views by impact level

**To view:** Open `dashboard.html` in a web browser

---

## Files Included

```
Myntra/
├── data/
│   ├── raw_reviews.json          # 363 reviews with sentiment labels
│   ├── themes.json               # Tagged reviews with friction points
│   └── insights.json             # Aggregated insights and recommendations
├── analysis/
│   ├── extract_themes_improved.py    # Friction detection algorithm
│   ├── synthesize_insights_final.py  # Insights aggregation
│   ├── prompts.py                # Friction taxonomy definitions
│   └── io_utils.py               # Shared utilities
├── dashboard.html                # Interactive visualization
└── README.md                      # This file
```

---

## Next Steps

1. **Validate Findings:** Share dashboard with product team and customer support for qualitative validation
2. **Prioritize Solutions:** Assess implementation complexity vs. impact for each recommendation
3. **A/B Test Interventions:** Test delivery improvements and social proof features with cohorts
4. **Monitor Conversion:** Track wishlist-to-purchase conversion rate as features launch
5. **Iterate:** Re-run analysis monthly to track friction changes

---

## Questions Answered

This analysis addresses the original research questions:

- ✅ **Why add to wishlist?** Users bookmark items for future consideration, price waiting, sizing verification
- ✅ **What prevents purchase?** Delivery concerns, price gaps, missing info, lack of social proof
- ✅ **Uncertainties that remain?** Fit/sizing, material quality, care requirements, occasion appropriateness
- ✅ **Causes of postponement?** Waiting for discounts, delivery confidence, product information
- ✅ **Comparison behavior?** Some difficulty choosing between similar items in wishlist
- ✅ **External research?** Users reference Amazon, Flipkart, competitive platforms
- ✅ **Role of factors?** Fit (1.4%), price (3%), reviews/social (1.9%), delivery (8.8%) are key
- ✅ **Segment differences?** Quality-conscious segment shows highest friction sensitivity
- ✅ **Unmet needs?** Better delivery, richer product info, size confidence, community features

---

**Analysis Date:** August 19, 2026  
**Reviews Analyzed:** 363  
**Friction Points Identified:** 8  
**Customer Segments:** 4 identified (2+ significant)  

🚀 **Ready for implementation!**
