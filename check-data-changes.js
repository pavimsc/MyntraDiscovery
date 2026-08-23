#!/usr/bin/env node

/**
 * Smart Change Detection for Review Data
 *
 * Checks if review data has changed since last analysis
 * Only runs full analysis if changes are detected
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const DATA_FILES = [
    'data/raw_reviews.json',
    '/root/.claude/uploads/67b92f82-9a6f-5f91-9a45-c4568918eb03/0d1a3627-wishlist_reviews.csv'
];

const HASH_FILE = 'data/.data-hash';

/**
 * Calculate hash of a file
 */
function getFileHash(filePath) {
    try {
        if (!fs.existsSync(filePath)) {
            return null;
        }
        const content = fs.readFileSync(filePath, 'utf-8');
        return crypto.createHash('md5').update(content).digest('hex');
    } catch (error) {
        console.error(`Error hashing ${filePath}:`, error.message);
        return null;
    }
}

/**
 * Get current state of all data files
 */
function getCurrentState() {
    const state = {};
    DATA_FILES.forEach(file => {
        state[file] = getFileHash(file);
    });
    return state;
}

/**
 * Load previous state
 */
function getPreviousState() {
    try {
        if (fs.existsSync(HASH_FILE)) {
            return JSON.parse(fs.readFileSync(HASH_FILE, 'utf-8'));
        }
    } catch (error) {
        console.error('Error loading previous state:', error.message);
    }
    return {};
}

/**
 * Save current state
 */
function saveState(state) {
    try {
        fs.writeFileSync(HASH_FILE, JSON.stringify(state, null, 2));
    } catch (error) {
        console.error('Error saving state:', error.message);
    }
}

/**
 * Check if data has changed
 */
function hasDataChanged(currentState, previousState) {
    for (const file of DATA_FILES) {
        if (currentState[file] !== previousState[file]) {
            return true;
        }
    }
    return false;
}

/**
 * Main logic
 */
function main() {
    console.log('\n🔍 Checking for data changes...\n');

    const currentState = getCurrentState();
    const previousState = getPreviousState();

    // First run - no previous state
    if (Object.keys(previousState).length === 0) {
        console.log('✅ First run detected - analyzing data');
        saveState(currentState);
        process.exit(0); // Exit code 0 = run analysis
    }

    // Check for changes
    if (hasDataChanged(currentState, previousState)) {
        console.log('✅ Data changes detected!');
        console.log('\nChanged files:');
        DATA_FILES.forEach(file => {
            if (currentState[file] !== previousState[file]) {
                console.log(`   📝 ${path.basename(file)}`);
                console.log(`      Old hash: ${previousState[file]}`);
                console.log(`      New hash: ${currentState[file]}`);
            }
        });
        console.log('\n🚀 Running full analysis...\n');
        saveState(currentState);
        process.exit(0); // Exit code 0 = run analysis
    } else {
        console.log('❌ No data changes detected');
        console.log('⏭️  Skipping analysis - data is identical\n');
        process.exit(1); // Exit code 1 = skip analysis
    }
}

main();
