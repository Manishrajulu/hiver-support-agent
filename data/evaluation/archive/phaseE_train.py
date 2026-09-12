#!/usr/bin/env python3
"""
Phase E: Train and Evaluate Taxonomy-Cleaned Model
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
warnings.filterwarnings('ignore')

sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("PHASE E: TRAIN AND EVALUATE")
print("=" * 60)

# =============================================================================
# LOAD PHASE E DATASET
# =============================================================================
print("\n[1] Loading Phase E taxonomy-cleaned dataset...")
phaseE_path = "data/cleaned/phaseE_taxonomy_cleaned.jsonl"
data = []
with open(phaseE_path, 'r', encoding='utf-8') as f:
    for line in f:
        data.append(json.loads(line.strip()))
print(f"  Loaded {len(data)} examples")

with open("data/baseline/baseline_train_test_split.json", 'r') as f:
    split = json.load(f)
test_ids = set(split["test_ids"])
train_ids = set(split["train_ids"])

train_data = [item for item in data if item.get('conversation_id') in train_ids]
test_data = [item for item in data if item.get('conversation_id') in test_ids]
print(f"  Train: {len(train_data)}, Test: {len(test_data)}")

# =============================================================================
# TEXT PREPROCESSING
# =============================================================================
def get_customer_text(item):
    turns = item.get('turns', [])
    customer_texts = []
    for turn in turns:
        if turn.get('speaker') == 'Customer' or turn.get('inbound', '').lower() == 'true':
            text = turn.get('text', '').strip()
            if text:
                customer_texts.append(text)
    return ' '.join(customer_texts)

X_train = [get_customer_text(item) for item in train_data]
y_train = [item.get('primary_intent') for item in train_data]
X_test = [get_customer_text(item) for item in test_data]
y_test = [item.get('primary_intent') for item in test_data]

all_labels = sorted(set(y_train + y_test))
print(f"  Unique labels: {len(all_labels)}")
print(f"  Labels: {all_labels}")

# =============================================================================
# TRAIN PHASE E MODEL (same config as Phase C)
# =============================================================================
print("\n[2] Training Phase E model (TF-IDF + LinearSVC)...")

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
    max_features=8000,
    min_df=2,
    max_df=0.95,
    sublinear_tf=True,
    analyzer='char_wb'
)

print("  Fitting word vectorizer...")
X_train_word = vec_word.fit_transform(X_train)
print(f"    Word features: {X_train_word.shape[1]}")

print("  Fitting char vectorizer...")
X_train_char = vec_char.fit_transform(X_train)
print(f"    Char features: {X_train_char.shape[1]}")

X_train_combined = hstack([X_train_word, X_train_char])
print(f"  Combined train features: {X_train_combined.shape}")

X_test_word = vec_word.transform(X_test)
X_test_char = vec_char.transform(X_test)
X_test_combined = hstack([X_test_word, X_test_char])
print(f"  Combined test features: {X_test_combined.shape}")

print("  Training LinearSVC...")
clf = LinearSVC(C=5.0, class_weight='balanced', random_state=42, max_iter=10000)
clf.fit(X_train_combined, y_train)

# =============================================================================
# EVALUATE
# =============================================================================
print("\n[3] Evaluating on 540-example test set...")

y_pred = clf.predict(X_test_combined)

correct = sum(1 for p, t in zip(y_pred, y_test) if p == t)
accuracy = correct / len(y_test)
print(f"\n  Phase E Accuracy: {accuracy:.4f} ({correct}/{len(y_test)})")
print(f"  Phase C Accuracy: 0.7111 (384/540)")
print(f"  Delta: {(accuracy - 0.7111)*100:+.2f} percentage points")

# =============================================================================
# CONFUSION MATRIX
# =============================================================================
print("\n[4] Generating confusion matrix...")

cm = confusion_matrix(y_test, y_pred, labels=all_labels)

# Top confusion pairs
confusion_pairs = []
for i, true_label in enumerate(all_labels):
    for j, pred_label in enumerate(all_labels):
        if i != j and cm[i, j] > 0:
            confusion_pairs.append((true_label, pred_label, cm[i, j]))

confusion_pairs.sort(key=lambda x: -x[2])

print("\nTop 15 Confusion Pairs:")
for i, (true, pred, count) in enumerate(confusion_pairs[:15]):
    print(f"  {i+1}. {true} -> {pred}: {count}")

# =============================================================================
# CLASSIFICATION REPORT
# =============================================================================
print("\n[5] Classification Report:")
print(classification_report(y_test, y_pred, digits=4))

# =============================================================================
# SAVE PREDICTIONS
# =============================================================================
print("\n[6] Saving predictions...")

predictions = []
test_conversation_ids = [item.get('conversation_id') for item in test_data]
for cid, true_label, pred_label in zip(test_conversation_ids, y_test, y_pred):
    predictions.append({
        'conversation_id': cid,
        'true_label': true_label,
        'predicted_label': pred_label,
        'correct': true_label == pred_label
    })

with open("data/cleaned/phaseE_predictions.jsonl", 'w', encoding='utf-8') as f:
    for pred in predictions:
        f.write(json.dumps(pred, ensure_ascii=False) + '\n')

# Save model
phaseE_model = {
    'vectorizer_word': vec_word,
    'vectorizer_char': vec_char,
    'classifier': clf
}
with open("data/cleaned/phaseE_model.joblib", 'wb') as f:
    pickle.dump(phaseE_model, f)

# =============================================================================
# ERROR ANALYSIS
# =============================================================================
print("\n[7] Error Analysis...")

errors = [(cid, true, pred) for cid, true, pred in zip(test_conversation_ids, y_test, y_pred) if true != pred]
print(f"\nTotal errors: {len(errors)}")

# Categorize errors
ambiguous = 0
genuine_mistake = 0
low_example = 0
other = 0

# Get train counts
train_counts = {}
for label in all_labels:
    train_counts[label] = sum(1 for l in y_train if l == label)

# Key confusion pairs for ambiguous
key_pairs = [
    ('OTHER', 'DELIVERY_LATE'),
    ('OTHER', 'DELIVERY_MISSING'),
    ('APP_USAGE', 'DEVICE_ISSUE'),
    ('DELIVERY_LATE', 'DELIVERY_MISSING'),
    ('DELIVERY_LATE', 'DELIVERY_TRACKING'),
    ('ORDER_STATUS', 'DELIVERY_LATE'),
    ('ORDER_STATUS', 'DELIVERY_MISSING'),
]

low_threshold = 15  # Classes with <15 train examples considered "low"

for cid, true, pred in errors:
    is_low = train_counts.get(true, 0) < low_threshold

    # Check if it's an ambiguous boundary issue
    is_ambiguous = (true, pred) in key_pairs or (pred, true) in key_pairs

    if is_low:
        low_example += 1
    elif is_ambiguous:
        ambiguous += 1
    else:
        genuine_mistake += 1

print(f"\nError Categorization:")
print(f"  a) Ambiguous/overlapping taxonomy: {ambiguous} ({ambiguous*100/len(errors):.1f}%)")
print(f"  b) Genuine model mistakes: {genuine_mistake} ({genuine_mistake*100/len(errors):.1f}%)")
print(f"  c) Low-example classes: {low_example} ({low_example*100/len(errors):.1f}%)")
print(f"  d) Other: {other} ({other*100/len(errors):.1f}%)")

# Low example classes
print("\nLow-example classes (<15 train examples):")
for label, count in sorted(train_counts.items(), key=lambda x: x[1]):
    if count < 15:
        print(f"  {label}: {count} train examples")

# =============================================================================
# COMPARISON TO PHASE C
# =============================================================================
print("\n" + "=" * 60)
print("PHASE E RESULTS SUMMARY")
print("=" * 60)
print(f"  Original baseline:        54.44%")
print(f"  Phase 6 TF-IDF+LinearSVC: 70.56%")
print(f"  Phase C TF-IDF+LinearSVC: 71.11% (384/540)")
print(f"  Phase E (cleaned):         {accuracy*100:.2f}% ({correct}/540)")
print(f"  Delta vs Phase C:         {(accuracy - 0.7111)*100:+.2f}pp")
print("=" * 60)

# Save summary
summary = {
    'phaseE_accuracy': accuracy,
    'correct': correct,
    'total': 540,
    'delta_vs_phaseC': accuracy - 0.7111,
    'delta_vs_phase6': accuracy - 0.7056,
    'errors_total': len(errors),
    'errors_ambiguous': ambiguous,
    'errors_genuine_mistake': genuine_mistake,
    'errors_low_example': low_example,
    'errors_other': other,
    'train_counts': train_counts,
    'all_labels': all_labels,
    'confusion_pairs_top15': [(t, p, c) for t, p, c in confusion_pairs[:15]]
}

with open("data/cleaned/phaseE_summary.json", 'w') as f:
    json.dump(summary, f, indent=2)

print("\nPhase E training and evaluation complete!")
print("Results saved to data/cleaned/")