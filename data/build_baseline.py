#!/usr/bin/env python3
"""
Baseline Classification Model: Majority Class + TF-IDF + Logistic Regression
=========================================================================
For Hiver/AmazonHelp Intent Classification
"""

import json
import random
import sys
import numpy as np
from sklearn.model_selection import train_test_split

# Fix Unicode encoding on Windows
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix, balanced_accuracy_score
)
import joblib
import os

# Set random seed for reproducibility
RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)
random.seed(RANDOM_STATE)

# Paths
DATA_PATH = 'data/processed/amazonhelp_labeled_conversations_v21_phase6c.jsonl'
OUTPUT_DIR = 'data/baseline'

print("=" * 70)
print("BASELINE CLASSIFICATION MODEL")
print("=" * 70)

# ============================================================================
# A. DATA PREPARATION
# ============================================================================
print("\n[A] DATA PREPARATION")
print("-" * 40)

# Load conversations
conversations = []
with open(DATA_PATH, 'r', encoding='utf-8') as f:
    for line in f:
        conversations.append(json.loads(line))

print(f"Loaded {len(conversations)} conversations")

# Check for duplicates
conv_ids = [c['conversation_id'] for c in conversations]
unique_ids = set(conv_ids)
print(f"Unique IDs: {len(unique_ids)}")
assert len(conv_ids) == len(unique_ids), "Duplicate IDs found!"
print("No duplicate IDs: PASS")

# Check for missing primary_intent
missing = [c['conversation_id'] for c in conversations if not c.get('primary_intent')]
print(f"Missing primary_intent: {len(missing)}")
assert len(missing) == 0, f"Missing labels for: {missing[:5]}"
print("No missing labels: PASS")

# Convert to text representation (customer text only)
def get_customer_text(conv):
    """Extract customer text from conversation."""
    texts = []
    for turn in conv.get('turns', []):
        if turn.get('speaker') == 'Customer':
            texts.append(turn.get('text', ''))
    return ' '.join(texts)

# Prepare data
X_text = [get_customer_text(c) for c in conversations]
y = [c['primary_intent'] for c in conversations]
conv_ids_list = [c['conversation_id'] for c in conversations]

print(f"\nText representation: Customer text only")
print(f"Number of samples: {len(X_text)}")

# Label distribution
label_dist = {}
for label in y:
    label_dist[label] = label_dist.get(label, 0) + 1

print("\nLabel Distribution (before split):")
print("-" * 40)
for label, count in sorted(label_dist.items(), key=lambda x: -x[1]):
    pct = 100 * count / len(y)
    print(f"  {label:<20}: {count:>4} ({pct:>5.1f}%)")

# ============================================================================
# B. TRAIN/TEST SPLIT
# ============================================================================
print("\n[B] TRAIN/TEST SPLIT")
print("-" * 40)

X_train_text, X_test_text, y_train, y_test, ids_train, ids_test = train_test_split(
    X_text, y, conv_ids_list,
    test_size=0.2,
    stratify=y,
    random_state=RANDOM_STATE
)

print(f"Training set: {len(X_train_text)} samples")
print(f"Test set: {len(X_test_text)} samples")
print(f"Total: {len(X_train_text) + len(X_test_text)}")
assert len(X_train_text) + len(X_test_text) == 2700, "Split doesn't add up!"
print("Train + Test = 2700: PASS")

# Verify no overlap
overlap = set(ids_train) & set(ids_test)
assert len(overlap) == 0, f"Train/test overlap found: {overlap}"
print("No train/test overlap: PASS")

# ============================================================================
# C. MAJORITY-CLASS BASELINE
# ============================================================================
print("\n[C] MAJORITY-CLASS BASELINE")
print("-" * 40)

# Find majority class in training set
from collections import Counter
train_dist = Counter(y_train)
majority_class = train_dist.most_common(1)[0][0]
majority_count = train_dist.most_common(1)[0][1]
print(f"Majority class: {majority_class}")
print(f"Majority class count in train: {majority_count}")

# Predict majority class for all test samples
y_pred_majority = [majority_class] * len(y_test)

# Evaluate
majority_accuracy = accuracy_score(y_test, y_pred_majority)
majority_macro_precision = precision_score(y_test, y_pred_majority, average='macro', zero_division=0)
majority_macro_recall = recall_score(y_test, y_pred_majority, average='macro', zero_division=0)
majority_macro_f1 = f1_score(y_test, y_pred_majority, average='macro', zero_division=0)
majority_weighted_f1 = f1_score(y_test, y_pred_majority, average='weighted', zero_division=0)

print(f"\nMajority Baseline Results:")
print(f"  Accuracy:           {majority_accuracy:.4f}")
print(f"  Macro Precision:    {majority_macro_precision:.4f}")
print(f"  Macro Recall:       {majority_macro_recall:.4f}")
print(f"  Macro F1:           {majority_macro_f1:.4f}")
print(f"  Weighted F1:        {majority_weighted_f1:.4f}")

