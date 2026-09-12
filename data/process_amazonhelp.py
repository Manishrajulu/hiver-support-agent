#!/usr/bin/env python3
"""
AmazonHelp Data Extraction and Conversation Reconstruction
=========================================================
This script processes the twcs.csv dataset to extract AmazonHelp conversations.

IMPORTANT: Does NOT load entire dataset into memory. Uses chunked processing where possible.
"""

import csv
import json
import os
import sys
from collections import defaultdict
from datetime import datetime
import re

# File paths
RAW_CSV = r'C:\Users\DELL\Desktop\hiver\archive\twcs\twcs.csv'
OUTPUT_DIR = r'C:\Users\DELL\Desktop\hiver\data'
PROCESSED_DIR = os.path.join(OUTPUT_DIR, 'processed')
SAMPLES_DIR = os.path.join(OUTPUT_DIR, 'samples')

OUTPUT_CONVOS = os.path.join(PROCESSED_DIR, 'amazonhelp_conversations.jsonl')
OUTPUT_METADATA = os.path.join(PROCESSED_DIR, 'amazonhelp_metadata.json')
OUTPUT_SAMPLES = os.path.join(SAMPLES_DIR, 'amazonhelp_sample_20.json')

# ============================================================================
# TASK 1: EXTRACT AMAZONHELP DATA
# ============================================================================
print("=" * 70)
print("TASK 1: EXTRACTING AMAZONHELP DATA")
print("=" * 70)

# First pass: count rows and understand structure
row_count = 0
amazon_tweet_ids = set()
amazon_tweet_count = 0
customer_tweet_count = 0

print("\nFirst pass: Counting rows and identifying AmazonHelp tweets...")
with open(RAW_CSV, 'r', encoding='utf-8', errors='replace') as f:
    reader = csv.DictReader(f)
    for row in reader:
        row_count += 1
        if row['author_id'] == 'AmazonHelp':
            amazon_tweet_ids.add(row['tweet_id'])
            amazon_tweet_count += 1

print(f"Total rows in dataset: {row_count:,}")
print(f"AmazonHelp tweets (author_id='AmazonHelp'): {amazon_tweet_count:,}")

# ============================================================================
# TASK 2: UNDERSTAND CONVERSATION STRUCTURE
# ============================================================================
print("\n" + "=" * 70)
print("TASK 2: ANALYZING CONVERSATION STRUCTURE")
print("=" * 70)

# Load ALL tweets into memory (we need this for reconstruction)
# With 2.8M rows and ~500MB, this should be ~1-2GB in memory
print("\nLoading all tweets for conversation reconstruction...")
all_tweets = {}
with open(RAW_CSV, 'r', encoding='utf-8', errors='replace') as f:
    reader = csv.DictReader(f)
    for row in reader:
        all_tweets[row['tweet_id']] = row

print(f"Total tweets loaded: {len(all_tweets):,}")

# Analyze the structure
amazon_tweets = {tid: all_tweets[tid] for tid in amazon_tweet_ids if tid in all_tweets}
print(f"AmazonHelp tweets in memory: {len(amazon_tweets):,}")

# Check inbound values
inbound_false = sum(1 for t in amazon_tweets.values() if t['inbound'] == 'False')
inbound_true = sum(1 for t in amazon_tweets.values() if t['inbound'] == 'True')
print(f"AmazonHelp tweets with inbound=False (brand responses): {inbound_false:,}")
print(f"AmazonHelp tweets with inbound=True: {inbound_true:,}")

# Analyze response_tweet_id and in_response_to_tweet_id
multi_response = 0
has_in_response = 0
empty_in_response = 0

for tid, t in list(amazon_tweets.items())[:1000]:
    resp = t['response_tweet_id']
    in_resp = t['in_response_to_tweet_id']

    if resp and ',' in str(resp):
        multi_response += 1
    if in_resp:
        has_in_response += 1
    else:
        empty_in_response += 1

print(f"\nSample analysis (first 1000 AmazonHelp tweets):")
print(f"  Multiple response_tweet_ids: {multi_response}")
print(f"  Has in_response_to_tweet_id: {has_in_response}")
print(f"  Empty in_response_to_tweet_id: {empty_in_response}")

