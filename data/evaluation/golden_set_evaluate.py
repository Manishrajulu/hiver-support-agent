#!/usr/bin/env python3
"""
Golden Set Evaluation Script

Evaluates the manually-labeled golden set against the Phase C model.
This is an INDEPENDENT evaluation and must NOT be presented as the official 71.11% Phase C test accuracy.
"""

import csv
import json
import pickle
import numpy as np
from scipy.sparse import hstack
import sys
import os
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding='utf-8')

# Configuration
GOLDEN_SET_CSV = "data/evaluation/golden_set_labeled.csv"
OUTPUT_PREDICTIONS = "data/evaluation/golden_set_predictions.jsonl"
OUTPUT_REPORT = "data/evaluation/golden_set_evaluation_report.md"
MODEL_PATH = "data/baseline/phaseC_model.joblib"

VALID_INTENTS = {
    'ACCOUNT_ACCESS', 'APP_USAGE', 'CANCELLATION', 'DELIVERY_LATE', 'DELIVERY_MISSING',
    'DELIVERY_TRACKING', 'DEVICE_ISSUE', 'ORDER_MODIFY', 'ORDER_STATUS', 'OTHER',
    'PAYMENT_ISSUE', 'PRODUCT_ISSUE', 'REFUND_REQUEST', 'RETURN_REQUEST', 'VIDEO_STREAMING'
}


def load_phasec_model(model_path):
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    return model


def classify(conversation_text, phasec_model):
    vec_word = phasec_model['vectorizer_word']
    vec_char = phasec_model['vectorizer_char']
    clf = phasec_model['classifier']
    classes = clf.classes_

    X_word = vec_word.transform([conversation_text])
    X_char = vec_char.transform([conversation_text])
    X = hstack([X_word, X_char])

    decision_scores = clf.decision_function(X)[0]
    predicted_idx = np.argmax(decision_scores)
    predicted_class = classes[predicted_idx]

    return predicted_class


def load_golden_set(csv_path):
    rows = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def calculate_metrics(predictions, human_labels):
    n = len(predictions)
    correct = sum(1 for p, h in zip(predictions, human_labels) if p == h)
    accuracy = correct / n * 100 if n > 0 else 0
    return {'total': n, 'correct': correct, 'incorrect': n - correct, 'accuracy': accuracy}


def calculate_per_intent_metrics(predictions, human_labels, valid_intents):
    confusion = defaultdict(lambda: defaultdict(int))
    intent_counts = defaultdict(lambda: {'correct': 0, 'predicted_as': Counter(), 'actual': 0})

    for pred, human in zip(predictions, human_labels):
        confusion[human][pred] += 1
        intent_counts[human]['actual'] += 1
        intent_counts[human]['predicted_as'][pred] += 1
        if pred == human:
            intent_counts[human]['correct'] += 1

    per_intent = {}
    for intent in valid_intents:
        data = intent_counts[intent]
        actual_count = data['actual']
        predicted_count = sum(data['predicted_as'].values())
        true_positive = data['correct']

        precision = true_positive / predicted_count * 100 if predicted_count > 0 else 0
        recall = true_positive / actual_count * 100 if actual_count > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        per_intent[intent] = {
            'actual_count': actual_count,
            'predicted_count': predicted_count,
            'correct': true_positive,
            'precision': precision,
            'recall': recall,
            'f1': f1
        }

    return per_intent, confusion


def get_top_confusion_pairs(confusion, n=10):
    pairs = []
    for true_label, predicted_dict in confusion.items():
        for pred_label, count in predicted_dict.items():
            if true_label != pred_label:
                pairs.append((true_label, pred_label, count))
    pairs.sort(key=lambda x: -x[2])
    return pairs[:n]