# ============================================================================
# D. TF-IDF + LOGISTIC REGRESSION
# ============================================================================
print("\n[D] TF-IDF + LOGISTIC REGRESSION")
print("-" * 40)

# Create pipeline
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

print("Pipeline Configuration:")
print("  TfidfVectorizer:")
print("    max_features=10000")
print("    ngram_range=(1, 2)")
print("    min_df=2, max_df=0.95")
print("    sublinear_tf=True")
print("  LogisticRegression:")
print("    C=1.0")
print("    class_weight='balanced'")
print("    solver='lbfgs', multi_class='multinomial'")

# Fit ONLY on training data
print("\nFitting on training data only...")
pipeline.fit(X_train_text, y_train)
print("Fitting complete: PASS")
print("  TF-IDF fitted on training: PASS")
print("  LogisticRegression fitted on training: PASS")

# ============================================================================
# E. EVALUATION
# ============================================================================
print("\n[E] EVALUATION ON TEST SET")
print("-" * 40)

# Predictions
y_pred = pipeline.predict(X_test_text)

# Metrics
accuracy = accuracy_score(y_test, y_pred)
macro_precision = precision_score(y_test, y_pred, average='macro', zero_division=0)
macro_recall = recall_score(y_test, y_pred, average='macro', zero_division=0)
macro_f1 = f1_score(y_test, y_pred, average='macro', zero_division=0)
weighted_f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
balanced_acc = balanced_accuracy_score(y_test, y_pred)

print(f"\nTF-IDF + Logistic Regression Results:")
print(f"  Accuracy:           {accuracy:.4f}")
print(f"  Balanced Accuracy:  {balanced_acc:.4f}")
print(f"  Macro Precision:    {macro_precision:.4f}")
print(f"  Macro Recall:       {macro_recall:.4f}")
print(f"  Macro F1:           {macro_f1:.4f}")
print(f"  Weighted F1:        {weighted_f1:.4f}")

# Per-intent report
print("\nPer-Intent Performance:")
print("-" * 70)
intents = sorted(set(y_test))
report_lines = []
for intent in intents:
    report_lines.append(classification_report(
        [y for y in y_test if y == intent] + [y for y in y_test if y != intent],
        [y for y in y_pred if y == intent] + [y for y in y_pred if y != intent],
        labels=[intent],
        zero_division=0
    ))

# Simpler per-intent calculation
print(f"{'Intent':<20} {'Precision':>10} {'Recall':>10} {'F1':>10} {'Support':>10}")
print("-" * 60)
per_intent_metrics = {}
for intent in intents:
    # True positives, false positives, false negatives for this intent
    tp = sum(1 for yt, yp in zip(y_test, y_pred) if yt == intent and yp == intent)
    fp = sum(1 for yt, yp in zip(y_test, y_pred) if yt != intent and yp == intent)
    fn = sum(1 for yt, yp in zip(y_test, y_pred) if yt == intent and yp != intent)
    support = sum(1 for yt in y_test if yt == intent)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    per_intent_metrics[intent] = {
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'support': support
    }
    print(f"{intent:<20} {precision:>10.4f} {recall:>10.4f} {f1:>10.4f} {support:>10}")

# Confusion matrix
print("\nConfusion Matrix (rows=actual, cols=predicted):")
cm = confusion_matrix(y_test, y_pred, labels=intents)
print(f"{'':>20}", end='')
for intent in intents[:5]:
    print(f"{intent[:10]:>12}", end='')
print()
for i, intent in enumerate(intents[:10]):
    print(f"{intent[:20]:<20}", end='')
    for j in range(min(5, len(intents))):
        print(f"{cm[i][j]:>12}", end='')
    print()

# ============================================================================
# F. ERROR ANALYSIS
# ============================================================================
print("\n[F] ERROR ANALYSIS")
print("-" * 40)

# Find misclassifications
errors = []
for i in range(len(y_test)):
    if y_test[i] != y_pred[i]:
        errors.append({
            'conversation_id': ids_test[i],
            'actual': y_test[i],
            'predicted': y_pred[i],
            'text': X_test_text[i][:200] + '...' if len(X_test_text[i]) > 200 else X_test_text[i]
        })

print(f"Total errors: {len(errors)}")
print(f"Error rate: {100 * len(errors) / len(y_test):.1f}%")

# Most common confusion pairs
confusion_pairs = {}
for e in errors:
    pair = f"{e['actual']} -> {e['predicted']}"
    confusion_pairs[pair] = confusion_pairs.get(pair, 0) + 1

print("\nTop 10 Confusion Pairs:")
sorted_confusions = sorted(confusion_pairs.items(), key=lambda x: -x[1])[:10]
for pair, count in sorted_confusions:
    print(f"  {pair}: {count}")

# Representative examples for top 5 confusions
error_examples = {}
for pair, _ in sorted_confusions[:5]:
    actual, predicted = pair.split(' -> ')
    examples = [e for e in errors if e['actual'] == actual and e['predicted'] == predicted][:2]
    error_examples[pair] = examples

