#!/usr/bin/env python3
"""
Phase F: Train Experimental Model on English-Only Data

This script trains a Phase C-style model using only English training examples
to see if it improves performance on the English-only golden set.
"""

import json
import os
import sys
import pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from scipy.sparse import hstack
import warnings
import csv
from collections import Counter, defaultdict

warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 70)
print("PHASE F: EXPERIMENTAL MODEL - ENGLISH-ONLY TRAINING")
print("=" * 70)

# =============================================================================
# CONFIGURATION
# =============================================================================

MODEL_PATH = "data/baseline/phaseC_model.joblib"
LABELED_DATA = "data/processed/amazonhelp_labeled_conversations_v21_phase6c.jsonl"
TRAIN_TEST_SPLIT = "data/baseline/baseline_train_test_split.json"
GOLDEN_SET_CSV = "data/evaluation/golden_set_labeled.csv"
OUTPUT_MODEL = "data/baseline/phaseF_experimental_model.joblib"

# =============================================================================
# LOAD DATA
# =============================================================================
print("\n[1] Loading data...")

with open(TRAIN_TEST_SPLIT, 'r') as f:
    split = json.load(f)
    train_ids = set(split['train_ids'])
    test_ids = set(split['test_ids'])

# Load labeled data and filter by language
all_train = []
all_test = []

with open(LABELED_DATA, 'r', encoding='utf-8') as f:
    for line in f:
        d = json.loads(line)
        cid = d['conversation_id']
        intent = d.get('primary_intent', 'UNKNOWN')
        lang = d.get('language', 'unknown')

        # Extract customer text
        customer_texts = []
        for turn in d.get('turns', []):
            speaker = turn.get('speaker', '').lower()
            text = turn.get('text', '').strip()
            inbound = turn.get('inbound', '').lower()
            if speaker == 'customer' or inbound == 'true':
                if text:
                    customer_texts.append(text)
        customer_text = ' '.join(customer_texts)

        record = {
            'conversation_id': cid,
            'intent': intent,
            'language': lang,
            'customer_text': customer_text
        }

        if cid in train_ids:
            all_train.append(record)
        elif cid in test_ids:
            all_test.append(record)

print(f"  Total train: {len(all_train)}")
print(f"  Total test: {len(all_test)}")

# Filter to English only
english_train = [r for r in all_train if r['language'] == 'en']
english_test = [r for r in all_test if r['language'] == 'en']

print(f"  English train: {len(english_train)}")
print(f"  English test: {len(english_test)}")

# Intent distribution in English training
intent_dist = Counter(r['intent'] for r in english_train)
print("\n  English training intent distribution:")
for intent, count in sorted(intent_dist.items(), key=lambda x: -x[1]):
    print(f"    {intent}: {count}")

# =============================================================================
# PREPARE TRAINING DATA
# =============================================================================
print("\n[2] Preparing training data...")

X_train = [r['customer_text'] for r in english_train]
y_train = [r['intent'] for r in english_train]
X_test = [r['customer_text'] for r in english_test]
y_test = [r['intent'] for r in english_test]

print(f"  Training examples: {len(X_train)}")
print(f"  Test examples: {len(X_test)}")

# =============================================================================
# TRAIN MODEL (same config as Phase C)
# =============================================================================
print("\n[3] Training Phase F model (TF-IDF + LinearSVC)...")

# Same vectorizers as Phase C
vec_word = TfidfVectorizer(
    ngram_range=(1, 2),
    max_features=8000,
    min_df=2,
    max_df=0.95,
    sublinear_tf=True,
    analyzer='word'
)

vec_char = TfidfVectorizer(
    ngram_range=(3, 6),
    max_features=5000,
    min_df=2,
    max_df=0.95,
    sublinear_tf=True,
    analyzer='char'
)

# Fit vectorizers
print("  Fitting word vectorizer...")
X_train_word = vec_word.fit_transform(X_train)
X_test_word = vec_word.transform(X_test)

print("  Fitting char vectorizer...")
X_train_char = vec_char.fit_transform(X_train)
X_test_char = vec_char.transform(X_test)

# Combine features
X_train_combined = hstack([X_train_word, X_train_char])
X_test_combined = hstack([X_test_word, X_test_char])

