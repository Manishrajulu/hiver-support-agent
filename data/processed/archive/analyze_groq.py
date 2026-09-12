#!/usr/bin/env python3
"""
Compare Groq LLM vs TF-IDF + Logistic Regression on the same 540 test conversations.
"""

import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Load Groq predictions
groq_predictions = {}
with open('data/evaluation/groq_test_predictions.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        rec = json.loads(line)
        groq_predictions[rec['conversation_id']] = rec['groq_predicted_intent']

print(f"Loaded {len(groq_predictions)} Groq predictions")

# Load baseline predictions
baseline_predictions = {}
with open('data/baseline/baseline_predictions.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        rec = json.loads(line)
        baseline_predictions[rec['conversation_id']] = rec['predicted']

print(f"Loaded {len(baseline_predictions)} baseline predictions")

# Load ground truth
with open('data/baseline/baseline_train_test_split.json', 'r') as f:
    split = json.load(f)
test_ids = split['test_ids']

# Build ground truth from conversations
ground_truth = {}
with open('data/processed/amazonhelp_labeled_conversations_v21.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        conv = json.loads(line)
        if conv['conversation_id'] in test_ids:
            ground_truth[conv['conversation_id']] = conv['primary_intent']

print(f"Loaded {len(ground_truth)} ground truth labels")

# Verify alignment
for cid in test_ids:
    if cid not in groq_predictions:
        print(f"ERROR: Missing Groq prediction for {cid}")
    if cid not in baseline_predictions:
        print(f"ERROR: Missing baseline prediction for {cid}")
    if cid not in ground_truth:
        print(f"ERROR: Missing ground truth for {cid}")

print("\nVerification complete - all IDs aligned")

# Calculate metrics
def calculate_metrics(y_true, y_pred, model_name):
    intents = sorted(set(y_true))

    # Per-intent metrics
    per_intent = {}
    for intent in intents:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == intent and p == intent)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != intent and p == intent)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == intent and p != intent)
        support = sum(1 for t in y_true if t == intent)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        per_intent[intent] = {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'support': support
        }

    # Macro metrics
    macro_precision = sum(p['precision'] for p in per_intent.values()) / len(per_intent)
    macro_recall = sum(p['recall'] for p in per_intent.values()) / len(per_intent)
    macro_f1 = sum(p['f1'] for p in per_intent.values()) / len(per_intent)

    # Weighted metrics
    total_support = sum(p['support'] for p in per_intent.values())
    weighted_precision = sum(p['precision'] * p['support'] for p in per_intent.values()) / total_support
    weighted_recall = sum(p['recall'] * p['support'] for p in per_intent.values()) / total_support
    weighted_f1 = sum(p['f1'] * p['support'] for p in per_intent.values()) / total_support

    # Accuracy
    accuracy = sum(1 for t, p in zip(y_true, y_pred) if t == p) / len(y_true)

    # Confusion pairs
    confusion = {}
    for t, p in zip(y_true, y_pred):
        if t != p:
            pair = f"{t} -> {p}"
            confusion[pair] = confusion.get(pair, 0) + 1

    return {
        'accuracy': accuracy,
        'macro_precision': macro_precision,
        'macro_recall': macro_recall,
        'macro_f1': macro_f1,
        'weighted_precision': weighted_precision,
        'weighted_recall': weighted_recall,
        'weighted_f1': weighted_f1,
        'per_intent': per_intent,
        'confusion': confusion
    }

# Build aligned arrays
y_true = []
y_groq = []
y_baseline = []

for cid in test_ids:
    y_true.append(ground_truth[cid])
    y_groq.append(groq_predictions[cid])
    y_baseline.append(baseline_predictions[cid])

# Calculate metrics
groq_metrics = calculate_metrics(y_true, y_groq, 'Groq LLM')
baseline_metrics = calculate_metrics(y_true, y_baseline, 'TF-IDF + LR')

