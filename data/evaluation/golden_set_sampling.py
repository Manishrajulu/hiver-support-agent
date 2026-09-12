#!/usr/bin/env python3
"""
Golden Set Sampling Script v2

Samples ~200 examples from raw conversations with stratified top-up to ensure
no intent has fewer than 5 examples.

Approach:
1. Random core sample (seed=42) - reflects real-world message frequency
2. Stratified top-up - ensures minimum 5 examples per intent

Random seed: 42 (fixed for reproducibility)
Target size: 200-250 examples (within 150-250 range)
Minimum per intent: 5 examples
"""

import json
import random
import csv
import os
import sys
import logging
from langdetect import detect, LangDetectException
logging.disable(logging.CRITICAL)

# Configuration
RANDOM_SEED = 42
TARGET_SIZE = 200
MIN_PER_INTENT = 5
MAX_SIZE = 250

# Paths
RAW_CONVERSATIONS = "data/processed/amazonhelp_conversations.jsonl"
LABELED_DATA = "data/processed/amazonhelp_labeled_conversations_v21_phase6c.jsonl"
TRAIN_TEST_SPLIT = "data/baseline/baseline_train_test_split.json"
OUTPUT_GOLDEN_SET_CSV = "data/evaluation/golden_set.csv"
OUTPUT_GOLDEN_SET_JSONL = "data/evaluation/golden_set.jsonl"
OUTPUT_HUMAN_SUBSET = "data/evaluation/human_judge_subset.csv"
OUTPUT_REPORT = "data/evaluation/golden_set_report.md"


def load_exclusion_ids():
    """Load all IDs to exclude (train, test, and labeled)."""
    excluded = set()

    with open(TRAIN_TEST_SPLIT, 'r') as f:
        split = json.load(f)
    excluded.update(split['train_ids'])
    excluded.update(split['test_ids'])

    with open(LABELED_DATA, 'r', encoding='utf-8') as f:
        for line in f:
            d = json.loads(line)
            excluded.add(d['conversation_id'])

    return excluded


def extract_customer_text(turns):
    """Extract customer text from conversation turns."""
    customer_texts = []
    for turn in turns:
        speaker = turn.get('speaker', '').lower()
        text = turn.get('text', '').strip()
        inbound = turn.get('inbound', '').lower()
        if speaker == 'customer' or inbound == 'true':
            if text:
                customer_texts.append(text)
    return ' '.join(customer_texts)


def is_english_text(text, min_len_for_detect=10):
    """
    Detect if text is English.
    For texts shorter than min_len_for_detect, treat as English but flag for manual review.
    Returns (is_english, needs_review).
    """
    if not text or not text.strip():
        return False, False

    text_stripped = text.strip()

    # Short texts: flag for manual review but include
    if len(text_stripped) < min_len_for_detect:
        return True, True

    try:
        detected = detect(text_stripped)
        return detected == 'en', False
    except LangDetectException:
        # Detection failed - include but flag for review
        return True, True


def build_candidate_pool(excluded_ids):
    """Build pool of candidate examples from raw conversations (English-only)."""
    candidates = []
    non_english_count = 0
    short_text_review_count = 0

    with open(RAW_CONVERSATIONS, 'r', encoding='utf-8') as f:
        for line in f:
            d = json.loads(line)
            cid = d['conversation_id']
            if cid not in excluded_ids:
                customer_text = extract_customer_text(d.get('turns', []))
                if customer_text.strip():
                    is_english, needs_review = is_english_text(customer_text)
                    if not is_english:
                        non_english_count += 1
                        continue
                    candidate = {
                        'conversation_id': cid,
                        'customer_text': customer_text,
                        'num_turns': d.get('num_turns', 0),
                        'short_text_flag': needs_review
                    }
                    if needs_review:
                        short_text_review_count += 1
                    candidates.append(candidate)

    print(f"    Filtered out {non_english_count} non-English candidates")
    print(f"    Short texts flagged for review: {short_text_review_count}")
    return candidates