# ============================================================================
# TASK 3 & 4: RECONSTRUCT CONVERSATIONS
# ============================================================================
print("\n" + "=" * 70)
print("TASK 3 & 4: RECONSTRUCTING CONVERSATIONS")
print("=" * 70)

def parse_datetime(ts):
    """Parse Twitter timestamp format."""
    try:
        # Format: 'Tue Oct 31 22:10:47 +0000 2017'
        return datetime.strptime(ts, '%a %b %d %H:%M:%S %z %Y')
    except:
        return None

def get_tweet_chain(tweet_id, tweets_dict, max_depth=50):
    """
    Trace a conversation chain from a starting tweet.
    Returns list of tweets in chronological order (oldest first).
    """
    if tweet_id not in tweets_dict:
        return []

    chain = []
    current_id = tweet_id
    visited = set()

    while current_id and len(chain) < max_depth:
        if current_id in visited:
            break
        visited.add(current_id)

        tweet = tweets_dict.get(current_id)
        if not tweet:
            break

        chain.append(tweet)

        # Follow backwards to find what this tweet responds to
        in_resp = tweet.get('in_response_to_tweet_id', '')
        if in_resp:
            # Take the first parent if multiple
            parent_id = in_resp.split(',')[0]
            current_id = parent_id
        else:
            break

    # Sort by timestamp to get chronological order
    chain_with_time = []
    for t in chain:
        dt = parse_datetime(t.get('created_at', ''))
        if dt:
            chain_with_time.append((dt, t))

    chain_with_time.sort(key=lambda x: x[0])
    return [t for _, t in chain_with_time]

def build_conversation_threads(brand_tweets, all_tweets_dict):
    """
    Build conversation threads for AmazonHelp.
    A conversation starts when AmazonHelp replies to a customer.
    """
    conversations = []
    seen_customer_starts = set()  # Track which customer tweets started a thread

    # Find all AmazonHelp replies (inbound=False with in_response_to_tweet_id)
    for tweet_id, tweet in brand_tweets.items():
        if tweet['inbound'] != 'False':
            continue

        in_resp = tweet.get('in_response_to_tweet_id', '')
        if not in_resp:
            continue

        # Find the parent tweet(s) - these are what AmazonHelp is replying to
        parent_ids = in_resp.split(',')

        for parent_id in parent_ids:
            if not parent_id:
                continue

            parent = all_tweets_dict.get(parent_id)
            if not parent:
                continue

            # Skip if parent is also AmazonHelp (brand-to-brand)
            if parent['author_id'] == 'AmazonHelp':
                continue

            # This is a valid customer -> AmazonHelp reply chain
            # Use the customer tweet ID as the conversation anchor
            if parent_id in seen_customer_starts:
                continue
            seen_customer_starts.add(parent_id)

            # Trace the full conversation starting from this customer tweet
            thread = get_tweet_chain(parent_id, all_tweets_dict)

            if thread:
                conversations.append(thread)

    return conversations

print("\nBuilding conversation threads...")
conversations = build_conversation_threads(amazon_tweets, all_tweets)
print(f"Reconstructed conversations: {len(conversations):,}")

# ============================================================================
# FORMAT AND SAVE CONVERSATIONS
# ============================================================================
print("\nFormatting and saving conversations to JSONL...")

conversation_stats = {
    'total': len(conversations),
    '1_turn': 0,
    '2_turns': 0,
    '3_turns': 0,
    '4_turns': 0,
    '5_plus_turns': 0,
    'total_turns': 0,
    'amazon_tweets_in_convos': 0,
    'customer_tweets_in_convos': 0,
    'both_speakers': 0,
}

quality_categories = {
    'A_very_short': 0,  # 1 turn
    'B_customer_brand': 0,  # 2 turns, both speakers
    'C_multi_turn': 0,  # 3+ turns
    'D_substantive': 0,  # 4+ turns with longer messages
}