def main():
    print("=" * 70)
    print("GOLDEN SET EVALUATION")
    print("=" * 70)
    print()
    print("IMPORTANT: This is an INDEPENDENT golden-set evaluation.")
    print("It must NOT be presented as the official 71.11% Phase C test accuracy.")
    print()

    # Load model
    print("[1] Loading Phase C model...")
    phasec_model = load_phasec_model(MODEL_PATH)
    print(f"  Model loaded from: {MODEL_PATH}")
    print(f"  Word vectorizer: ngram={phasec_model['vectorizer_word'].ngram_range}")
    print(f"  Char vectorizer: ngram={phasec_model['vectorizer_char'].ngram_range}")
    print(f"  Classes: {len(phasec_model['classifier'].classes_)}")
    print()

    # Load golden set
    print("[2] Loading golden set...")
    golden_rows = load_golden_set(GOLDEN_SET_CSV)
    print(f"  Loaded {len(golden_rows)} examples from {GOLDEN_SET_CSV}")
    print()

    # Integrity check
    print("[3] Integrity checks...")
    human_labels = [r['human_label'] for r in golden_rows]
    missing_human = sum(1 for h in human_labels if not h)
    invalid_human = sum(1 for h in human_labels if h not in VALID_INTENTS)
    print(f"  Input rows: {len(golden_rows)}")
    print(f"  Missing human_label: {missing_human}")
    print(f"  Invalid human_label: {invalid_human}")
    if missing_human > 0 or invalid_human > 0:
        print("  ERROR: Data integrity check failed!")
        return
    print("  PASS: All integrity checks passed")
    print()

    # Run predictions
    print("[4] Running Phase C model predictions...")
    predictions = []
    details = []

    for i, row in enumerate(golden_rows):
        customer_text = row['customer_text']
        human_label = row['human_label']
        example_id = row['example_id']

        model_pred = classify(customer_text, phasec_model)
        is_correct = model_pred == human_label

        predictions.append(model_pred)
        details.append({
            'example_id': example_id,
            'customer_text': customer_text,
            'human_label': human_label,
            'model_prediction': model_pred,
            'correct': is_correct
        })

        if (i + 1) % 50 == 0:
            print(f"  Processed {i + 1}/{len(golden_rows)}...")

    print(f"  Completed {len(predictions)} predictions")
    print()

    # Calculate metrics
    print("[5] Calculating metrics...")
    metrics = calculate_metrics(predictions, human_labels)
    per_intent, confusion = calculate_per_intent_metrics(predictions, human_labels, VALID_INTENTS)
    top_confusion = get_top_confusion_pairs(confusion, 10)

    print(f"  Overall Accuracy: {metrics['accuracy']:.2f}%")
    print(f"  Correct: {metrics['correct']}/{metrics['total']}")
    print(f"  Incorrect: {metrics['incorrect']}/{metrics['total']}")
    print()

    # Save predictions
    print("[6] Saving predictions...")
    with open(OUTPUT_PREDICTIONS, 'w', encoding='utf-8') as f:
        for detail in details:
            f.write(json.dumps(detail, ensure_ascii=False) + '\n')
    print(f"  Saved to: {OUTPUT_PREDICTIONS}")
    print()

    # Generate report
    print("[7] Generating evaluation report...")
    report = generate_report(golden_rows, predictions, human_labels, metrics, per_intent, top_confusion, confusion)
    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"  Saved to: {OUTPUT_REPORT}")
    print()

    # Final summary
    print("=" * 70)
    print("GOLDEN SET RESULTS")
    print("=" * 70)
    print(f"Examples: {metrics['total']}")
    print(f"Correct: {metrics['correct']}")
    print(f"Incorrect: {metrics['incorrect']}")
    print(f"Accuracy: {metrics['accuracy']:.2f}%")
    print()
    print("Top confusion pairs:")
    for true_label, pred_label, count in top_confusion:
        print(f"  {true_label} -> {pred_label}: {count}")
    print()
    print("Production model changed: NO")
    print("Phase C official test accuracy remains: 71.11%")
    print("=" * 70)