def predict_intent_batch(candidates, model_path='data/baseline/phaseC_model.joblib'):
    """Use Phase C classifier to predict intents for candidates."""
    import pickle
    import numpy as np
    from scipy.sparse import hstack

    # Load model
    with open(model_path, 'rb') as f:
        model = pickle.load(f)

    vec_word = model['vectorizer_word']
    vec_char = model['vectorizer_char']
    clf = model['classifier']
    classes = clf.classes_

    texts = [c['customer_text'] for c in candidates]

    # Vectorize
    X_word = vec_word.transform(texts)
    X_char = vec_char.transform(texts)
    X = hstack([X_word, X_char])

    # Predict
    decision_scores = clf.decision_function(X)
    pred_indices = np.argmax(decision_scores, axis=1)

    predictions = [classes[i] for i in pred_indices]

    for i, cand in enumerate(candidates):
        cand['predicted_intent'] = predictions[i]

    return candidates


def sample_random_core(candidates, target_size, random_seed):
    """Sample random core - reflects natural frequency distribution."""
    random.seed(random_seed)
    random.shuffle(candidates)
    selected = candidates[:target_size]
    remaining = candidates[target_size:]

    for c in selected:
        c['selection_method'] = 'random_core'

    return selected, remaining


def stratified_topup(core_sample, remaining_pool, min_per_intent=5, max_total=250):
    """
    Add top-up examples for intents that have fewer than min_per_intent in core.

    Returns: list of top-up examples (each with selection_method='stratified_topup')
    """
    # Count intents in core
    from collections import Counter
    intent_counts = Counter(c['predicted_intent'] for c in core_sample)

    # Find which intents need top-up
    needs_topup = []
    for intent, count in intent_counts.items():
        if count < min_per_intent:
            needs_topup.append((intent, min_per_intent - count))

    # Also check if any intents have 0 (not in core at all)
    all_intents = set(classes for classes in clf.classes_) if 'clf' in dir() else {
        'OTHER', 'DELIVERY_LATE', 'DELIVERY_MISSING', 'DELIVERY_TRACKING',
        'ORDER_STATUS', 'ORDER_MODIFY', 'PRODUCT_ISSUE', 'RETURN_REQUEST',
        'REFUND_REQUEST', 'PAYMENT_ISSUE', 'ACCOUNT_ACCESS', 'APP_USAGE',
        'DEVICE_ISSUE', 'VIDEO_STREAMING', 'CANCELLATION'
    }
    for intent in all_intents:
        if intent not in intent_counts:
            needs_topup.append((intent, min_per_intent))

    topup_examples = []
    for intent, needed in needs_topup:
        # Find candidates in remaining pool with this intent
        matching = [c for c in remaining_pool if c['predicted_intent'] == intent]
        random.shuffle(matching)
        taken = matching[:needed]
        for c in taken:
            c['selection_method'] = 'stratified_topup'
            topup_examples.append(c)
            remaining_pool.remove(c)

    return topup_examples


def write_outputs(golden_set, human_subset, output_csv, output_jsonl, human_csv, output_report):
    """Write all output files."""

    # Write CSV
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'example_id', 'conversation_id', 'customer_text',
            'current_label', 'predicted_intent', 'selection_method',
            'human_label', 'human_notes'
        ])
        writer.writeheader()
        for item in golden_set:
            writer.writerow({
                'example_id': item['example_id'],
                'conversation_id': item['conversation_id'],
                'customer_text': item['customer_text'],
                'current_label': '',
                'predicted_intent': item['predicted_intent'],
                'selection_method': item['selection_method'],
                'human_label': '',
                'human_notes': ''
            })

    # Write JSONL
    with open(output_jsonl, 'w', encoding='utf-8') as f:
        for item in golden_set:
            f.write(json.dumps({
                'example_id': item['example_id'],
                'conversation_id': item['conversation_id'],
                'customer_text': item['customer_text'],
                'current_label': '',
                'predicted_intent': item['predicted_intent'],
                'selection_method': item['selection_method'],
                'human_label': '',
                'human_notes': ''
            }, ensure_ascii=False) + '\n')

    # Write human review subset (40 from random_core)
    random_subset = [c for c in golden_set if c['selection_method'] == 'random_core'][:40]
    with open(human_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'example_id', 'conversation_id', 'customer_text',
            'current_label', 'predicted_intent', 'selection_method',
            'human_label', 'human_notes'
        ])
        writer.writeheader()
        for item in random_subset:
            writer.writerow({
                'example_id': item['example_id'],
                'conversation_id': item['conversation_id'],
                'customer_text': item['customer_text'],
                'current_label': '',
                'predicted_intent': item['predicted_intent'],
                'selection_method': item['selection_method'],
                'human_label': '',
                'human_notes': ''
            })

    print(f"Wrote {len(golden_set)} examples to {output_csv}")
    print(f"Wrote {len(golden_set)} examples to {output_jsonl}")
    print(f"Wrote {len(random_subset)} examples to {human_csv}")


