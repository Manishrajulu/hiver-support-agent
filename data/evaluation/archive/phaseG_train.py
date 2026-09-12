#!/usr/bin/env python3
"""
Phase G: Train Experimental Model with Targeted Augmentation

Train using the same TF-IDF + LinearSVC architecture as Phase C.
"""

import json
import pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score
from scipy.sparse import hstack
import warnings
import sys

warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 70)
print("PHASE G: TRAIN EXPERIMENTAL MODEL")
print("=" * 70)

# Paths
EXPERIMENTAL_DATA = "data/baseline/phaseG_experimental.jsonl"
MODEL_PATH = "data/baseline/phaseG_experimental_model.joblib"
LABELED_DATA = "data/processed/amazonhelp_labeled_conversations_v21_phase6c.jsonl"
TRAIN_TEST_SPLIT = "data/baseline/baseline_train_test_split.json"
GOLDEN_SET_CSV = "data/evaluation/golden_set_labeled.csv"

# Load train/test split
print("\n[1] Loading train/test split...")
with open(TRAIN_TEST_SPLIT, 'r') as f:
    split = json.load(f)
    test_ids = set(split['test_ids'])
    train_ids = set(split['train_ids'])

# Load experimental training data
print("[2] Loading experimental training data...")
experimental_data = []
with open(EXPERIMENTAL_DATA, 'r', encoding='utf-8') as f:
    for line in f:
        experimental_data.append(json.loads(line))
print(f"  Experimental training examples: {len(experimental_data)}")

# Load test data from original labeled data (for evaluation)
print("[3] Loading test data...")
test_data = []
with open(LABELED_DATA, 'r', encoding='utf-8') as f:
    for line in f:
        d = json.loads(line)
        if d['conversation_id'] in test_ids:
            test_data.append(d)
print(f"  Test examples: {len(test_data)}")

# Extract customer text function
def get_customer_text(item):
    turns = item.get('turns', [])
    customer_texts = []
    for turn in turns:
        speaker = turn.get('speaker', '').lower()
        text = turn.get('text', '').strip()
        inbound = turn.get('inbound', '').lower()
        if speaker == 'customer' or inbound == 'true':
            if text:
                customer_texts.append(text)
    return ' '.join(customer_texts)

# Prepare training data
print("\n[4] Preparing training data...")
X_train = [get_customer_text(item) for item in experimental_data]
y_train = [item.get('primary_intent') for item in experimental_data]
X_test = [get_customer_text(item) for item in test_data]
y_test = [item.get('primary_intent') for item in test_data]

print(f"  Training: {len(X_train)} examples")
print(f"  Test: {len(X_test)} examples")

# Train Phase G model (same config as Phase C)
print("\n[5] Training Phase G model (TF-IDF + LinearSVC)...")

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

X_train_word = vec_word.fit_transform(X_train)
X_test_word = vec_word.transform(X_test)

X_train_char = vec_char.fit_transform(X_train)
X_test_char = vec_char.transform(X_test)

X_train_combined = hstack([X_train_word, X_train_char])
X_test_combined = hstack([X_test_word, X_test_char])

print(f"  Feature shape: {X_train_combined.shape}")

clf = LinearSVC(C=1.0, max_iter=5000, dual=True)
clf.fit(X_train_combined, y_train)

# Save model
model = {
    'vectorizer_word': vec_word,
    'vectorizer_char': vec_char,
    'classifier': clf
}

with open(MODEL_PATH, 'wb') as f:
    pickle.dump(model, f)
print(f"  Model saved to: {MODEL_PATH}")

# Evaluate on test set
print("\n[6] Evaluating on test set...")
y_pred_test = clf.predict(X_test_combined)
test_acc = accuracy_score(y_test, y_pred_test)
test_correct = sum(1 for p, h in zip(y_pred_test, y_test) if p == h)
print(f"  Phase G test accuracy: {test_acc * 100:.2f}% ({test_correct}/{len(y_test)})")

