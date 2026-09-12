#!/usr/bin/env python3
"""
Retrain baseline classifier with cleaned data.
Uses existing train/test split for fair comparison.
"""

import json
import sys
import numpy as np
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report, confusion_matrix, balanced_accuracy_score
import joblib
import os

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

print("="*70)
print("RETRAINING BASELINE WITH CLEANED DATA")
print("Using existing train/test split IDs for fair comparison")
print("="*70)

# ============================================================================
# A. LOAD EXISTING TRAIN/TEST SPLIT
# ============================================================================
print("\n[A] LOADING EXISTING TRAIN/TEST SPLIT")
print("-"*40)

with open('data/baseline/baseline_train_test_split.json', 'r') as f:
    split_data = json.load(f)

train_ids = set(split_data['train_ids'])
test_ids = set(split_data['test_ids'])

print(f"Train IDs: {len(train_ids)}")
print(f"Test IDs: {len(test_ids)}")

# ============================================================================
# B. LOAD CLEANED DATASET
# ============================================================================
print("\n[B] LOADING CLEANED DATASET")
print("-"*40)

conversations = []
cid_to_data = {}
with open('data/processed/amazonhelp_labeled_conversations_v21.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line)
        conversations.append(data)
        cid_to_data[data['conversation_id']] = data

print(f"Loaded {len(conversations)} conversations")

# Check for duplicates
conv_ids = [c['conversation_id'] for c in conversations]
unique_ids = set(conv_ids)
assert len(conv_ids) == len(unique_ids), "Duplicate IDs found!"
print("No duplicate IDs: PASS")

# ============================================================================
# C. PREPARE TRAIN/TEST DATA
# ============================================================================
print("\n[C] PREPARING TRAIN/TEST DATA")
print("-"*40)

def get_customer_text(conv):
    texts = []
    for turn in conv.get('turns', []):
        if turn.get('speaker') == 'Customer':
            texts.append(turn.get('text', ''))
    return ' '.join(texts)

X_train_text = []
y_train = []
ids_train = []

X_test_text = []
y_test = []
ids_test = []

for conv in conversations:
    cid = conv['conversation_id']
    text = get_customer_text(conv)
    label = conv['primary_intent']

    if cid in train_ids:
        X_train_text.append(text)
        y_train.append(label)
        ids_train.append(cid)
    elif cid in test_ids:
        X_test_text.append(text)
        y_test.append(label)
        ids_test.append(cid)

print(f"Training set: {len(X_train_text)} samples")
print(f"Test set: {len(X_test_text)} samples")

# Verify split
print(f"Total: {len(X_train_text) + len(X_test_text)}")

# Label distribution
print("\nTraining label distribution:")
train_dist = Counter(y_train)
for label, count in sorted(train_dist.items(), key=lambda x: -x[1]):
    pct = 100 * count / len(y_train)
    print(f"  {label:<25}: {count:>4} ({pct:>5.1f}%)")

print("\nTest label distribution:")
test_dist = Counter(y_test)
for label, count in sorted(test_dist.items(), key=lambda x: -x[1]):
    pct = 100 * count / len(y_test)
    print(f"  {label:<25}: {count:>4} ({pct:>5.1f}%)")

# ============================================================================
# D. TRAIN MODEL
# ============================================================================
print("\n[D] TRAINING TF-IDF + LOGISTIC REGRESSION")
print("-"*40)

pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(
        max_features=10000,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.95,
        sublinear_tf=True
    )),
    ('clf', LogisticRegression(
        C=1.0,
        max_iter=1000,
        class_weight='balanced',
        random_state=RANDOM_STATE,
        solver='lbfgs'
    ))
])

print("Fitting on training data...")
pipeline.fit(X_train_text, y_train)
print("Fitting complete: PASS")

# ============================================================================
# E. EVALUATE
# ============================================================================
print("\n[E] EVALUATION ON TEST SET")
print("-"*40)

y_pred = pipeline.predict(X_test_text)

accuracy = accuracy_score(y_test, y_pred)
balanced_acc = balanced_accuracy_score(y_test, y_pred)
macro_precision = precision_score(y_test, y_pred, average='macro', zero_division=0)
macro_recall = recall_score(y_test, y_pred, average='macro', zero_division=0)
macro_f1 = f1_score(y_test, y_pred, average='macro', zero_division=0)
weighted_f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)