print(f"  Combined feature shape: {X_train_combined.shape}")

# Train classifier with class weight balancing
print("  Training LinearSVC with class_weight='balanced'...")
clf = LinearSVC(
    C=1.0,
    class_weight='balanced',  # Help with imbalanced classes
    max_iter=5000,
    dual=True
)
clf.fit(X_train_combined, y_train)

# Save model
model = {
    'vectorizer_word': vec_word,
    'vectorizer_char': vec_char,
    'classifier': clf
}

with open(OUTPUT_MODEL, 'wb') as f:
    pickle.dump(model, f)

print(f"  Model saved to: {OUTPUT_MODEL}")

# =============================================================================
# EVALUATE ON TEST SET
# =============================================================================
print("\n[4] Evaluating on English test set...")

y_pred_test = clf.predict(X_test_combined)
test_acc = accuracy_score(y_test, y_pred_test)
test_correct = sum(1 for p, h in zip(y_pred_test, y_test) if p == h)

print(f"  Phase F (English-only) test accuracy: {test_acc * 100:.2f}% ({test_correct}/{len(y_test)})")

# =============================================================================
# EVALUATE ON GOLDEN SET
# =============================================================================
print("\n[5] Evaluating on golden set...")

# Load golden set
golden_rows = []
with open(GOLDEN_SET_CSV, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        golden_rows.append(row)

golden_texts = [r['customer_text'] for r in golden_rows]
golden_labels = [r['human_label'] for r in golden_rows]

# Predict
X_golden_word = vec_word.transform(golden_texts)
X_golden_char = vec_char.transform(golden_texts)
X_golden = hstack([X_golden_word, X_golden_char])
y_pred_golden = clf.predict(X_golden)

golden_correct = sum(1 for p, h in zip(y_pred_golden, golden_labels) if p == h)
golden_acc = golden_correct / len(y_pred_golden) * 100

print(f"  Phase F (English-only) golden-set accuracy: {golden_acc:.2f}% ({golden_correct}/{len(y_pred_golden)})")

# =============================================================================
# COMPARE WITH PHASE C
# =============================================================================
print("\n[6] Comparing Phase F with Phase C...")

# Load Phase C model
with open(MODEL_PATH, 'rb') as f:
    phasec_model = pickle.load(f)

phasec_vec_word = phasec_model['vectorizer_word']
phasec_vec_char = phasec_model['vectorizer_char']
phasec_clf = phasec_model['classifier']

# Phase C predictions on golden set
X_golden_word_pc = phasec_vec_word.transform(golden_texts)
X_golden_char_pc = phasec_vec_char.transform(golden_texts)
X_golden_pc = hstack([X_golden_word_pc, X_golden_char_pc])
y_pred_golden_pc = phasec_clf.predict(X_golden_pc)

phasec_golden_correct = sum(1 for p, h in zip(y_pred_golden_pc, golden_labels) if p == h)
phasec_golden_acc = phasec_golden_correct / len(y_pred_golden_pc) * 100

print(f"  Phase C golden-set accuracy: {phasec_golden_acc:.2f}% ({phasec_golden_correct}/{len(y_pred_golden_pc)})")
print(f"  Phase F golden-set accuracy: {golden_acc:.2f}% ({golden_correct}/{len(y_pred_golden)})")
print(f"  Improvement: {golden_acc - phasec_golden_acc:+.2f} percentage points")

# =============================================================================
# ERROR ANALYSIS
# =============================================================================
print("\n[7] Error analysis...")

# Compare predictions
phase_f_errors = [i for i in range(len(y_pred_golden)) if y_pred_golden[i] != golden_labels[i]]
phase_c_errors = [i for i in range(len(y_pred_golden_pc)) if y_pred_golden_pc[i] != golden_labels[i]]

print(f"  Phase C errors: {len(phase_c_errors)}")
print(f"  Phase F errors: {len(phase_f_errors)}")

# Find errors unique to each model
pc_only_errors = set(phase_c_errors) - set(phase_f_errors)
pf_only_errors = set(phase_f_errors) - set(phase_c_errors)
both_errors = set(phase_c_errors) & set(phase_f_errors)

print(f"  Errors unique to Phase C: {len(pc_only_errors)}")
print(f"  Errors unique to Phase F: {len(pf_only_errors)}")
print(f"  Errors in both: {len(both_errors)}")

# Confusion pairs for Phase F
print("\n  Phase F top confusion pairs:")
confusion = Counter()
for i in phase_f_errors:
    confusion[f"{golden_labels[i]} -> {y_pred_golden[i]}"] += 1
for pair, count in confusion.most_common(10):
    print(f"    {pair}: {count}")

# =============================================================================
# SAVE RESULTS
# =============================================================================
print("\n[8] Saving results...")

results = {
    'phase': 'F',
    'training_data': 'English-only',
    'train_examples': len(X_train),
    'test_accuracy': test_acc * 100,
    'test_correct': test_correct,
    'test_total': len(y_test),
    'golden_accuracy': golden_acc,
    'golden_correct': golden_correct,
    'golden_total': len(y_pred_golden),
    'phase_c_golden_accuracy': phasec_golden_acc,
    'improvement': golden_acc - phasec_golden_acc,
    'phase_c_errors': len(phase_c_errors),
    'phase_f_errors': len(phase_f_errors),
    'errors_unique_to_phase_c': len(pc_only_errors),
    'errors_unique_to_phase_f': len(pf_only_errors),
    'errors_in_both': len(both_errors)
}

with open('data/evaluation/phaseF_comparison.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

# Save Phase F predictions
phase_f_preds = []
for i, row in enumerate(golden_rows):
    phase_f_preds.append({
        'example_id': row['example_id'],
        'customer_text': row['customer_text'],
        'human_label': golden_labels[i],
        'phase_c_prediction': y_pred_golden_pc[i],
        'phase_f_prediction': y_pred_golden[i],
        'phase_c_correct': y_pred_golden_pc[i] == golden_labels[i],
        'phase_f_correct': y_pred_golden[i] == golden_labels[i]
    })

with open('data/evaluation/phaseF_predictions.jsonl', 'w', encoding='utf-8') as f:
    for pred in phase_f_preds:
        f.write(json.dumps(pred, ensure_ascii=False) + '\n')

print(f"  Results saved to: data/evaluation/phaseF_comparison.json")
print(f"  Predictions saved to: data/evaluation/phaseF_predictions.jsonl")

# =============================================================================
# FINAL SUMMARY
# =============================================================================
print("\n" + "=" * 70)
print("PHASE F RESULTS SUMMARY")
print("=" * 70)
print(f"""
Training Data:
  - English-only: {len(X_train)} examples (vs 2160 mixed in Phase C)

Test Set (English):
  - Phase F accuracy: {test_acc * 100:.2f}% ({test_correct}/{len(y_test)})

Golden Set (220 English examples):
  - Phase C accuracy: {phasec_golden_acc:.2f}% ({phasec_golden_correct}/220)
  - Phase F accuracy: {golden_acc:.2f}% ({golden_correct}/220)
  - Improvement: {golden_acc - phasec_golden_acc:+.2f} percentage points

Error Analysis:
  - Phase C errors: {len(phase_c_errors)}
  - Phase F errors: {len(phase_f_errors)}
  - Errors fixed by Phase F: {len(pc_only_errors)}
  - New errors introduced: {len(pf_only_errors)}
""")

# Decision
if golden_acc > phasec_golden_acc + 1:
    decision = "CONSIDER PHASE F"
    reason = f"Phase F improves golden-set accuracy by {golden_acc - phasec_golden_acc:.2f} percentage points"
elif golden_acc > phasec_golden_acc:
    decision = "KEEP PHASE C (marginal improvement)"
    reason = "Improvement is less than 1 percentage point"
else:
    decision = "REJECT PHASE F"
    reason = "Phase F does not improve golden-set accuracy"

print(f"Recommendation: {decision}")
print(f"Reason: {reason}")
print("=" * 70)
print("\nPHASE F STATUS: EXPERIMENT COMPLETE")
print("PHASE C OFFICIAL ACCURACY: 71.11%")
print(f"PHASE F EXPERIMENTAL ACCURACY: {test_acc * 100:.2f}%")
print("PRODUCTION MODEL CHANGED: NO")