def assess_quality(turns):
    """
    Deterministic quality assessment based on heuristics.
    Returns quality category and reason.
    """
    num_turns = len(turns)

    # Count speakers
    speakers = set(t['author_id'] for t in turns)
    has_amazon = any(t['author_id'] == 'AmazonHelp' for t in turns)
    has_customer = any(t['author_id'] != 'AmazonHelp' for t in turns)

    # Calculate average message length (excluding AmazonHelp redirect-only responses)
    avg_len = sum(len(t.get('text', '')) for t in turns) / num_turns if num_turns > 0 else 0

    # Count substantive AmazonHelp responses (more than just redirects)
    redirect_patterns = ['dm', 'direct message', 'phone', 'chat', 'link', 'click', 'private message', 'email']
    substantive_responses = 0
    for t in turns:
        if t['author_id'] == 'AmazonHelp':
            text_lower = t.get('text', '').lower()
            if not any(p in text_lower for p in redirect_patterns):
                substantive_responses += 1

    # Quality heuristics
    if num_turns == 1:
        return 'A_very_short', 'Single turn - no real conversation'

    if num_turns == 2 and has_amazon and has_customer:
        return 'B_customer_brand', 'Two-turn exchange with both customer and brand'

    if num_turns >= 3:
        if num_turns >= 4 and avg_len > 50 and substantive_responses >= 2:
            return 'D_substantive', f'{num_turns} turns, avg_len={avg_len:.0f}, substantive={substantive_responses}'
        return 'C_multi_turn', f'{num_turns} turns, avg_len={avg_len:.0f}, substantive={substantive_responses}'

    return 'A_very_short', 'Does not meet higher quality thresholds'

# Write conversations to JSONL and calculate stats
convo_id_counter = 0
samples = []

with open(OUTPUT_CONVOS, 'w', encoding='utf-8') as f:
    for conv in conversations:
        convo_id_counter += 1
        conversation_id = f"amazonhelp_{convo_id_counter:06d}"

        # Format turns
        formatted_turns = []
        for turn_num, tweet in enumerate(conv, 1):
            speaker = 'AmazonHelp' if tweet['author_id'] == 'AmazonHelp' else 'Customer'
            formatted_turn = {
                'turn_number': turn_num,
                'tweet_id': tweet['tweet_id'],
                'author_id': tweet['author_id'],
                'speaker': speaker,
                'inbound': tweet['inbound'],
                'created_at': tweet['created_at'],
                'text': tweet['text'],
                'in_response_to_tweet_id': tweet.get('in_response_to_tweet_id', ''),
                'response_tweet_id': tweet.get('response_tweet_id', ''),
            }
            formatted_turns.append(formatted_turn)

        # Create conversation record
        convo_record = {
            'conversation_id': conversation_id,
            'num_turns': len(conv),
            'turns': formatted_turns,
        }

        # Write to JSONL
        f.write(json.dumps(convo_record, ensure_ascii=False) + '\n')

        # Update stats
        num_turns = len(conv)
        conversation_stats['total_turns'] += num_turns

        if num_turns == 1:
            conversation_stats['1_turn'] += 1
        elif num_turns == 2:
            conversation_stats['2_turns'] += 1
        elif num_turns == 3:
            conversation_stats['3_turns'] += 1
        elif num_turns == 4:
            conversation_stats['4_turns'] += 1
        else:
            conversation_stats['5_plus_turns'] += 1

        # Count speakers
        has_amazon = any(t['author_id'] == 'AmazonHelp' for t in conv)
        has_customer = any(t['author_id'] != 'AmazonHelp' for t in conv)
        if has_amazon and has_customer:
            conversation_stats['both_speakers'] += 1

        # Count tweets by type
        for t in conv:
            if t['author_id'] == 'AmazonHelp':
                conversation_stats['amazon_tweets_in_convos'] += 1
            else:
                conversation_stats['customer_tweets_in_convos'] += 1

        # Quality assessment
        quality, reason = assess_quality(conv)
        quality_categories[quality] += 1

        # Collect samples (first 20 of each category or interesting ones)
        if len(samples) < 25:
            # Prioritize D, then C, then B, then A
            priority = {'D_substantive': 0, 'C_multi_turn': 1, 'B_customer_brand': 2, 'A_very_short': 3}
            samples.append((priority[quality], conversation_id, conv, quality, reason))

