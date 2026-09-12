#!/usr/bin/env python3
"""
Analysis of OTHER category in AmazonHelp dataset.
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

# File paths
DATA_FILE = r"C:\Users\DELL\Desktop\hiver\data\processed\amazonhelp_intent_discovery_sample.jsonl"
OUTPUT_DIR = Path(r"C:\Users\DELL\Desktop\hiver\data")

# Leaf patterns from stress_test.py
leaf_patterns = {
    'DELIVERY_LATE': ['late', 'delayed', 'eta', 'expected delivery', 'not arrived yet', 'still waiting'],
    'DELIVERY_MISSING': ['not delivered', 'never received', 'missing', 'shows delivered but'],
    'DELIVERY_TRACKING': ['tracking', 'track', 'track my package', 'tracking number'],
    'DELIVERY_CARRIER': ['gati', 'dtdc', 'fedex', 'ups', 'usps', 'carrier', 'delivery partner'],
    'ORDER_STATUS': ['order status', 'where is my order', 'when will my order', 'order number'],
    'ORDER_MODIFY': ['cancel order', 'change order', 'modify order', 'edit order'],
    'APP_USAGE': ['app', 'website', 'not working', 'error', 'page'],
    'DEVICE_ISSUE': ['kindle', 'fire tv', 'echo', 'alexa', 'tablet', 'device'],
    'VIDEO_STREAMING': ['video', 'streaming', 'prime video', 'subtitle', 'playback'],
    'ACCOUNT_ACCESS': ['login', 'password', 'locked', 'access', 'account suspended'],
    'REFUND_REQUEST': ['refund', 'money back', 'reimburse', 'charged'],
    'PAYMENT_ISSUE': ['payment', 'billing', 'credit card', 'gift card'],
    'RETURN_REQUEST': ['return', 'exchange', 'replacement', 'pick up'],
    'PRODUCT_ISSUE': ['wrong item', 'damaged', 'defective', 'not as described']
}

# Theme keywords for OTHER categorization
theme_keywords = {
    'CASUAL_ORDER_STATUS': ['update', 'pending', 'shipped', 'status', 'any update'],
    'PRIME_ISSUES': ['prime', 'membership', 'prime member', 'cancel prime'],
    'DELIVERY_CASUAL': ['stuff', 'waiting', 'nothing arrived', 'didnt get', 'havent received'],
    'HOW_TO_QUESTIONS': ['how do i', 'how to', 'can i change', 'need to know'],
    'APP_NAVIGATION': ['cant find', 'where is', 'looking for', 'how to find'],
    'REFUND_TIMELINE': ['when will i get', 'how long', 'pending refund'],
    'ADDRESS_ISSUE': ['wrong address', 'change address', 'delivery address'],
    'SUBSCRIPTION': ['subscription', 'cancel subscription', 'amazon fresh']
}


def load_conversations(filepath):
    """Load conversations from JSONL file."""
    conversations = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                conversations.append(json.loads(line))
    return conversations


def get_conversation_text(conv):
    """Extract all customer text from a conversation."""
    texts = []
    for turn in conv.get('turns', []):
        if turn.get('speaker') == 'Customer' and turn.get('inbound'):
            text = turn.get('text', '').lower()
            texts.append(text)
    return ' '.join(texts)


def classify_conversation(text):
    """Classify a conversation based on keyword matching."""
    matched_intents = []
    text_lower = text.lower()

    for intent, patterns in leaf_patterns.items():
        for pattern in patterns:
            if pattern.lower() in text_lower:
                matched_intents.append(intent)
                break

    return matched_intents


def assign_themes(text):
    """Assign themes to an OTHER conversation based on keyword matching."""
    text_lower = text.lower()
    assigned_themes = []

    for theme, keywords in theme_keywords.items():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                assigned_themes.append(theme)
                break

    return assigned_themes


def extract_words(text):
    """Extract words from text for frequency analysis."""
    # Remove URLs
    text = re.sub(r'http\S+', '', text)
    # Remove mentions
    text = re.sub(r'@\w+', '', text)
    # Remove special characters but keep spaces
    text = re.sub(r'[^\w\s]', ' ', text)
    # Split into words
    words = text.split()
    # Filter short words
    words = [w for w in words if len(w) > 2]
    return words


def get_bigrams(words):
    """Get bigrams from a list of words."""
    return [(words[i], words[i+1]) for i in range(len(words)-1)]


def main():
    print("=" * 60)
    print("AMAZONHELP 'OTHER' CATEGORY ANALYSIS")
    print("=" * 60)

    # 1. Load conversations
    print("\n1. Loading conversations...")
    conversations = load_conversations(DATA_FILE)
    print(f"   Loaded {len(conversations)} conversations")

    # 2. Classify each conversation
    print("\n2. Classifying conversations...")
    classified = []
    other_convs = []

    for conv in conversations:
        text = get_conversation_text(conv)
        intents = classify_conversation(text)
        conv['matched_intents'] = intents
        conv['full_text'] = text

        if intents:
            classified.append(conv)
        else:
            other_convs.append(conv)

    print(f"   Classified (with intents): {len(classified)}")
    print(f"   OTHER (no matching intents): {len(other_convs)}")

    # 3. Intent distribution
    print("\n3. Intent Distribution (classified conversations):")
    intent_counts = Counter()
    for conv in classified:
        for intent in conv['matched_intents']:
            intent_counts[intent] += 1

    for intent, count in intent_counts.most_common():
        print(f"   {intent}: {count}")

    # 4. Word frequency and bigram analysis on OTHER
    print("\n4. Word Frequency Analysis on OTHER conversations...")
    all_words = []
    all_bigrams = []

    for conv in other_convs:
        words = extract_words(conv['full_text'])
        all_words.extend(words)
        all_bigrams.extend(get_bigrams(words))

    word_freq = Counter(all_words)
    bigram_freq = Counter(all_bigrams)

    print(f"\n   Total words: {len(all_words)}")
    print(f"   Unique words: {len(word_freq)}")
    print(f"   Total bigrams: {len(all_bigrams)}")

    print("\n   Top 30 words in OTHER:")
    for word, count in word_freq.most_common(30):
        print(f"      {word}: {count}")

    print("\n   Top 20 bigrams in OTHER:")
    for bigram, count in bigram_freq.most_common(20):
        print(f"      {' '.join(bigram)}: {count}")

    # 5. Theme analysis on OTHER
    print("\n5. Theme Analysis on OTHER conversations...")
    theme_counts = Counter()
    theme_examples = defaultdict(list)

    for conv in other_convs:
        themes = assign_themes(conv['full_text'])
        conv['assigned_themes'] = themes

        if themes:
            for theme in themes:
                theme_counts[theme] += 1
                if len(theme_examples[theme]) < 15:  # Keep 15 for sampling
                    theme_examples[theme].append({
                        'conversation_id': conv['conversation_id'],
                        'text': conv['full_text'][:300],  # First 300 chars
                        'themes': themes
                    })
        else:
            theme_counts['NO_THEME_MATCH'] += 1

    print("\n   Theme distribution:")
    for theme, count in theme_counts.most_common():
        print(f"      {theme}: {count}")

    # 6. Multi-intent analysis
    print("\n6. Multi-Intent Analysis...")
    multi_intent_convs = [c for c in classified if len(c['matched_intents']) >= 2]
    print(f"   Conversations with 2+ intents: {len(multi_intent_convs)}")

    # Count intent pairs
    intent_pairs = Counter()
    for conv in multi_intent_convs:
        intents = sorted(conv['matched_intents'])
        for i in range(len(intents)):
            for j in range(i+1, len(intents)):
                pair = (intents[i], intents[j])
                intent_pairs[pair] += 1

    print("\n   Top 20 Intent Pairs in Multi-Intent conversations:")
    for pair, count in intent_pairs.most_common(20):
        print(f"      {pair[0]} + {pair[1]}: {count}")

    # 7. Save output files
    print("\n7. Saving output files...")

    # Save theme counts
    theme_output = {
        'theme_counts': dict(theme_counts),
        'total_other_conversations': len(other_convs),
        'classified_conversations': len(classified),
        'top_words': dict(word_freq.most_common(100)),
        'top_bigrams': {f"{b[0]} {b[1]}": c for b, c in bigram_freq.most_common(100)}
    }

    with open(OUTPUT_DIR / 'processed' / 'other_theme_counts.json', 'w', encoding='utf-8') as f:
        json.dump(theme_output, f, indent=2, ensure_ascii=False)
    print(f"   Saved: other_theme_counts.json")

    # Save multi-intent combinations
    multi_intent_output = {
        'total_multi_intent': len(multi_intent_convs),
        'intent_pair_counts': {f"{p[0]}+{p[1]}": c for p, c in intent_pairs.most_common()},
        'top_multi_intent_examples': [
            {
                'conversation_id': c['conversation_id'],
                'intents': c['matched_intents'],
                'text': c['full_text'][:500]
            }
            for c in multi_intent_convs[:100]
        ]
    }

    with open(OUTPUT_DIR / 'processed' / 'multi_intent_combinations.json', 'w', encoding='utf-8') as f:
        json.dump(multi_intent_output, f, indent=2, ensure_ascii=False)
    print(f"   Saved: multi_intent_combinations.json")

    # Save representative examples for themes with 30+ conversations
    samples_dir = OUTPUT_DIR / 'samples'
    samples_dir.mkdir(exist_ok=True)

    # OTHER representative examples
    other_examples = []
    for theme in theme_counts.keys():
        if theme != 'NO_THEME_MATCH' and theme_counts[theme] >= 30:
            examples = theme_examples.get(theme, [])
            other_examples.extend(examples[:10])

    with open(samples_dir / 'other_representative_examples.json', 'w', encoding='utf-8') as f:
        json.dump(other_examples, f, indent=2, ensure_ascii=False)
    print(f"   Saved: other_representative_examples.json ({len(other_examples)} examples)")

    # Multi-intent sample
    multi_sample = [
        {
            'conversation_id': c['conversation_id'],
            'intents': c['matched_intents'],
            'text': c['full_text'][:500]
        }
        for c in multi_intent_convs[:50]
    ]

    with open(samples_dir / 'multi_intent_sample.json', 'w', encoding='utf-8') as f:
        json.dump(multi_sample, f, indent=2, ensure_ascii=False)
    print(f"   Saved: multi_intent_sample.json ({len(multi_sample)} examples)")

    # Print key findings summary
    print("\n" + "=" * 60)
    print("KEY FINDINGS")
    print("=" * 60)
    print(f"\nTotal conversations: {len(conversations)}")
    print(f"Classified with known intents: {len(classified)} ({100*len(classified)/len(conversations):.1f}%)")
    print(f"OTHER (unclassified): {len(other_convs)} ({100*len(other_convs)/len(conversations):.1f}%)")
    print(f"\nMulti-intent conversations: {len(multi_intent_convs)} ({100*len(multi_intent_convs)/len(classified):.1f}% of classified)")

    # Top themes in OTHER
    print("\nTop THEMES in OTHER conversations:")
    for theme, count in theme_counts.most_common():
        pct = 100 * count / len(other_convs) if other_convs else 0
        print(f"   {theme}: {count} ({pct:.1f}%)")

    # Top intents in multi-intent
    print("\nTop INTENTS in multi-intent conversations:")
    multi_intent_intents = Counter()
    for conv in multi_intent_convs:
        for intent in conv['matched_intents']:
            multi_intent_intents[intent] += 1
    for intent, count in multi_intent_intents.most_common():
        print(f"   {intent}: {count}")

    print("\n" + "=" * 60)
    print("Analysis complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()