print("\nRepresentative Error Examples (first 3 pairs):")
count = 0
for pair, exs in error_examples.items():
    if count >= 3:
        break
    print(f"\n  {pair}:")
    for ex in exs:
        text = ex['text'][:80].replace('\n', ' ').replace('\r', '')
        print(f"    ID: {ex['conversation_id']}")
        print(f"    Text: {text}...")

# ============================================================================
# G. SAVE ARTIFACTS
# ============================================================================
print("\n[G] SAVING ARTIFACTS")
print("-" * 40)

# 1. Save model
model_path = os.path.join(OUTPUT_DIR, 'baseline_model.joblib')
joblib.dump(pipeline, model_path)
print(f"  Saved: {model_path}")

# 2. Save metrics
metrics = {
    'majority_baseline': {
        'accuracy': majority_accuracy,
        'macro_precision': majority_macro_precision,
        'macro_recall': majority_macro_recall,
        'macro_f1': majority_macro_f1,
        'weighted_f1': majority_weighted_f1,
        'majority_class': majority_class
    },
    'tfidf_lr': {
        'accuracy': accuracy,
        'balanced_accuracy': balanced_acc,
        'macro_precision': macro_precision,
        'macro_recall': macro_recall,
        'macro_f1': macro_f1,
        'weighted_f1': weighted_f1
    }
}
metrics_path = os.path.join(OUTPUT_DIR, 'baseline_metrics.json')
with open(metrics_path, 'w') as f:
    json.dump(metrics, f, indent=2)
print(f"  Saved: {metrics_path}")

# 3. Save classification report
class_report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
class_report_path = os.path.join(OUTPUT_DIR, 'baseline_classification_report.json')
with open(class_report_path, 'w') as f:
    json.dump(class_report, f, indent=2)
print(f"  Saved: {class_report_path}")

# 4. Save confusion matrix
cm_data = {
    'intents': intents,
    'matrix': cm.tolist()
}
cm_path = os.path.join(OUTPUT_DIR, 'baseline_confusion_matrix.json')
with open(cm_path, 'w') as f:
    json.dump(cm_data, f, indent=2)
print(f"  Saved: {cm_path}")

# 5. Save predictions
predictions = []
for i in range(len(y_test)):
    predictions.append({
        'conversation_id': ids_test[i],
        'actual': y_test[i],
        'predicted': y_pred[i],
        'correct': y_test[i] == y_pred[i]
    })
pred_path = os.path.join(OUTPUT_DIR, 'baseline_predictions.jsonl')
with open(pred_path, 'w', encoding='utf-8') as f:
    for p in predictions:
        f.write(json.dumps(p, ensure_ascii=False) + '\n')
print(f"  Saved: {pred_path}")

# 6. Save error analysis
error_analysis = {
    'total_errors': len(errors),
    'error_rate': len(errors) / len(y_test),
    'top_confusion_pairs': sorted_confusions[:20],
    'error_examples': errors[:50]  # First 50 errors
}
error_path = os.path.join(OUTPUT_DIR, 'baseline_error_analysis.json')
with open(error_path, 'w', encoding='utf-8') as f:
    json.dump(error_analysis, f, indent=2, ensure_ascii=False)
print(f"  Saved: {error_path}")

# 7. Save train/test IDs for reproducibility
split_data = {
    'train_ids': ids_train,
    'test_ids': ids_test,
    'random_state': RANDOM_STATE,
    'test_size': 0.2
}
split_path = os.path.join(OUTPUT_DIR, 'baseline_train_test_split.json')
with open(split_path, 'w') as f:
    json.dump(split_data, f)
print(f"  Saved: {split_path}")

# ============================================================================
# H. FINAL SUMMARY
# ============================================================================
print("\n" + "=" * 70)
print("FINAL SUMMARY")
print("=" * 70)
print(f"\nDATASET")
print(f"  Total conversations: 2700")
print(f"  Training: {len(X_train_text)}")
print(f"  Test: {len(X_test_text)}")
print(f"  Number of intents: {len(intents)}")

print(f"\nMAJORITY BASELINE:")
print(f"  Majority class: {majority_class}")
print(f"  Accuracy: {majority_accuracy:.4f}")
print(f"  Macro F1: {majority_macro_f1:.4f}")

print(f"\nTF-IDF + LOGISTIC REGRESSION:")
print(f"  Accuracy: {accuracy:.4f}")
print(f"  Macro F1: {macro_f1:.4f}")
print(f"  Weighted F1: {weighted_f1:.4f}")

print(f"\nTOP CONFUSIONS:")
for pair, count in sorted_confusions[:5]:
    print(f"  {pair}: {count}")

print(f"\nFILES CREATED:")
files = ['baseline_model.joblib', 'baseline_metrics.json',
         'baseline_classification_report.json', 'baseline_confusion_matrix.json',
         'baseline_predictions.jsonl', 'baseline_error_analysis.json',
         'baseline_train_test_split.json']
for f in files:
    print(f"  {OUTPUT_DIR}/{f}")

print("\n" + "=" * 70)
print("BASELINE COMPLETE")
print("=" * 70)