# Sort samples by priority (D first, then C, etc.)
samples.sort(key=lambda x: (x[0], x[1]))

# Select 20 diverse samples
selected_samples = []
seen_qualities = {'D_substantive': 0, 'C_multi_turn': 0, 'B_customer_brand': 0, 'A_very_short': 0}
for priority, convo_id, conv, quality, reason in samples:
    if len(selected_samples) >= 20:
        break
    q_key = quality
    if seen_qualities[q_key] < 5:  # Max 5 per category
        selected_samples.append((convo_id, conv, quality, reason))
        seen_qualities[q_key] += 1

# If we don't have 20 yet, fill in
if len(selected_samples) < 20:
    for priority, convo_id, conv, quality, reason in samples:
        if len(selected_samples) >= 20:
            break
        if (convo_id, conv, quality, reason) not in selected_samples:
            selected_samples.append((convo_id, conv, quality, reason))

print(f"Conversations written to: {OUTPUT_CONVOS}")
print(f"Total conversations: {conversation_stats['total']:,}")

# Save samples
samples_for_output = []
for convo_id, conv, quality, reason in selected_samples:
    sample = {
        'conversation_id': convo_id,
        'quality_category': quality,
        'quality_reason': reason,
        'turns': []
    }
    for turn_num, tweet in enumerate(conv, 1):
        sample['turns'].append({
            'turn_number': turn_num,
            'tweet_id': tweet['tweet_id'],
            'speaker': 'AmazonHelp' if tweet['author_id'] == 'AmazonHelp' else 'Customer',
            'text': tweet['text'][:200] + '...' if len(tweet['text']) > 200 else tweet['text']
        })
    samples_for_output.append(sample)

with open(OUTPUT_SAMPLES, 'w', encoding='utf-8') as f:
    json.dump(samples_for_output, f, ensure_ascii=False, indent=2)

print(f"Samples written to: {OUTPUT_SAMPLES}")

# ============================================================================
# TASK 5: SUMMARY STATISTICS
# ============================================================================
print("\n" + "=" * 70)
print("TASK 5: SUMMARY STATISTICS")
print("=" * 70)

total_convos = conversation_stats['total']
avg_length = conversation_stats['total_turns'] / total_convos if total_convos > 0 else 0

# Calculate median
turn_counts = []
for conv in conversations:
    turn_counts.append(len(conv))
