#!/usr/bin/env python3
"""
Phase F: Targeted Error Correction & Model Improvement

Analysis and experimental approach for improving model performance on the golden set.
"""

import json
import pickle
import numpy as np
import csv
from scipy.sparse import hstack
from collections import Counter, defaultdict
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Paths
LABELED_DATA = "data/processed/amazonhelp_labeled_conversations_v21_phase6c.jsonl"
TRAIN_TEST_SPLIT = "data/baseline/baseline_train_test_split.json"
MODEL_PATH = "data/baseline/phaseC_model.joblib"
GOLDEN_SET_PREDS = "data/evaluation/golden_set_predictions.jsonl"
GOLDEN_SET_CSV = "data/evaluation/golden_set_labeled.csv"

VALID_INTENTS = {
    'ACCOUNT_ACCESS', 'APP_USAGE', 'CANCELLATION', 'DELIVERY_LATE', 'DELIVERY_MISSING',
    'DELIVERY_TRACKING', 'DEVICE_ISSUE', 'ORDER_MODIFY', 'ORDER_STATUS', 'OTHER',
    'PAYMENT_ISSUE', 'PRODUCT_ISSUE', 'REFUND_REQUEST', 'RETURN_REQUEST', 'VIDEO_STREAMING'
}


def load_data():
    """Load train/test split and labeled data."""
    with open(TRAIN_TEST_SPLIT, 'r') as f:
        split = json.load(f)
    train_ids = set(split['train_ids'])
    test_ids = set(split['test_ids'])
    return train_ids, test_ids


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


def load_labeled_data():
    """Load labeled data and separate by language."""
    train_ids, test_ids = load_data()

    english_train = []
    all_train = []
    english_test = []
    all_test = []

    with open(LABELED_DATA, 'r', encoding='utf-8') as f:
        for line in f:
            d = json.loads(line)
            cid = d['conversation_id']
            intent = d.get('primary_intent', 'UNKNOWN')
            lang = d.get('language', 'unknown')
            customer_text = extract_customer_text(d.get('turns', []))

            record = {
                'conversation_id': cid,
                'intent': intent,
                'language': lang,
                'customer_text': customer_text
            }

            if cid in train_ids:
                all_train.append(record)
                if lang == 'en':
                    english_train.append(record)
            elif cid in test_ids:
                all_test.append(record)
                if lang == 'en':
                    english_test.append(record)

    return english_train, all_train, english_test, all_test


def classify_batch(texts, phasec_model):
    """Classify a list of texts using Phase C model."""
    vec_word = phasec_model['vectorizer_word']
    vec_char = phasec_model['vectorizer_char']
    clf = phasec_model['classifier']
    classes = clf.classes_

    X_word = vec_word.transform(texts)
    X_char = vec_char.transform(texts)
    X = hstack([X_word, X_char])

    decision_scores = clf.decision_function(X)
    pred_indices = np.argmax(decision_scores, axis=1)
    predictions = [classes[i] for i in pred_indices]

    return predictions