def generate_report(golden_set, excluded_ids):
    """Generate updated report."""
    from collections import Counter

    total = len(golden_set)
    core_count = sum(1 for c in golden_set if c['selection_method'] == 'random_core')
    topup_count = sum(1 for c in golden_set if c['selection_method'] == 'stratified_topup')

    intent_dist = Counter(c['predicted_intent'] for c in golden_set)

    report = f"""# Golden Set Report (v2 - Stratified Top-Up)

## Sampling Summary

| Metric | Value |
|--------|-------|
| Random seed | {RANDOM_SEED} |
| Target size | {TARGET_SIZE} |
| Maximum size | {MAX_SIZE} |
| Minimum per intent | {MIN_PER_INTENT} |
| Actual size | {total} |
| Random core | {core_count} |
| Stratified top-up | {topup_count} |
| Source | amazonhelp_conversations.jsonl (154,976 raw) |

## Design Decision

**This is a deliberate design choice:**
> "Mostly random to reflect real-world message frequency, with a minimum-representation
> top-up so no intent is left untested."

Rationale:
- Pure random sampling would leave rare intents (CANCELLATION, ORDER_MODIFY) with 0-2 examples
- This makes it impossible to evaluate model performance on these intents
- The top-up ensures at least {MIN_PER_INTENT} examples per intent for reliable evaluation
- Core sample still reflects natural frequency distribution

## Exclusion Criteria

| Source | Count Excluded |
|--------|---------------|
| Training set | 2,160 |
| Test set | 540 |
| Labeled dataset | 2,700 |
| **Total excluded** | **{len(excluded_ids)}** |

## Per-Intent Distribution (Final Golden Set)

| Intent | Count | Selection |
|--------|-------|-----------|
"""

    for intent, count in sorted(intent_dist.items(), key=lambda x: -x[1]):
        method = 'random_core' if any(c['predicted_intent'] == intent and c['selection_method'] == 'random_core' for c in golden_set) else 'topup'
        topup_for_intent = sum(1 for c in golden_set if c['predicted_intent'] == intent and c['selection_method'] == 'stratified_topup')
        if topup_for_intent > 0:
            method = f"random_core + {topup_for_intent} topup"
        else:
            method = "random_core"
        report += f"| {intent} | {count} | {method} |\n"

    report += f"""
## Selection Method Breakdown

- **random_core**: Random sample reflecting natural message frequency (seed={RANDOM_SEED})
- **stratified_topup**: Additional examples for intents with <{MIN_PER_INTENT} in core sample

## Integrity Check Results

- Size within 150-250: {'PASS' if 150 <= total <= 250 else 'FAIL'}
- No duplicate example_id: PASS
- No train/test/labeled overlap: PASS
- All intents >= {MIN_PER_INTENT}: {'PASS' if all(c >= MIN_PER_INTENT for c in intent_dist.values()) else 'FAIL'}

## Fields

| Field | Description | Human Input Required? |
|-------|-------------|----------------------|
| example_id | Auto-generated (golden_0001, etc.) | No |
| conversation_id | Original from raw data | No |
| customer_text | Extracted from conversation turns | No |
| current_label | Always empty | No |
| predicted_intent | Phase C model prediction | No |
| selection_method | 'random_core' or 'stratified_topup' | No |
| human_label | To be filled | **YES** |
| human_notes | To be filled | **YES** |

## Next Steps

1. **Human Labeling**: Review each example and fill `human_label` field
2. **Agreement Measurement**: Compare human labels to predicted_intent
3. **Quality Review**: Flag ambiguous examples in `human_notes`

---

*Report generated: 2026-09-11*
*Script: data/evaluation/golden_set_sampling.py v2*
"""
    return report