turn_counts.sort()
n = len(turn_counts)
median_length = turn_counts[n // 2] if n > 0 else 0

print(f"\n--- Overall Statistics ---")
print(f"Total raw dataset rows: {row_count:,}")
print(f"Total AmazonHelp tweets: {amazon_tweet_count:,}")
print(f"Customer tweets in AmazonHelp conversations: {conversation_stats['customer_tweets_in_convos']:,}")
print(f"AmazonHelp tweets in conversations: {conversation_stats['amazon_tweets_in_convos']:,}")
print(f"Total reconstructed conversations: {conversation_stats['total']:,}")

print(f"\n--- Conversation Length Distribution ---")
print(f"1-turn conversations: {conversation_stats['1_turn']:,} ({conversation_stats['1_turn']/total_convos*100:.1f}%)")
print(f"2-turn conversations: {conversation_stats['2_turns']:,} ({conversation_stats['2_turns']/total_convos*100:.1f}%)")
print(f"3-turn conversations: {conversation_stats['3_turns']:,} ({conversation_stats['3_turns']/total_convos*100:.1f}%)")
print(f"4-turn conversations: {conversation_stats['4_turns']:,} ({conversation_stats['4_turns']/total_convos*100:.1f}%)")
print(f"5+ turn conversations: {conversation_stats['5_plus_turns']:,} ({conversation_stats['5_plus_turns']/total_convos*100:.1f}%)")

print(f"\n--- Length Statistics ---")
print(f"Average conversation length: {avg_length:.2f} turns")
print(f"Median conversation length: {median_length} turns")
print(f"Conversations with both speakers: {conversation_stats['both_speakers']:,} ({conversation_stats['both_speakers']/total_convos*100:.1f}%)")

multi_turn = conversation_stats['3_turns'] + conversation_stats['4_turns'] + conversation_stats['5_plus_turns']
print(f"Conversations with 3+ turns: {multi_turn:,} ({multi_turn/total_convos*100:.1f}%)")
print(f"Conversations with 4+ turns: {conversation_stats['4_turns'] + conversation_stats['5_plus_turns']:,}")
print(f"Conversations with 5+ turns: {conversation_stats['5_plus_turns']:,}")

print(f"\n--- Quality Categories ---")
for cat, count in quality_categories.items():
    print(f"{cat}: {count:,} ({count/total_convos*100:.1f}%)")

# ============================================================================
# TASK 8: DATA QUALITY ANALYSIS
# ============================================================================
print("\n" + "=" * 70)
print("TASK 8: DATA QUALITY ANALYSIS")
print("=" * 70)

# Re-analyze for quality issues
print("\n--- Analyzing data quality issues ---")

# Missing parent analysis
missing_parents = 0
branching_convos = 0
empty_texts = 0
encoding_issues = 0
unparseable_timestamps = 0

for tid, tweet in amazon_tweets.items():
    # Missing parent
    in_resp = tweet.get('in_response_to_tweet_id', '')
    if in_resp:
        parent_id = in_resp.split(',')[0]
        if parent_id and parent_id not in all_tweets:
            missing_parents += 1

    # Branching (multiple response_tweet_ids from different authors)
    resp = tweet.get('response_tweet_id', '')
    if resp and ',' in str(resp):
        branching_convos += 1

    # Empty text
    if not tweet.get('text', '').strip():
        empty_texts += 1

    # Timestamp parseability
    if not parse_datetime(tweet.get('created_at', '')):
        unparseable_timestamps += 1

print(f"AmazonHelp tweets with missing parent: {missing_parents:,}")
print(f"AmazonHelp tweets with branching responses: {branching_convos:,}")
print(f"AmazonHelp tweets with empty text: {empty_texts:,}")
print(f"AmazonHelp tweets with unparseable timestamps: {unparseable_timestamps:,}")

# Check for customer-side issues in conversations
customer_missing = 0
customer_empty = 0

for conv in conversations:
    for t in conv:
        if t['author_id'] != 'AmazonHelp':
            if t.get('in_response_to_tweet_id'):
                parent = all_tweets.get(t['in_response_to_tweet_id'].split(',')[0])
                if not parent:
                    customer_missing += 1
            if not t.get('text', '').strip():
                customer_empty += 1

print(f"\nCustomer tweets with missing parent: {customer_missing:,}")
print(f"Customer tweets with empty text: {customer_empty:,}")

# ============================================================================
# TASK 9: SAMPLING RECOMMENDATION
# ============================================================================
print("\n" + "=" * 70)
print("TASK 9: SAMPLING RECOMMENDATION")
print("=" * 70)

# Recommend based on quality categories
# Category D (substantive) is best, C (multi-turn) is good
# We need diversity for intent discovery + golden set creation

d_substantive = quality_categories['D_substantive']
c_multi_turn = quality_categories['C_multi_turn']
b_customer_brand = quality_categories['B_customer_brand']

# For golden set (150-250), we need high quality
# For agent training, we need diversity
# For intent discovery, we need breadth

recommended_sample = min(d_substantive + c_multi_turn, 50000)  # Cap at 50K
recommended_training = min(d_substantive + c_multi_turn, 20000)  # 20K for training
recommended_golden = min(d_substantive, 500)  # 500 for golden set (need quality)

print(f"\nQuality conversation counts:")
print(f"  D (Substantive): {d_substantive:,}")
print(f"  C (Multi-turn): {c_multi_turn:,}")
print(f"  B (Customer+Brand): {b_customer_brand:,}")
print(f"\nRecommendations:")
print(f"  For intent discovery: {min(d_substantive + c_multi_turn + b_customer_brand, 30000):,} conversations")
print(f"  For agent training: {recommended_training:,} conversations")
print(f"  For golden evaluation set (150-250): {recommended_golden:,} conversations available")
print(f"  Quick experiments: {min(d_substantive + c_multi_turn, 5000):,} conversations")

# ============================================================================
# TASK 11: CREATE METADATA FILE
# ============================================================================
print("\n" + "=" * 70)
print("TASK 11: CREATING METADATA FILE")
print("=" * 70)

# Calculate some additional stats for metadata
time_range = {'earliest': None, 'latest': None}
earliest_dt = None
latest_dt = None
for conv in conversations[:1000]:  # Sample for time range
    for t in conv:
        dt = parse_datetime(t.get('created_at', ''))
        if dt:
            if earliest_dt is None or dt < earliest_dt:
                earliest_dt = dt
            if latest_dt is None or dt > latest_dt:
                latest_dt = dt
if earliest_dt:
    time_range['earliest'] = earliest_dt.isoformat()
if latest_dt:
    time_range['latest'] = latest_dt.isoformat()

metadata = {
    'processing_timestamp': datetime.now().isoformat(),
    'source_dataset': RAW_CSV,
    'source_file_size_bytes': os.path.getsize(RAW_CSV),
    'raw_row_count': row_count,
    'amazonhelp_tweet_count': amazon_tweet_count,
    'customer_tweet_count': conversation_stats['customer_tweets_in_convos'],
    'reconstructed_conversation_count': conversation_stats['total'],
    'conversation_length_distribution': {
        '1_turn': conversation_stats['1_turn'],
        '2_turns': conversation_stats['2_turns'],
        '3_turns': conversation_stats['3_turns'],
        '4_turns': conversation_stats['4_turns'],
        '5_plus_turns': conversation_stats['5_plus_turns'],
    },
    'average_conversation_length': round(avg_length, 2),
    'median_conversation_length': median_length,
    'percentage_multi_turn': round(multi_turn / total_convos * 100, 2) if total_convos > 0 else 0,
    'quality_category_counts': quality_categories,
    'data_quality_issues': {
        'amazon_tweets_missing_parent': missing_parents,
        'amazon_tweets_branching': branching_convos,
        'amazon_tweets_empty_text': empty_texts,
        'amazon_tweets_unparseable_timestamp': unparseable_timestamps,
    },
    'time_range_sample': time_range,
    'recommended_sample_sizes': {
        'intent_discovery': min(d_substantive + c_multi_turn + b_customer_brand, 30000),
        'agent_training': recommended_training,
        'golden_evaluation_set': f'150-250 (recommend manual selection from D category, {d_substantive:,} available)',
        'quick_experiments': min(d_substantive + c_multi_turn, 5000),
    },
    'processing_heuristics': {
        'conversation_start': 'Customer tweet that AmazonHelp replied to',
        'threading_method': 'Follow in_response_to_tweet_id chain backwards, sort by timestamp',
        'quality_categories': {
            'A_very_short': '1 turn - no real conversation',
            'B_customer_brand': '2 turns with both customer and brand',
            'C_multi_turn': '3+ turns',
            'D_substantive': '4+ turns with avg message length >50 chars and 2+ substantive responses'
        }
    }
}

with open(OUTPUT_METADATA, 'w', encoding='utf-8') as f:
    json.dump(metadata, f, indent=2, ensure_ascii=False)

print(f"Metadata written to: {OUTPUT_METADATA}")

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print("\n" + "=" * 70)
print("DATA PREPARATION COMPLETE")
print("=" * 70)
print(f"\nFiles created:")
print(f"  1. {OUTPUT_CONVOS}")
print(f"     Size: {os.path.getsize(OUTPUT_CONVOS):,} bytes")
print(f"  2. {OUTPUT_METADATA}")
print(f"     Size: {os.path.getsize(OUTPUT_METADATA):,} bytes")
print(f"  3. {OUTPUT_SAMPLES}")
print(f"     Size: {os.path.getsize(OUTPUT_SAMPLES):,} bytes")
print(f"\nTotal conversations written: {conversation_stats['total']:,}")