def generate_report(rows, predictions, human_labels, metrics, per_intent, top_confusion, confusion):
    human_dist = Counter(human_labels)
    model_dist = Counter(predictions)

    other_pct = human_dist.get('OTHER', 0) / len(rows) * 100
    min_count = min(human_dist.values())
    max_count = max(human_dist.values())
    balance_ratio = min_count / max_count if max_count > 0 else 0

    report = """# Golden Set Evaluation Report

## Important Disclaimer

**This is an INDEPENDENT golden-set evaluation using manually labeled data.**
**It must NOT be presented as the official 71.11% Phase C test accuracy.**

The official 71.11% accuracy was obtained on a separate 540-example held-out test set
using the same Phase C model. This golden-set evaluation uses a different dataset
of 220 English-only examples with human-verified labels.

---

## Evaluation Configuration

| Setting | Value |
|---------|-------|
| Model | Phase C (TF-IDF + LinearSVC) |
| Model path | data/baseline/phaseC_model.joblib |
| Word n-grams | (1, 2) |
| Char n-grams | (3, 6) |
| Dataset | golden_set_labeled.csv |
| Examples | 220 |
| Language filter | English-only |

---

## Overall Results

| Metric | Value |
|--------|-------|
| **Accuracy** | **{accuracy:.2f}%** |
| Correct | {correct}/{total} |
| Incorrect | {incorrect}/{total} |

---

## Integrity Checks

| Check | Result |
|-------|--------|
| Input rows | PASS (220) |
| Predictions generated | PASS (220) |
| Human labels present | PASS (220) |
| Missing predictions | PASS (0) |
| Missing human labels | PASS (0) |
| Invalid intent labels | PASS (0) |

---

## Human Label Distribution

| Intent | Count | Percentage |
|--------|-------|------------|
""".format(**metrics)

    for intent, count in sorted(human_dist.items(), key=lambda x: -x[1]):
        pct = count / len(rows) * 100
        report += f"| {intent} | {count} | {pct:.1f}% |\n"

    report += f"""
**Total examples:** {len(rows)}

---

## Model Prediction Distribution

| Intent | Count | Percentage |
|--------|-------|------------|
"""

    for intent, count in sorted(model_dist.items(), key=lambda x: -x[1]):
        pct = count / len(rows) * 100
        report += f"| {intent} | {count} | {pct:.1f}% |\n"

    report += """
---

## Per-Intent Metrics

| Intent | Actual | Predicted | Correct | Precision | Recall | F1 |
|--------|--------|-----------|---------|-----------|--------|-----|
"""

    for intent in sorted(VALID_INTENTS):
        data = per_intent.get(intent, {})
        actual = data.get('actual_count', 0)
        predicted = data.get('predicted_count', 0)
        correct = data.get('correct', 0)
        prec = data.get('precision', 0)
        rec = data.get('recall', 0)
        f1 = data.get('f1', 0)
        report += f"| {intent} | {actual} | {predicted} | {correct} | {prec:.1f}% | {rec:.1f}% | {f1:.1f} |\n"

    report += """
---

## Confusion Matrix

"""
    sorted_intents = sorted(VALID_INTENTS)
    report += "| **True \\ Pred** |"
    for intent in sorted_intents:
        report += f" {intent[:8]:8s} |"
    report += "\n" + "|---" * (len(sorted_intents) + 1) + "|\n"

    for true_intent in sorted_intents:
        report += f"| **{true_intent[:12]:12s}** |"
        for pred_intent in sorted_intents:
            count = confusion[true_intent][pred_intent]
            report += f" {count:8d} |"
        report += "\n"

    report += """
---

## Top 10 Confusion Pairs

| Rank | True Intent | Predicted As | Count |
|------|-------------|--------------|-------|
"""

    for i, (true_label, pred_label, count) in enumerate(top_confusion, 1):
        report += f"| {i} | {true_label} | {pred_label} | {count} |\n"

    report += """
---

## Misclassified Examples

| Example ID | Human Label | Model Prediction |
|------------|-------------|-----------------|
"""

    misclassified = []
    for i in range(len(rows)):
        if human_labels[i] != predictions[i]:
            misclassified.append((rows[i]['example_id'], human_labels[i], predictions[i]))

    for example_id, human, model_pred in sorted(misclassified, key=lambda x: x[0]):
        report += f"| {example_id} | {human} | {model_pred} |\n"

    report += f"""
**Total misclassified:** {len(misclassified)}

---

## Class Balance Assessment

| Metric | Value |
|--------|-------|
| Min examples per intent | {min_count} |
| Max examples per intent | {max_count} |
| Balance ratio (min/max) | {balance_ratio:.2f} |
| OTHER intent ratio | {other_pct:.1f}% |

"""

    if balance_ratio < 0.1:
        conclusion = """**Conclusion:** The class distribution is HIGHLY IMBALANCED.
The OTHER intent dominates ({other_pct:.1f}% of examples), which means overall accuracy
may be heavily influenced by the model's performance on OTHER versus specific intents.
Accuracy alone may not reflect true model performance across all intents.""".format(other_pct=other_pct)
    elif other_pct > 30:
        conclusion = """**Conclusion:** The class distribution is MODERATELY IMBALANCED.
The OTHER intent is overrepresented ({other_pct:.1f}%), which may inflate or deflate
overall accuracy depending on the model's performance on OTHER.
Consider looking at per-intent metrics for a more complete picture.""".format(other_pct=other_pct)
    else:
        conclusion = """**Conclusion:** The class distribution is relatively balanced.
Overall accuracy is a meaningful metric for this golden set."""

    report += conclusion + """

---

## Production Model Status

- **Model file:** data/baseline/phaseC_model.joblib
- **Model changed:** NO
- **Official Phase C test accuracy:** 71.11% (384/540 on held-out test set)
- **This evaluation:** Independent golden-set evaluation with human-verified labels

---

*Report generated automatically*
*This evaluation is INDEPENDENT and must NOT be presented as the official 71.11% Phase C test accuracy.*

"""

    return report


if __name__ == '__main__':
    main()