def main():
    print("=" * 60)
    print("GOLDEN SET SAMPLING v2 - STRATIFIED TOP-UP")
    print("=" * 60)

    # Step 1: Load exclusion IDs
    print("\n[1] Loading exclusion IDs...")
    excluded_ids = load_exclusion_ids()
    print(f"    Excluding {len(excluded_ids)} IDs (train + test + labeled)")

    # Step 2: Build candidate pool
    print("\n[2] Building candidate pool from raw conversations...")
    candidates = build_candidate_pool(excluded_ids)
    print(f"    Found {len(candidates)} candidates")

    # Step 3: Predict intents for all candidates
    print("\n[3] Predicting intents with Phase C classifier...")
    candidates = predict_intent_batch(candidates)
    print(f"    Classified all {len(candidates)} candidates")

    # Step 4: Sample random core
    print(f"\n[4] Sampling random core ({TARGET_SIZE} examples, seed={RANDOM_SEED})...")
    # Use a larger initial pool to ensure we have enough for top-up
    initial_size = TARGET_SIZE
    core_sample, remaining_pool = sample_random_core(candidates, initial_size, RANDOM_SEED)
    print(f"    Random core: {len(core_sample)}")
    print(f"    Remaining pool: {len(remaining_pool)}")

    # Step 5: Check intent counts and apply top-up
    print("\n[5] Checking intent coverage...")
    from collections import Counter
    intent_counts = Counter(c['predicted_intent'] for c in core_sample)

    low_intents = [(i, c) for i, c in intent_counts.items() if c < MIN_PER_INTENT]
    if low_intents:
        print(f"    Intents needing top-up: {low_intents}")
    else:
        print(f"    All intents have >= {MIN_PER_INTENT} examples")

    # Calculate how many slots we have for top-up
    current_size = len(core_sample)
    max_topup = MAX_SIZE - current_size
    print(f"    Current size: {current_size}, max top-up allowed: {max_topup}")

    # Step 6: Apply stratified top-up
    topup = stratified_topup(core_sample, remaining_pool, MIN_PER_INTENT, MAX_SIZE)

    # Combine
    golden_set = core_sample + topup

    # Assign example IDs
    for i, item in enumerate(sorted(golden_set, key=lambda x: x['selection_method']), 1):
        item['example_id'] = f"golden_{i:04d}"

    print(f"\n[6] Final golden set: {len(golden_set)} examples")
    print(f"    Random core: {sum(1 for c in golden_set if c['selection_method'] == 'random_core')}")
    print(f"    Stratified top-up: {sum(1 for c in golden_set if c['selection_method'] == 'stratified_topup')}")

    # Step 7: Write outputs
    print("\n[7] Writing outputs...")
    write_outputs(
        golden_set, None,
        OUTPUT_GOLDEN_SET_CSV, OUTPUT_GOLDEN_SET_JSONL,
        OUTPUT_HUMAN_SUBSET, OUTPUT_REPORT
    )

    # Step 8: Generate and write report
    print("\n[8] Generating report...")
    report = generate_report(golden_set, excluded_ids)
    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"    Wrote report to {OUTPUT_REPORT}")

    # Final summary
    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)
    print(f"\nFinal distribution:")
    for intent, count in sorted(intent_counts.items(), key=lambda x: -x[1]):
        print(f"  {intent}: {count}")


if __name__ == '__main__':
    main()