print("\nResults:")
print(f"  Accuracy:           {accuracy:.4f} ({accuracy*100:.2f}%)")
print(f"  Balanced Accuracy:  {balanced_acc:.4f}")
print(f"  Macro Precision:    {macro_precision:.4f}")
print(f"  Macro Recall:       {macro_recall:.4f}")
print(f"  Macro F1:           {macro_f1:.4f}")
print(f"  Weighted F1:        {weighted_f1:.4f}")

# Per-intent metrics
intents = sorted(set(y_test))
print(f"\n{'Intent':<25} {'Precision':>10} {'Recall':>10} {'F1':>10} {'Support':>10}")
print("-"*65)
per_intent_metrics = {}
for intent in intents:
    tp = sum(1 for yt, yp in zip(y_test, y_pred) if yt == intent and yp == intent)
    fp = sum(1 for yt, yp in zip(y_test, y_pred) if yt != intent and yp == intent)
    fn = sum(1 for yt, yp in zip(y_test, y_pred) if yt == intent and yp != intent)
    support = sum(1 for yt in y_test if yt == intent)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    per_intent_metrics[intent] = {'precision': precision, 'recall': recall, 'f1': f1, 'support': support}
    print(f"{intent:<25} {precision:>10.4f} {recall:>10.4f} {f1:>10.4f} {support:>10}")

# ============================================================================
# F. ERROR ANALYSIS
# ============================================================================
print("\n[F] ERROR ANALYSIS")
print("-"*40)

errors = []
for i in range(len(y_test)):
    if y_test[i] != y_pred[i]:
        errors.append({
            'conversation_id': ids_test[i],
            'actual': y_test[i],
            'predicted': y_pred[i],
            'text': X_test_text[i][:200]
        })

print(f"Total errors: {len(errors)}")
print(f"Error rate: {100 * len(errors) / len(y_test):.1f}%")

# Confusion pairs
confusion_pairs = {}
for e in errors:
    pair = f"{e['actual']} -> {e['predicted']}"
    confusion_pairs[pair] = confusion_pairs.get(pair, 0) + 1

sorted_confusions = sorted(confusion_pairs.items(), key=lambda x: -x[1])
print("\nTop 10 Confusion Pairs:")
for pair, count in sorted_confusions[:10]:
    print(f"  {pair}: {count}")

# ============================================================================
# G. SAVE MODEL
# ============================================================================
print("\n[G] SAVING MODEL")
print("-"*40)

model_path = 'data/baseline/baseline_model.joblib'
joblib.dump(pipeline, model_path)
print(f"Saved: {model_path}")

# Save metrics
metrics = {
    'accuracy': accuracy,
    'balanced_accuracy': balanced_acc,
    'macro_precision': macro_precision,
    'macro_recall': macro_recall,
    'macro_f1': macro_f1,
    'weighted_f1': weighted_f1,
    'total_errors': len(errors),
    'error_rate': len(errors) / len(y_test)
}
with open('data/baseline/baseline_metrics.json', 'w') as f:
    json.dump(metrics, f, indent=2)
print(f"Saved: data/baseline/baseline_metrics.json")

# Save error analysis
error_analysis = {
    'total_errors': len(errors),
    'error_rate': len(errors) / len(y_test),
    'top_confusion_pairs': sorted_confusions[:20],
    'error_examples': errors[:50]
}
with open('data/baseline/baseline_error_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(error_analysis, f, indent=2, ensure_ascii=False)
print(f"Saved: data/baseline/baseline_error_analysis.json")

# Save predictions
predictions = []
for i in range(len(y_test)):
    predictions.append({
        'conversation_id': ids_test[i],
        'actual': y_test[i],
        'predicted': y_pred[i],
        'correct': y_test[i] == y_pred[i]
    })
with open('data/baseline/baseline_predictions.jsonl', 'w', encoding='utf-8') as f:
    for p in predictions:
        f.write(json.dumps(p, ensure_ascii=False) + '\n')
print(f"Saved: data/baseline/baseline_predictions.jsonl")

# Save classification report
class_report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
with open('data/baseline/baseline_classification_report.json', 'w') as f:
    json.dump(class_report, f, indent=2)
print(f"Saved: data/baseline/baseline_classification_report.json")

print("\n" + "="*70)
print("RETRAINING COMPLETE")
print("="*70)
print(f"\nNew accuracy: {accuracy*100:.2f}% ({int(accuracy*len(y_test))}/{len(y_test)})")
print(f"Old accuracy: 72.86% (51/70)")