# Evaluate on golden set
print("\n[7] Evaluating on golden set...")
import csv
golden_rows = []
with open(GOLDEN_SET_CSV, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        golden_rows.append(row)

golden_texts = [r['customer_text'] for r in golden_rows]
golden_labels = [r['human_label'] for r in golden_rows]

X_golden_word = vec_word.transform(golden_texts)
X_golden_char = vec_char.transform(golden_texts)
X_golden = hstack([X_golden_word, X_golden_char])
y_pred_golden = clf.predict(X_golden)

golden_correct = sum(1 for p, h in zip(y_pred_golden, golden_labels) if p == h)
golden_acc = golden_correct / len(y_pred_golden) * 100
print(f"  Phase G golden-set accuracy: {golden_acc:.2f}% ({golden_correct}/{len(y_pred_golden)})")

# Save predictions
print("\n[8] Saving predictions...")
predictions = []
for i, row in enumerate(golden_rows):
    predictions.append({
        'example_id': row['example_id'],
        'customer_text': row['customer_text'],
        'human_label': golden_labels[i],
        'phase_g_prediction': y_pred_golden[i],
        'correct': y_pred_golden[i] == golden_labels[i]
    })

with open('data/evaluation/phaseG_predictions.jsonl', 'w', encoding='utf-8') as f:
    for pred in predictions:
        f.write(json.dumps(pred, ensure_ascii=False) + '\n')

print("  Predictions saved to: data/evaluation/phaseG_predictions.jsonl")

# Compare with Phase C
print("\n" + "=" * 70)
print("PHASE G RESULTS")
print("=" * 70)

# Load Phase C for comparison
with open('data/baseline/phaseC_model.joblib', 'rb') as f:
    pc_model = pickle.load(f)

pc_vec_word = pc_model['vectorizer_word']
pc_vec_char = pc_model['vectorizer_char']
pc_clf = pc_model['classifier']

# Phase C on test
X_test_pc_word = pc_vec_word.transform(X_test)
X_test_pc_char = pc_vec_char.transform(X_test)
X_test_pc = hstack([X_test_pc_word, X_test_pc_char])
y_pred_pc_test = pc_clf.predict(X_test_pc)
pc_test_correct = sum(1 for p, h in zip(y_pred_pc_test, y_test) if p == h)
pc_test_acc = pc_test_correct / len(y_test) * 100

# Phase C on golden
X_golden_pc_word = pc_vec_word.transform(golden_texts)
X_golden_pc_char = pc_vec_char.transform(golden_texts)
X_golden_pc = hstack([X_golden_pc_word, X_golden_pc_char])
y_pred_pc_golden = pc_clf.predict(X_golden_pc)
pc_golden_correct = sum(1 for p, h in zip(y_pred_pc_golden, golden_labels) if p == h)
pc_golden_acc = pc_golden_correct / len(y_pred_golden) * 100

print(f"\nComparison:")
print(f"  Phase C test:  {pc_test_acc:.2f}% ({pc_test_correct}/540)")
print(f"  Phase G test:  {test_acc*100:.2f}% ({test_correct}/{len(y_test)})")
print(f"  Difference:   {test_acc*100 - pc_test_acc:+.2f} percentage points")
print()
print(f"  Phase C golden: {pc_golden_acc:.2f}% ({pc_golden_correct}/220)")
print(f"  Phase G golden: {golden_acc:.2f}% ({golden_correct}/220)")
print(f"  Difference:    {golden_acc - pc_golden_acc:+.2f} percentage points")

# Save comparison
comparison = {
    'phase': 'G',
    'augmentation': {
        'added': 40,
        'cancellation': 20,
        'order_modify': 20
    },
    'training_size': {
        'original': 2160,
        'experimental': 2200
    },
    'phase_c': {
        'test_accuracy': pc_test_acc,
        'test_correct': pc_test_correct,
        'test_total': len(y_test),
        'golden_accuracy': pc_golden_acc,
        'golden_correct': pc_golden_correct,
        'golden_total': len(golden_labels)
    },
    'phase_g': {
        'test_accuracy': test_acc * 100,
        'test_correct': test_correct,
        'test_total': len(y_test),
        'golden_accuracy': golden_acc,
        'golden_correct': golden_correct,
        'golden_total': len(golden_labels)
    },
    'difference': {
        'test': test_acc * 100 - pc_test_acc,
        'golden': golden_acc - pc_golden_acc
    }
}

with open('data/evaluation/phaseG_comparison.json', 'w', encoding='utf-8') as f:
    json.dump(comparison, f, indent=2)

print("\nComparison saved to: data/evaluation/phaseG_comparison.json")
print("=" * 70)