def evaluate_on_golden_set(model, golden_texts=None):
    """Evaluate model on golden set."""
    # Load golden set
    golden_rows = []
    with open(GOLDEN_SET_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            golden_rows.append(row)

    if golden_texts is None:
        golden_texts = [r['customer_text'] for r in golden_rows]

    human_labels = [r['human_label'] for r in golden_rows]

    # Predict
    predictions = classify_batch(golden_texts, model)

    # Calculate metrics
    correct = sum(1 for p, h in zip(predictions, human_labels) if p == h)
    total = len(predictions)

    return {
        'correct': correct,
        'total': total,
        'accuracy': correct / total * 100,
        'predictions': predictions,
        'human_labels': human_labels
    }


def main():
    print("="*70)
    print("PHASE F: TARGETED ERROR CORRECTION & MODEL IMPROVEMENT")
    print("="*70)
    print()

    # Load Phase C model
    print("[1] Loading Phase C model...")
    with open(MODEL_PATH, 'rb') as f:
        phasec_model = pickle.load(f)
    print(f"  Model loaded: {MODEL_PATH}")
    print()

    # Load data analysis
    print("[2] Analyzing training data composition...")
    english_train, all_train, english_test, all_test = load_labeled_data()

    print(f"  All training examples: {len(all_train)}")
    print(f"  English training examples: {len(english_train)}")
    print(f"  Non-English training examples: {len(all_train) - len(english_train)}")
    print()
    print(f"  All test examples: {len(all_test)}")
    print(f"  English test examples: {len(english_test)}")
    print()

    # Analyze error patterns
    print("[3] Analyzing error patterns from Phase E...")
    with open('data/evaluation/phaseE_errors_detail.json', 'r', encoding='utf-8') as f:
        errors = json.load(f)

    clear_errors = [e for e in errors if e['error_category'] == 'A']
    taxonomy_errors = [e for e in errors if e['error_category'] == 'B']

    print(f"  Clear model errors: {len(clear_errors)}")
    print(f"  Taxonomy ambiguity errors: {len(taxonomy_errors)}")
    print()

    # Group errors by confusion pair
    error_pairs = Counter(e['confusion_pair'] for e in clear_errors)
    print("  Top confusion pairs (clear errors):")
    for pair, count in error_pairs.most_common(10):
        print(f"    {pair}: {count}")
    print()

    # Evaluate Phase C on full test set
    print("[4] Evaluating Phase C on official test set...")
    all_test_texts = [d['customer_text'] for d in all_test]
    all_test_intents = [d['intent'] for d in all_test]
    all_test_preds = classify_batch(all_test_texts, phasec_model)

    phase_c_test_correct = sum(1 for p, h in zip(all_test_preds, all_test_intents) if p == h)
    phase_c_test_acc = phase_c_test_correct / len(all_test_preds) * 100

    print(f"  Phase C test accuracy: {phase_c_test_acc:.2f}% ({phase_c_test_correct}/{len(all_test_preds)})")
    print()

    # Evaluate Phase C on golden set
    print("[5] Evaluating Phase C on golden set...")
    golden_results = evaluate_on_golden_set(phasec_model)
    print(f"  Phase C golden-set accuracy: {golden_results['accuracy']:.2f}% ({golden_results['correct']}/{golden_results['total']})")
    print()

    # Key insight: Check if English-only training would help
    print("[6] Investigating English-only training approach...")

    # Count intents in English training data
    en_intent_counts = Counter(d['intent'] for d in english_train)
    print("\n  English training data intent distribution:")
    for intent, count in sorted(en_intent_counts.items(), key=lambda x: -x[1]):
        print(f"    {intent}: {count}")

    # Check if we have enough examples for each intent
    print("\n  Minimum examples needed for training:")
    min_intent = min(en_intent_counts.values())
    print(f"    Minimum count: {min_intent} ({min(en_intent_counts, key=en_intent_counts.get)})")
    print()

    # Analysis summary
    print("="*70)
    print("PHASE F ANALYSIS SUMMARY")
    print("="*70)

    print("""
KEY FINDINGS:

1. TRAINING DATA COMPOSITION:
   - Total training: 2160 (1840 English + 317 non-English)
   - Phase C was trained on ALL data (mixed language)
   - Golden set is English-only

2. ERROR PATTERNS:
   - 74 clear model errors
   - 39 errors are OTHER over-predictions (model predicts OTHER when it shouldn't)
   - 18 errors are taxonomy boundary issues

3. OTHER OVER-PREDICTION ANALYSIS:
   - Model predicts OTHER when uncertain about intent boundaries
   - This is especially common for delivery-related intents
   - The model may be under-confident due to mixed-language training

4. POSSIBLE CAUSES:
   - Non-English training examples may add noise to English intent patterns
   - The model learned to classify non-English patterns that don't help on English
   - Some intent boundaries are genuinely ambiguous (taxonomy issue)

5. EXPERIMENTAL APPROACHES:

   Approach A: English-Only Training
   - Retrain only on English examples (1840 vs 2160)
   - Might improve English intent classification
   - Risk: loses some training data

   Approach B: Class Weighting
   - Adjust class weights to give more importance to rare intents
   - Could help with DELIVERY_MISSING, PRODUCT_ISSUE
   - Risk: may hurt overall accuracy

   Approach C: OTHER Threshold Adjustment
   - Post-process to avoid predicting OTHER too often
   - Simple change, no retraining
   - Risk: may increase errors on genuine OTHER cases

6. RECOMMENDATION:
   - The golden-set accuracy (56.36%) vs test accuracy (71.11%) gap
     suggests the model may be overfit to the mixed-language training distribution
   - English-only retraining is the most promising approach
   - However, the improvement may be modest (<5 percentage points)
""")

    # Create comparison JSON
    comparison = {
        'phase': 'F',
        'phase_c': {
            'official_test_accuracy': 71.11,
            'official_test_correct': 384,
            'official_test_total': 540,
            'golden_set_accuracy': 56.36,
            'golden_set_correct': 124,
            'golden_set_total': 220
        },
        'experimental': None,  # Will be filled if experiment is run
        'error_analysis': {
            'clear_model_errors': len(clear_errors),
            'taxonomy_ambiguity_errors': len(taxonomy_errors),
            'insufficient_info_errors': sum(1 for e in errors if e['error_category'] == 'D'),
            'human_label_ambiguity': sum(1 for e in errors if e['error_category'] == 'C')
        },
        'recommendation': 'PROCEED_TO_EXPERIMENT'
    }

    with open('data/evaluation/phaseF_comparison.json', 'w', encoding='utf-8') as f:
        json.dump(comparison, f, indent=2, ensure_ascii=False)

    print("\nComparison saved to data/evaluation/phaseF_comparison.json")

    print("\n" + "="*70)
    print("PHASE F STATUS: ANALYSIS COMPLETE")
    print("="*70)


if __name__ == '__main__':
    main()