# Majority baseline
from collections import Counter
train_dist = Counter()
with open('data/processed/amazonhelp_labeled_conversations_v21.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        conv = json.loads(line)
        if conv['conversation_id'] in split['train_ids']:
            train_dist[conv['primary_intent']] += 1

majority_class = train_dist.most_common(1)[0][0]
y_majority = [majority_class] * len(y_true)
majority_metrics = calculate_metrics(y_true, y_majority, 'Majority')

# Print comparison
print("\n" + "=" * 70)
print("MODEL COMPARISON")
print("=" * 70)

print(f"\n{'Model':<30} {'Accuracy':<12} {'Macro F1':<12} {'Weighted F1':<12}")
print("-" * 70)
print(f"{'Majority Baseline':<30} {majority_metrics['accuracy']:<12.4f} {majority_metrics['macro_f1']:<12.4f} {majority_metrics['weighted_f1']:<12.4f}")
print(f"{'TF-IDF + Logistic Regression':<30} {baseline_metrics['accuracy']:<12.4f} {baseline_metrics['macro_f1']:<12.4f} {baseline_metrics['weighted_f1']:<12.4f}")
print(f"{'Groq LLM':<30} {groq_metrics['accuracy']:<12.4f} {groq_metrics['macro_f1']:<12.4f} {groq_metrics['weighted_f1']:<12.4f}")

# Improvement
print(f"\n{'Groq improvement over TF-IDF:':<30}")
print(f"  Accuracy: +{groq_metrics['accuracy'] - baseline_metrics['accuracy']:.4f}")
print(f"  Macro F1: +{groq_metrics['macro_f1'] - baseline_metrics['macro_f1']:.4f}")
print(f"  Weighted F1: +{groq_metrics['weighted_f1'] - baseline_metrics['weighted_f1']:.4f}")

# Per-intent comparison
print("\n" + "=" * 70)
print("PER-INTENT COMPARISON (F1 SCORES)")
print("=" * 70)
print(f"{'Intent':<20} {'Baseline':<12} {'Groq':<12} {'Diff':<12}")
print("-" * 70)

for intent in sorted(set(y_true)):
    b_f1 = baseline_metrics['per_intent'].get(intent, {}).get('f1', 0)
    g_f1 = groq_metrics['per_intent'].get(intent, {}).get('f1', 0)
    diff = g_f1 - b_f1
    diff_str = f"+{diff:.3f}" if diff >= 0 else f"{diff:.3f}"
    print(f"{intent:<20} {b_f1:<12.3f} {g_f1:<12.3f} {diff_str:<12}")

# Top confusions
print("\n" + "=" * 70)
print("TOP 10 GROQ CONFUSIONS")
print("=" * 70)
sorted_confusions = sorted(groq_metrics['confusion'].items(), key=lambda x: -x[1])[:10]
for pair, count in sorted_confusions:
    print(f"  {pair}: {count}")

print("\n" + "=" * 70)
print("TOP 10 BASELINE CONFUSIONS")
print("=" * 70)
sorted_baseline_confusions = sorted(baseline_metrics['confusion'].items(), key=lambda x: -x[1])[:10]
for pair, count in sorted_baseline_confusions:
    print(f"  {pair}: {count}")

# Save artifacts
output = {
    'groq_metrics': groq_metrics,
    'baseline_metrics': baseline_metrics,
    'majority_metrics': majority_metrics,
    'test_size': len(test_ids),
    'model': 'allam-2-7b'
}

# Save metrics
with open('data/evaluation/groq_test_metrics.json', 'w') as f:
    json.dump({
        'groq': {
            'accuracy': groq_metrics['accuracy'],
            'macro_precision': groq_metrics['macro_precision'],
            'macro_recall': groq_metrics['macro_recall'],
            'macro_f1': groq_metrics['macro_f1'],
            'weighted_f1': groq_metrics['weighted_f1']
        },
        'baseline': {
            'accuracy': baseline_metrics['accuracy'],
            'macro_precision': baseline_metrics['macro_precision'],
            'macro_recall': baseline_metrics['macro_recall'],
            'macro_f1': baseline_metrics['macro_f1'],
            'weighted_f1': baseline_metrics['weighted_f1']
        },
        'majority': {
            'accuracy': majority_metrics['accuracy'],
            'macro_f1': majority_metrics['macro_f1'],
            'weighted_f1': majority_metrics['weighted_f1']
        }
    }, f, indent=2)

print("\nSaved: data/evaluation/groq_test_metrics.json")

# Save Groq confusion matrix
with open('data/evaluation/groq_test_confusion_matrix.json', 'w') as f:
    json.dump({
        'groq_confusions': dict(sorted_confusions[:20]),
        'baseline_confusions': dict(sorted_baseline_confusions[:20])
    }, f, indent=2)

print("Saved: data/evaluation/groq_test_confusion_matrix.json")

# Save comparison
with open('data/evaluation/groq_vs_baseline_comparison.json', 'w') as f:
    json.dump({
        'test_size': len(test_ids),
        'comparison': {
            'majority_baseline': majority_metrics,
            'tfidf_lr': baseline_metrics,
            'groq_llm': groq_metrics
        },
        'improvement': {
            'accuracy_delta': groq_metrics['accuracy'] - baseline_metrics['accuracy'],
            'macro_f1_delta': groq_metrics['macro_f1'] - baseline_metrics['macro_f1'],
            'weighted_f1_delta': groq_metrics['weighted_f1'] - baseline_metrics['weighted_f1']
        }
    }, f, indent=2, default=lambda x: float(x) if isinstance(x, (int, float)) and x != x else x)

print("Saved: data/evaluation/groq_vs_baseline_comparison.json")

# Save error analysis
error_examples = []
for i, cid in enumerate(test_ids):
    if y_true[i] != y_groq[i]:
        error_examples.append({
            'conversation_id': cid,
            'actual': y_true[i],
            'tfidf_predicted': y_baseline[i],
            'groq_predicted': y_groq[i]
        })

with open('data/evaluation/groq_vs_baseline_error_analysis.json', 'w') as f:
    json.dump({
        'total_errors': len(error_examples),
        'error_rate': len(error_examples) / len(test_ids),
        'errors': error_examples[:50]
    }, f, indent=2)

print("Saved: data/evaluation/groq_vs_baseline_error_analysis.json")

print("\n" + "=" * 70)
print("FINAL SUMMARY")
print("=" * 70)
print(f"\nTest conversations: {len(test_ids)}")
print(f"\nMAJORITY BASELINE:")
print(f"  Accuracy: {majority_metrics['accuracy']:.4f}")
print(f"  Macro F1: {majority_metrics['macro_f1']:.4f}")
print(f"\nTF-IDF + LOGISTIC REGRESSION:")
print(f"  Accuracy: {baseline_metrics['accuracy']:.4f}")
print(f"  Macro F1: {baseline_metrics['macro_f1']:.4f}")
print(f"  Weighted F1: {baseline_metrics['weighted_f1']:.4f}")
print(f"\nGROQ LLM:")
print(f"  Accuracy: {groq_metrics['accuracy']:.4f}")
print(f"  Macro F1: {groq_metrics['macro_f1']:.4f}")
print(f"  Weighted F1: {groq_metrics['weighted_f1']:.4f}")
print(f"\nGROQ IMPROVEMENT OVER TF-IDF:")
print(f"  Accuracy: +{groq_metrics['accuracy'] - baseline_metrics['accuracy']:.4f}")
print(f"  Macro F1: +{groq_metrics['macro_f1'] - baseline_metrics['macro_f1']:.4f}")
print(f"\nTOP GROQ CONFUSIONS:")
for pair, count in sorted_confusions[:5]:
    print(f"  {pair}: {count}")
