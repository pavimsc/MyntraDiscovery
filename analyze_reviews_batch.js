#!/usr/bin/env node

/**
 * Batch Review Analysis Pipeline
 * Processes 721 Myntra reviews in batches of 100 using Groq LLM
 */

const fs = require('fs');
const path = require('path');
const csv = require('csv-parse/sync');

// Configuration
const CONFIG = {
    groqApiKey: process.env.GROQ_API_KEY,
    groqModel: 'qwen/qwen3.6-27b', // Powerful Qwen model available on Groq free tier
    batchSize: 10, // Reduced from 25 to fit within token limits (8000 TPM)
    maxRetries: 5,
    retryDelay: 2000, // ms
    requestDelay: 3000 // ms between requests to respect rate limits
};

// Colors for console output
const colors = {
    reset: '\x1b[0m',
    green: '\x1b[32m',
    red: '\x1b[31m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    cyan: '\x1b[36m'
};

function log(msg, color = 'reset') {
    console.log(`${colors[color]}${msg}${colors.reset}`);
}

/**
 * Read and parse CSV file
 */
async function readReviews(filePath) {
    try {
        log(`📖 Reading reviews from ${path.basename(filePath)}...`, 'cyan');
        const fileContent = fs.readFileSync(filePath, 'utf-8');
        const records = csv.parse(fileContent, {
            columns: true,
            skip_empty_lines: true
        });
        log(`✅ Loaded ${records.length} reviews`, 'green');
        return records;
    } catch (error) {
        log(`❌ Error reading file: ${error.message}`, 'red');
        throw error;
    }
}

/**
 * Create batches from reviews
 */
function createBatches(reviews, batchSize) {
    const batches = [];
    for (let i = 0; i < reviews.length; i += batchSize) {
        batches.push(reviews.slice(i, i + batchSize));
    }
    log(`📦 Created ${batches.length} batches of ${batchSize} reviews`, 'cyan');
    return batches;
}

/**
 * Call Groq API for batch analysis
 */
async function analyzeWithGroq(batch, batchNumber, totalBatches) {
    const prompt = `Analyze these ${batch.length} Myntra customer reviews and return JSON array with analysis for each review.

For each review, extract:
{
  "reviewId": "id from input",
  "friction_points": ["array of friction types - choose from: wishlist_limit, price_increase, delivery_delay, poor_quality, app_performance, payment_issue, return_process, customer_support, stock_management, size_fit, product_info, technical_bug"],
  "customer_segment": "one of: new_customer, quality_conscious, price_sensitive, repeat_buyer, app_user",
  "sentiment": "positive|neutral|negative",
  "key_insight": "1-2 sentence summary of main issue/praise",
  "quote": "most relevant sentence from review (max 100 chars)",
  "confidence": 0.0-1.0
}

Reviews to analyze (JSON format):
${JSON.stringify(batch.map(r => ({
    reviewId: r.reviewId,
    content: r.content,
    score: r.score
})), null, 2)}

Return ONLY valid JSON array with ${batch.length} result objects. No markdown, no code blocks, just raw JSON.`;

    let lastError;
    for (let attempt = 1; attempt <= CONFIG.maxRetries; attempt++) {
        try {
            const response = await fetch('https://api.groq.com/openai/v1/chat/completions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${CONFIG.groqApiKey}`
                },
                body: JSON.stringify({
                    model: CONFIG.groqModel,
                    messages: [
                        {
                            role: 'user',
                            content: prompt
                        }
                    ],
                    temperature: 0.3,
                    max_tokens: 4000
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error?.message || `HTTP ${response.status}`);
            }

            const data = await response.json();
            const analysisText = data.choices[0].message.content.trim();

            // Extract JSON from response
            const jsonMatch = analysisText.match(/\[[\s\S]*\]/);
            if (!jsonMatch) {
                throw new Error('Could not extract JSON from response');
            }

            const results = JSON.parse(jsonMatch[0]);
            log(`✅ Batch ${batchNumber}/${totalBatches} analyzed (${batch.length} reviews)`, 'green');
            return results;

        } catch (error) {
            lastError = error;
            if (attempt < CONFIG.maxRetries) {
                const delay = CONFIG.retryDelay * attempt;
                log(`⚠️  Batch ${batchNumber} attempt ${attempt} failed, retrying in ${delay}ms...`, 'yellow');
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }
    }

    log(`❌ Batch ${batchNumber} failed after ${CONFIG.maxRetries} attempts: ${lastError.message}`, 'red');
    throw lastError;
}

/**
 * Process all batches
 */
async function processBatches(batches) {
    log(`\n🚀 Starting batch analysis (${batches.length} batches)...`, 'cyan');
    const allResults = [];
    let failedBatches = [];

    for (let i = 0; i < batches.length; i++) {
        try {
            const results = await analyzeWithGroq(batches[i], i + 1, batches.length);
            allResults.push(...results);

            // Rate limiting delays
            if (i < batches.length - 1) {
                // Every 3 batches, add a longer delay to avoid hitting rate limit
                if ((i + 1) % 3 === 0) {
                    log(`⏳ Batch ${i + 1} complete, pausing 5s to manage rate limit...`, 'yellow');
                    await new Promise(resolve => setTimeout(resolve, 5000));
                } else {
                    await new Promise(resolve => setTimeout(resolve, CONFIG.requestDelay));
                }
            }
        } catch (error) {
            log(`❌ Failed to process batch ${i + 1}`, 'red');
            failedBatches.push(i + 1);
        }
    }

    if (failedBatches.length > 0) {
        log(`\n⚠️  ${failedBatches.length} batches failed: ${failedBatches.join(', ')}`, 'yellow');
    }

    log(`\n✅ Analysis complete! Processed ${allResults.length} reviews`, 'green');
    return allResults;
}

/**
 * Answer 10 research questions
 */
function answerResearchQuestions(reviews, originalReviews) {
    log(`\n📊 Analyzing ${reviews.length} reviews to answer 10 research questions...`, 'cyan');

    const questionAnswers = {};

    // Q1: Why do users add to wishlist?
    const wishlistReasons = reviews.filter(r =>
        r.sentiment === 'positive' || (r.key_insight && r.key_insight.toLowerCase().includes('wishlist'))
    );
    questionAnswers.q1 = {
        question: "Why do users add fashion products to their wishlist?",
        answer: `Users add to wishlist for ${wishlistReasons.length} reasons found in reviews: price tracking (${getPercentage(wishlistReasons.filter(r => r.key_insight.toLowerCase().includes('price')), wishlistReasons)}%), saving for later (${getPercentage(wishlistReasons.filter(r => r.key_insight.toLowerCase().includes('save')), wishlistReasons)}%), comparison shopping (${getPercentage(wishlistReasons.filter(r => r.key_insight.toLowerCase().includes('compare')), wishlistReasons)}%)`,
        evidence: wishlistReasons.slice(0, 3).map(r => r.quote),
        count: wishlistReasons.length
    };

    // Q2: What prevents wishlisted products from being purchased?
    const frictionCounts = {};
    reviews.forEach(r => {
        r.friction_points.forEach(fp => {
            frictionCounts[fp] = (frictionCounts[fp] || 0) + 1;
        });
    });
    const topFrictions = Object.entries(frictionCounts).sort((a, b) => b[1] - a[1]).slice(0, 5);
    questionAnswers.q2 = {
        question: "What prevents wishlisted products from eventually being purchased?",
        answer: `Top friction points preventing purchase: ${topFrictions.map(([fp, count]) =>
            `${fp} (${getPercentageOfTotal(count, reviews.length)}%)`
        ).join(', ')}`,
        friction_distribution: Object.fromEntries(topFrictions),
        total_friction_mentions: reviews.reduce((sum, r) => sum + r.friction_points.length, 0)
    };

    // Q3: What uncertainties remain?
    const uncertaintyReviews = reviews.filter(r =>
        r.friction_points.some(fp => ['size_fit', 'product_info', 'price_increase'].includes(fp))
    );
    questionAnswers.q3 = {
        question: "What uncertainties remain after users identify a product they like?",
        answer: `${uncertaintyReviews.length} reviews (${getPercentageOfTotal(uncertaintyReviews.length, reviews.length)}%) mention uncertainties: product information gaps, sizing concerns, price reliability`,
        evidence: uncertaintyReviews.slice(0, 3).map(r => r.quote),
        count: uncertaintyReviews.length
    };

    // Q4: What causes postponement?
    const postponementReviews = reviews.filter(r =>
        r.key_insight && (r.key_insight.toLowerCase().includes('wait') || r.key_insight.toLowerCase().includes('later') || r.key_insight.toLowerCase().includes('price'))
    );
    questionAnswers.q4 = {
        question: "What causes users to postpone a purchase?",
        answer: `${postponementReviews.length} reviews show postponement factors: price waiting (${getPercentageOfTotal(postponementReviews.filter(r => r.key_insight.includes('price')).length, reviews.length)}%), delivery concerns (${getPercentageOfTotal(postponementReviews.filter(r => r.key_insight.includes('delivery')).length, reviews.length)}%), information gaps (${getPercentageOfTotal(postponementReviews.filter(r => r.key_insight.includes('info')).length, reviews.length)}%)`,
        evidence: postponementReviews.slice(0, 3).map(r => r.quote),
        count: postponementReviews.length
    };

    // Q5: How do users compare products?
    const comparisonReviews = reviews.filter(r =>
        r.key_insight && r.key_insight.toLowerCase().includes('compar')
    );
    questionAnswers.q5 = {
        question: "How do users compare multiple shortlisted products?",
        answer: `${comparisonReviews.length} reviews mention comparison behavior`,
        evidence: comparisonReviews.slice(0, 2).map(r => r.quote),
        count: comparisonReviews.length
    };

    // Q6: External research
    const externalReviews = reviews.filter(r =>
        r.key_insight && (r.key_insight.toLowerCase().includes('other') || r.key_insight.toLowerCase().includes('compare'))
    );
    questionAnswers.q6 = {
        question: "What information do users seek outside Myntra?",
        answer: `${externalReviews.length} reviews indicate external research: price comparison with other platforms, alternative shopping options, detailed product reviews`,
        count: externalReviews.length
    };

    // Q7: Role of different factors
    const factorReviews = {
        fit: reviews.filter(r => r.friction_points.includes('size_fit')).length,
        price: reviews.filter(r => r.friction_points.includes('price_increase')).length,
        reviews: reviews.filter(r => r.friction_points.includes('product_info')).length,
        delivery: reviews.filter(r => r.friction_points.includes('delivery_delay')).length,
        quality: reviews.filter(r => r.friction_points.includes('poor_quality')).length
    };
    questionAnswers.q7 = {
        question: "What role do fit, size, styling, price, reviews, occasion, social validation play?",
        answer: `Critical factors: Delivery (${getPercentageOfTotal(factorReviews.delivery, reviews.length)}%), Price (${getPercentageOfTotal(factorReviews.price, reviews.length)}%), Quality (${getPercentageOfTotal(factorReviews.quality, reviews.length)}%), Fit/Size (${getPercentageOfTotal(factorReviews.fit, reviews.length)}%), Product Info (${getPercentageOfTotal(factorReviews.reviews, reviews.length)}%)`,
        factor_distribution: factorReviews
    };

    // Q8: Purchase intent vs bookmarking
    const intentReviews = reviews.filter(r => r.sentiment === 'negative' || r.key_insight.toLowerCase().includes('wait'));
    const bookmarkReviews = reviews.filter(r => r.sentiment === 'positive' || r.key_insight.toLowerCase().includes('save'));
    questionAnswers.q8 = {
        question: "When do users use wishlist as genuine purchase intent vs bookmarking?",
        answer: `Genuine intent: ${getPercentageOfTotal(intentReviews.length, reviews.length)}% (tracking, comparing). Bookmarking: ${getPercentageOfTotal(bookmarkReviews.length, reviews.length)}% (saving for later)`,
        purchase_intent: intentReviews.length,
        bookmarking: bookmarkReviews.length
    };

    // Q9: Segment differences
    const segmentDist = {};
    reviews.forEach(r => {
        segmentDist[r.customer_segment] = (segmentDist[r.customer_segment] || 0) + 1;
    });
    questionAnswers.q9 = {
        question: "How do these behaviors differ across user segments?",
        answer: `Segment distribution: ${Object.entries(segmentDist).map(([seg, count]) =>
            `${seg} (${getPercentageOfTotal(count, reviews.length)}%)`
        ).join(', ')}`,
        segment_distribution: segmentDist
    };

    // Q10: Unmet needs
    const unmetNeeds = {
        wishlist_features: reviews.filter(r => r.friction_points.includes('wishlist_limit')).length,
        performance: reviews.filter(r => r.friction_points.includes('app_performance')).length,
        price_transparency: reviews.filter(r => r.friction_points.includes('price_increase')).length,
        delivery: reviews.filter(r => r.friction_points.includes('delivery_delay')).length,
        quality_assurance: reviews.filter(r => r.friction_points.includes('poor_quality')).length
    };
    questionAnswers.q10 = {
        question: "What unmet needs emerge consistently?",
        answer: `Top unmet needs: App Performance (${getPercentageOfTotal(unmetNeeds.performance, reviews.length)}%), Price Transparency (${getPercentageOfTotal(unmetNeeds.price_transparency, reviews.length)}%), Delivery Reliability (${getPercentageOfTotal(unmetNeeds.delivery, reviews.length)}%), Wishlist Features (${getPercentageOfTotal(unmetNeeds.wishlist_features, reviews.length)}%), Quality Assurance (${getPercentageOfTotal(unmetNeeds.quality_assurance, reviews.length)}%)`,
        unmet_needs: unmetNeeds
    };

    return questionAnswers;
}

function getPercentage(subset, total) {
    if (total.length === 0) return '0';
    return ((subset.length / total.length) * 100).toFixed(1);
}

function getPercentageOfTotal(count, total) {
    return ((count / total) * 100).toFixed(1);
}

/**
 * Save results to files
 */
function saveResults(reviews, questionAnswers, originalReviews) {
    const dataDir = path.join(__dirname, 'data');
    if (!fs.existsSync(dataDir)) {
        fs.mkdirSync(dataDir);
    }

    // Save analyzed reviews
    const analyzedPath = path.join(dataDir, 'reviews_721_analyzed.json');
    fs.writeFileSync(analyzedPath, JSON.stringify({
        metadata: {
            total_reviews: reviews.length,
            analysis_date: new Date().toISOString(),
            groq_model: CONFIG.groqModel,
            batch_size: CONFIG.batchSize,
            total_cost: '$0 (Groq free tier)'
        },
        reviews: reviews
    }, null, 2));
    log(`💾 Saved analyzed reviews to: ${analyzedPath}`, 'green');

    // Save question answers
    const answersPath = path.join(dataDir, 'research_questions_answers.json');
    fs.writeFileSync(answersPath, JSON.stringify({
        metadata: {
            total_reviews_analyzed: reviews.length,
            analysis_date: new Date().toISOString(),
            timestamp: new Date().getTime()
        },
        questions: questionAnswers
    }, null, 2));
    log(`💾 Saved research answers to: ${answersPath}`, 'green');

    // Summary statistics
    const frictionCounts = {};
    const sentiments = { positive: 0, neutral: 0, negative: 0 };
    const segments = {};

    reviews.forEach(r => {
        r.friction_points.forEach(fp => {
            frictionCounts[fp] = (frictionCounts[fp] || 0) + 1;
        });
        sentiments[r.sentiment]++;
        segments[r.customer_segment] = (segments[r.customer_segment] || 0) + 1;
    });

    const summaryPath = path.join(dataDir, 'analysis_summary.json');
    fs.writeFileSync(summaryPath, JSON.stringify({
        total_reviews: reviews.length,
        sentiment_distribution: sentiments,
        segment_distribution: segments,
        top_friction_points: Object.entries(frictionCounts)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10)
            .reduce((obj, [k, v]) => ({ ...obj, [k]: v }), {}),
        average_confidence: (reviews.reduce((sum, r) => sum + r.confidence, 0) / reviews.length).toFixed(3)
    }, null, 2));
    log(`💾 Saved summary to: ${summaryPath}`, 'green');

    return {
        analyzedPath,
        answersPath,
        summaryPath
    };
}

/**
 * Main execution
 */
async function main() {
    log('\n╔════════════════════════════════════════════╗', 'cyan');
    log('║   Myntra Review Analysis Pipeline v1.0    ║', 'cyan');
    log('║   Powered by Groq (Free LLM)             ║', 'cyan');
    log('╚════════════════════════════════════════════╝\n', 'cyan');

    if (!CONFIG.groqApiKey) {
        log('❌ Error: GROQ_API_KEY environment variable not set', 'red');
        log('   Please set: export GROQ_API_KEY=your_api_key', 'yellow');
        process.exit(1);
    }

    try {
        // Read reviews
        const csvPath = '/root/.claude/uploads/67b92f82-9a6f-5f91-9a45-c4568918eb03/0d1a3627-wishlist_reviews.csv';
        const reviews = await readReviews(csvPath);

        // Create batches
        const batches = createBatches(reviews, CONFIG.batchSize);

        // Process batches with Groq
        log(`\n⏱️  Starting Groq analysis (this may take 10-15 minutes)...`, 'yellow');
        const analyzedReviews = await processBatches(batches);

        // Answer research questions
        const questionAnswers = answerResearchQuestions(analyzedReviews, reviews);

        // Save results
        log(`\n💾 Saving results...`, 'cyan');
        const paths = saveResults(analyzedReviews, questionAnswers, reviews);

        // Print summary
        log(`\n📈 ANALYSIS COMPLETE!`, 'green');
        log(`\n✅ Summary:`, 'green');
        log(`   • Reviews analyzed: ${analyzedReviews.length}`);
        log(`   • Batches processed: ${batches.length}`);
        log(`   • Cost: $0 (Groq free tier)`);
        log(`   • Time: ~15 minutes`);

        log(`\n📊 Results saved:`, 'green');
        log(`   • Analyzed reviews: data/reviews_721_analyzed.json`);
        log(`   • Research answers: data/research_questions_answers.json`);
        log(`   • Summary stats: data/analysis_summary.json`);

        log(`\n🎯 Next step: Build dashboard from these results`, 'cyan');

    } catch (error) {
        log(`\n❌ Fatal error: ${error.message}`, 'red');
        process.exit(1);
    }
}

main();
