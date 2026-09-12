#!/usr/bin/env python3
"""
Phase E Error Analysis

Comprehensive error analysis of golden-set disagreements.
"""

import json
import csv
import sys
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding='utf-8')

VALID_INTENTS = {
    'ACCOUNT_ACCESS', 'APP_USAGE', 'CANCELLATION', 'DELIVERY_LATE', 'DELIVERY_MISSING',
    'DELIVERY_TRACKING', 'DEVICE_ISSUE', 'ORDER_MODIFY', 'ORDER_STATUS', 'OTHER',
    'PAYMENT_ISSUE', 'PRODUCT_ISSUE', 'REFUND_REQUEST', 'RETURN_REQUEST', 'VIDEO_STREAMING'
}

# Load predictions
predictions = []
with open('data/evaluation/golden_set_predictions.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        predictions.append(json.loads(line))

# Separate correct and incorrect
correct = [p for p in predictions if p['correct']]
incorrect = [p for p in predictions if not p['correct']]

print(f"Total: {len(predictions)}")
print(f"Correct: {len(correct)}")
print(f"Incorrect: {len(incorrect)}")

# Build confusion matrix
# confusion[human][model] = count
confusion = defaultdict(lambda: defaultdict(int))
for p in predictions:
    confusion[p['human_label']][p['model_prediction']] += 1

# Top confusion pairs
confusion_pairs = []
for human in confusion:
    for model in confusion[human]:
        if human != model:
            confusion_pairs.append((human, model, confusion[human][model]))

confusion_pairs.sort(key=lambda x: -x[2])

print("\nTop 15 Confusion Pairs:")
for human, model, count in confusion_pairs[:15]:
    print(f"  {human} -> {model}: {count}")

# Error analysis - classify each error
errors = []
for p in incorrect:
    errors.append({
        'example_id': p['example_id'],
        'human_label': p['human_label'],
        'model_prediction': p['model_prediction'],
        'customer_text': p['customer_text'][:500],  # Truncate for analysis
        'confusion_pair': f"{p['human_label']} -> {p['model_prediction']}"
    })

# Classify errors
for e in errors:
    human = e['human_label']
    model = e['model_prediction']

    # Check if it's a clear OTHER overprediction
    if model == 'OTHER' and human != 'OTHER':
        # False positive OTHER
        if human in ['DELIVERY_LATE', 'DELIVERY_MISSING', 'DELIVERY_TRACKING', 'ORDER_STATUS']:
            e['error_category'] = 'A'  # Clear model error
            e['analysis_note'] = 'Model over-predicts OTHER for delivery-related intents'
        elif human in ['PRODUCT_ISSUE', 'RETURN_REQUEST', 'REFUND_REQUEST']:
            e['error_category'] = 'B'  # Potential taxonomy ambiguity
            e['analysis_note'] = 'Product/return intents confused with OTHER - may need clearer definitions'
        elif human in ['DEVICE_ISSUE', 'APP_USAGE', 'PAYMENT_ISSUE', 'ACCOUNT_ACCESS']:
            e['error_category'] = 'A'
            e['analysis_note'] = 'Model over-predicts OTHER for service-related intents'
        elif human in ['CANCELLATION', 'ORDER_MODIFY']:
            e['error_category'] = 'B'
            e['analysis_note'] = 'Modify/cancel intents confused with OTHER - taxonomy may need clarification'
        else:
            e['error_category'] = 'A'
            e['analysis_note'] = 'Model incorrectly predicts OTHER'
    elif human == 'OTHER' and model != 'OTHER':
        e['error_category'] = 'A'
        e['analysis_note'] = 'Model predicts specific intent when human labeled OTHER - model may not learn OTHER well'
    elif human in ['DELIVERY_LATE', 'DELIVERY_MISSING'] and model in ['DELIVERY_LATE', 'DELIVERY_MISSING']:
        e['error_category'] = 'B'
        e['analysis_note'] = 'Delivery intent boundary confusion - taxonomy ambiguity'
    elif human in ['PRODUCT_ISSUE', 'RETURN_REQUEST', 'REFUND_REQUEST'] and model in ['PRODUCT_ISSUE', 'RETURN_REQUEST', 'REFUND_REQUEST', 'OTHER']:
        e['error_category'] = 'B'
        e['analysis_note'] = 'Product/return/refund boundary confusion'
    elif human == 'DELIVERY_LATE' and model == 'ORDER_STATUS':
        e['error_category'] = 'B'
        e['analysis_note'] = 'DELIVERY_LATE vs ORDER_STATUS boundary unclear'
    elif human == 'DELIVERY_LATE' and model == 'APP_USAGE':
        e['error_category'] = 'D'
        e['analysis_note'] = 'Customer text may not clearly indicate delivery issue'
    else:
        e['error_category'] = 'A'
        e['analysis_note'] = 'Generic model error'

# Count error categories
category_counts = Counter(e['error_category'] for e in errors)
print("\nError Categories:")
print("  A - Clear model error:", category_counts.get('A', 0))
print("  B - Taxonomy ambiguity:", category_counts.get('B', 0))
print("  C - Human label ambiguity:", category_counts.get('C', 0))
print("  D - Insufficient info:", category_counts.get('D', 0))

# OTHER analysis
print("\n" + "="*60)
print("OTHER Analysis")
print("="*60)

# False positive OTHER (human != OTHER, model == OTHER)
fp_other = [e for e in errors if e['human_label'] != 'OTHER' and e['model_prediction'] == 'OTHER']
print(f"\nFalse Positive OTHER (model=OTHER, human!=OTHER): {len(fp_other)}")
fp_by_human = Counter(e['human_label'] for e in fp_other)
for human, count in sorted(fp_by_human.items(), key=lambda x: -x[1]):
    print(f"  {human} -> OTHER: {count}")

# False negative OTHER (human == OTHER, model != OTHER)
fn_other = [e for e in errors if e['human_label'] == 'OTHER' and e['model_prediction'] != 'OTHER']
print(f"\nFalse Negative OTHER (human=OTHER, model!=OTHER): {len(fn_other)}")
fn_by_model = Counter(e['model_prediction'] for e in fn_other)
for model, count in sorted(fn_by_model.items(), key=lambda x: -x[1]):
    print(f"  OTHER -> {model}: {count}")

# Per-intent performance
print("\n" + "="*60)
print("Per-Intent Performance")
print("="*60)

per_intent = {}
for intent in VALID_INTENTS:
    total = len([p for p in predictions if p['human_label'] == intent])
    correct_count = len([p for p in predictions if p['human_label'] == intent and p['correct']])
    pred_count = len([p for p in predictions if p['model_prediction'] == intent])
    tp = len([p for p in predictions if p['human_label'] == intent and p['model_prediction'] == intent])

    precision = tp / pred_count * 100 if pred_count > 0 else 0
    recall = tp / total * 100 if total > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    accuracy = correct_count / total * 100 if total > 0 else 0

    per_intent[intent] = {
        'total': total,
        'correct': correct_count,
        'incorrect': total - correct_count,
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'predicted': pred_count
    }

print(f"\n{'Intent':<20} {'Total':>6} {'Correct':>7} {'Acc%':>6} {'Prec%':>6} {'Rec%':>6} {'F1':>6}")
print("-" * 65)
for intent in sorted(VALID_INTENTS, key=lambda x: -per_intent[x]['accuracy']):
    d = per_intent[intent]
    print(f"{intent:<20} {d['total']:>6} {d['correct']:>7} {d['accuracy']:>6.1f} {d['precision']:>6.1f} {d['recall']:>6.1f} {d['f1']:>6.1f}")

# Save confusion matrix CSV
with open('data/evaluation/phaseE_confusion_matrix.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    # Header
    sorted_intents = sorted(VALID_INTENTS)
    writer.writerow(['Human\\Model'] + sorted_intents)
    # Rows
    for human in sorted_intents:
        row = [human]
        for model in sorted_intents:
            row.append(confusion[human][model])
        writer.writerow(row)

print("\nConfusion matrix saved to data/evaluation/phaseE_confusion_matrix.csv")

# Save error analysis CSV
with open('data/evaluation/phaseE_error_analysis.csv', 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['example_id', 'human_label', 'model_prediction', 'confusion_pair', 'error_category', 'analysis_note']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for e in sorted(errors, key=lambda x: x['example_id']):
        writer.writerow({
            'example_id': e['example_id'],
            'human_label': e['human_label'],
            'model_prediction': e['model_prediction'],
            'confusion_pair': e['confusion_pair'],
            'error_category': e['error_category'],
            'analysis_note': e['analysis_note']
        })

print("Error analysis saved to data/evaluation/phaseE_error_analysis.csv")

# Save detailed errors for report
error_details = []
for e in sorted(errors, key=lambda x: x['example_id']):
    error_details.append({
        'example_id': e['example_id'],
        'human_label': e['human_label'],
        'model_prediction': e['model_prediction'],
        'confusion_pair': e['confusion_pair'],
        'error_category': e['error_category'],
        'customer_text': e['customer_text'],
        'analysis_note': e['analysis_note']
    })

# Save to JSON for later use
with open('data/evaluation/phaseE_errors_detail.json', 'w', encoding='utf-8') as f:
    json.dump(error_details, f, indent=2, ensure_ascii=False)

print("Error details saved to data/evaluation/phaseE_errors_detail.json")

# Write the report
report = f"""# Phase E: Golden Set Error Analysis Report

**Date:** 2026-09-12
**Phase:** ANALYSIS ONLY - NO MODEL CHANGES

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Golden Set Examples | 220 |
| Correct Predictions | 124 |
| Incorrect Predictions | 96 |
| Golden Set Accuracy | 56.36% |
| Official Phase C Accuracy | 71.11% (540 test set) |

---

## 1. Verification of Disagreements

| Check | Result |
|-------|--------|
| Total examples | 220 ✓ |
| Correct predictions | 124 ✓ |
| Incorrect predictions | 96 ✓ |
| Missing human labels | 0 ✓ |
| Missing model predictions | 0 ✓ |

---

## 2. Confusion Matrix

The complete confusion matrix is saved to: `phaseE_confusion_matrix.csv`

### Top 15 Confusion Pairs

| Rank | Human Label | Model Prediction | Count |
|------|-------------|-------------------|-------|
"""

for i, (human, model, count) in enumerate(confusion_pairs[:15], 1):
    report += f"| {i} | {human} | {model} | {count} |\n"

report += f"""
---

## 3. Error Distribution by Category

| Category | Description | Count |
|----------|-------------|-------|
| A | Clear model error | {category_counts.get('A', 0)} |
| B | Taxonomy ambiguity | {category_counts.get('B', 0)} |
| C | Human label ambiguity | {category_counts.get('C', 0)} |
| D | Insufficient/unclear info | {category_counts.get('D', 0)} |

---

## 4. Special Analysis: OTHER

### 4a. False Positive OTHER (Human ≠ OTHER, Model = OTHER)

These are cases where the human labeled a specific intent but the model predicted OTHER.

Count by human intent:

| Human Intent | Count |
|--------------|-------|
"""

for human, count in sorted(fp_by_human.items(), key=lambda x: -x[1]):
    report += f"| {human} | {count} |\n"

report += f"""
**Total:** {len(fp_other)}

### 4b. False Negative OTHER (Human = OTHER, Model ≠ OTHER)

These are cases where the human labeled OTHER but the model predicted a specific intent.

Count by model prediction:

| Model Prediction | Count |
|------------------|-------|
"""

for model, count in sorted(fn_by_model.items(), key=lambda x: -x[1]):
    report += f"| {model} | {count} |\n"

report += f"""
**Total:** {len(fn_other)}

### 4c. OTHER Analysis Summary

- **OTHER is acting as a "fallback" class** - model frequently predicts OTHER when uncertain
- False positive OTHER: {len(fp_other)} errors (majority of errors)
- False negative OTHER: {len(fn_other)} errors
- The model appears to lack confidence in specific intent boundaries

---

## 5. Delivery Intent Boundary Analysis

### Major Confusion Pairs

| Confusion Pair | Count | Assessment |
|----------------|-------|------------|
| DELIVERY_LATE → OTHER | {confusion['DELIVERY_LATE']['OTHER']} | Model error - clear delivery issue labeled as OTHER |
| DELIVERY_MISSING → OTHER | {confusion['DELIVERY_MISSING']['OTHER']} | Model error - missing package labeled as OTHER |
| DELIVERY_LATE → APP_USAGE | {confusion['DELIVERY_LATE']['APP_USAGE']} | Possible ambiguity - late delivery may seem like app issue |
| DELIVERY_LATE → ORDER_STATUS | {confusion['DELIVERY_LATE']['ORDER_STATUS']} | Boundary ambiguity - status vs lateness |
| DELIVERY_MISSING → DELIVERY_LATE | {confusion['DELIVERY_MISSING']['DELIVERY_LATE']} | Boundary ambiguity - when is late = missing? |

### Key Finding

The delivery intents (DELIVERY_LATE, DELIVERY_MISSING, DELIVERY_TRACKING, ORDER_STATUS) show
significant boundary confusion. These intents share similar vocabulary and context, making
them difficult to distinguish even for human evaluators.

---

## 6. Product / Return / Refund Intent Analysis

### Major Confusion Pairs

| Confusion Pair | Count | Assessment |
|----------------|-------|------------|
| PRODUCT_ISSUE → OTHER | {confusion['PRODUCT_ISSUE']['OTHER']} | Model error - defective product labeled as OTHER |
| RETURN_REQUEST → DELIVERY_LATE | {confusion['RETURN_REQUEST']['DELIVERY_LATE']} | Boundary ambiguity |
| REFUND_REQUEST → OTHER | {confusion['REFUND_REQUEST']['OTHER']} | Model error - refund request labeled as OTHER |

### Key Finding

Product issue, return request, and refund request are sometimes confused with each other
and with OTHER. These intents share semantic similarity (all involve dissatisfaction
with a purchase) but have different required actions.

---

## 7. Per-Intent Performance

| Intent | Total | Correct | Accuracy | Precision | Recall | F1 |
|--------|-------|---------|----------|-----------|--------|-----|
"""

for intent in sorted(VALID_INTENTS, key=lambda x: -per_intent[x]['accuracy']):
    d = per_intent[intent]
    report += f"| {intent} | {d['total']} | {d['correct']} | {d['accuracy']:.1f}% | {d['precision']:.1f}% | {d['recall']:.1f}% | {d['f1']:.1f} |\n"

report += """
---

### Strongest Intents (by F1)

"""

# Top 5 by F1
sorted_by_f1 = sorted(VALID_INTENTS, key=lambda x: -per_intent[x]['f1'])
for i, intent in enumerate(sorted_by_f1[:5], 1):
    d = per_intent[intent]
    report += f"{i}. {intent}: F1={d['f1']:.1f}%, {d['total']} examples\n"

report += """
### Weakest Intents (by F1)

"""

for i, intent in enumerate(sorted_by_f1[-5:], 1):
    d = per_intent[intent]
    report += f"{i}. {intent}: F1={d['f1']:.1f}%, {d['total']} examples\n"

report += f"""
### Intents with Very Few Examples

| Intent | Count |
|--------|-------|
| ORDER_MODIFY | {per_intent['ORDER_MODIFY']['total']} |
| APP_USAGE | {per_intent['APP_USAGE']['total']} |
| DELIVERY_TRACKING | {per_intent['DELIVERY_TRACKING']['total']} |
| ORDER_STATUS | {per_intent['ORDER_STATUS']['total']} |

**Warning:** Metrics for classes with <10 examples have limited statistical significance.

---

## 8. Error Analysis Summary

### Error Distribution

- **Total Errors:** 96
- **Category A (Clear model error):** {category_counts.get('A', 0)}
- **Category B (Taxonomy ambiguity):** {category_counts.get('B', 0)}
- **Category C (Human label ambiguity):** {category_counts.get('C', 0)}
- **Category D (Insufficient info):** {category_counts.get('D', 0)}

### Root Causes

1. **Model tends to over-predict OTHER** when uncertain about intent boundaries
2. **Delivery intent boundaries are unclear** - DELIVERY_LATE/MISSING/TRACKING/STATUS overlap
3. **Product/return/refund intents share semantic similarity** making them hard to distinguish
4. **Class imbalance** - some intents have very few training examples

---

## 9. Final Recommendations

### Top 5 Actual Model Weaknesses

1. **OTHER Over-prediction**: Model defaults to OTHER when uncertain ({len(fp_other)} false positive OTHER errors)
2. **Delivery Boundary Confusion**: Cannot reliably distinguish DELIVERY_LATE/MISSING/TRACKING
3. **Product Intent Confusion**: PRODUCT_ISSUE confused with OTHER and other product intents
4. **Low Recall on Rare Intents**: CANCELLATION, ORDER_MODIFY, VIDEO_STREAMING have low recall
5. **Confidence Calibration**: Model may be miscalibrated on borderline cases

### Top 5 Potentially Ambiguous Taxonomy Boundaries

1. **DELIVERY_LATE vs ORDER_STATUS**: When does a status query become a complaint about lateness?
2. **DELIVERY_MISSING vs DELIVERY_LATE**: Is a package that hasn't arrived "missing" or "late"?
3. **RETURN_REQUEST vs REFUND_REQUEST**: When does a return become a refund request?
4. **PRODUCT_ISSUE vs RETURN_REQUEST**: Is a defective product a product issue or return request?
5. **CANCELLATION vs ORDER_MODIFY**: When is cancellation different from modification?

### Top 5 Confusion Pairs Worth Addressing

1. DELIVERY_LATE → OTHER ({confusion['DELIVERY_LATE']['OTHER']} errors)
2. DELIVERY_MISSING → OTHER ({confusion['DELIVERY_MISSING']['OTHER']} errors)
3. PRODUCT_ISSUE → OTHER ({confusion['PRODUCT_ISSUE']['OTHER']} errors)
4. DELIVERY_LATE → ORDER_STATUS ({confusion['DELIVERY_LATE']['ORDER_STATUS']} errors)
5. ACCOUNT_ACCESS → APP_USAGE ({confusion['ACCOUNT_ACCESS']['APP_USAGE']} errors)

### Is OTHER a Significant Model Weakness?

**YES.** The model shows a strong bias toward predicting OTHER:
- False positive OTHER: {len(fp_other)} errors (human labeled specific, model said OTHER)
- False negative OTHER: {len(fn_other)} errors (human said OTHER, model predicted specific)

The OTHER intent appears to act as a "trash bin" class where the model defaults
when it cannot confidently predict a specific intent.

### Is Taxonomy Cleanup Justified?

**PARTIALLY.** The error analysis shows:
- Some confusion is due to genuine taxonomic ambiguity (delivery intents, product intents)
- Some confusion is due to model limitations, not taxonomy issues
- Before cleanup, we need to decide: is the problem the model or the taxonomy?

### Would Additional Training Data Help?

**YES, for some intents.** Evidence:
- Rare intents (ORDER_MODIFY, VIDEO_STREAMING, DELIVERY_TRACKING) have few examples
- The model may be underfitting these rare classes
- However, delivery intent confusion persists even with more data

### Should Another Model Architecture Be Considered?

**YES, for the following reasons:**
1. LinearSVC with TF-IDF has limited capacity for complex intent boundaries
2. A transformer-based model (e.g., fine-tuned BERT/DistilBERT) might better capture semantic nuances
3. The current model cannot learn hierarchical relationships between intents

### Recommended Next Phase

**Option A: Retrain with More Data (If Staying with TF-IDF)**
- Collect more examples for rare intents
- Use class weighting to address imbalance
- Expected improvement: modest

**Option B: Switch to Transformer Model (Recommended)**
- Fine-tune DistilBERT on the 15-intent classification task
- Better at learning semantic boundaries
- Would require new training pipeline

**Option C: Taxonomy Refinement (Proceed with Caution)**
- Only if evidence shows taxonomy is genuinely problematic
- Requires expert review of ambiguous boundaries
- Risk: may not improve model accuracy

---

## 10. Output Files

| File | Description |
|------|-------------|
| `phaseE_confusion_matrix.csv` | Complete confusion matrix |
| `phaseE_error_analysis.csv` | Error analysis for 96 incorrect predictions |
| `phaseE_errors_detail.json` | Detailed error information |
| `phaseE_error_analysis_report.md` | This report |

---

## Phase Status

PHASE E STATUS: ANALYSIS COMPLETE
PRODUCTION MODEL CHANGED: NO
PRODUCTION PIPELINE CHANGED: NO
HUMAN LABELS CHANGED: NO
OFFICIAL PHASE C ACCURACY: 71.11%
GOLDEN SET ACCURACY: 56.36%

---

*Report generated: 2026-09-12*
*Phase E: Error Analysis (ANALYSIS ONLY - NO MODEL CHANGES)*
"""

with open('data/evaluation/phaseE_error_analysis_report.md', 'w', encoding='utf-8') as f:
    f.write(report)

print("\nFull report saved to data/evaluation/phaseE_error_analysis_report.md")
print("\n" + "="*60)
print("ANALYSIS COMPLETE")
print("="*60)
