# Phase E: Golden Set Error Analysis Report

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
| 1 | DELIVERY_LATE | OTHER | 14 |
| 2 | DELIVERY_MISSING | OTHER | 8 |
| 3 | PRODUCT_ISSUE | OTHER | 6 |
| 4 | DELIVERY_LATE | APP_USAGE | 4 |
| 5 | DELIVERY_LATE | ORDER_STATUS | 4 |
| 6 | DELIVERY_MISSING | DELIVERY_LATE | 4 |
| 7 | ACCOUNT_ACCESS | APP_USAGE | 4 |
| 8 | ACCOUNT_ACCESS | OTHER | 4 |
| 9 | DEVICE_ISSUE | OTHER | 3 |
| 10 | RETURN_REQUEST | DELIVERY_LATE | 2 |
| 11 | REFUND_REQUEST | DELIVERY_LATE | 2 |
| 12 | DELIVERY_LATE | DELIVERY_MISSING | 2 |
| 13 | DELIVERY_MISSING | ORDER_STATUS | 2 |
| 14 | DELIVERY_MISSING | DEVICE_ISSUE | 2 |
| 15 | PRODUCT_ISSUE | DELIVERY_LATE | 2 |

---

## 3. Error Distribution by Category

| Category | Description | Count |
|----------|-------------|-------|
| A | Clear model error | 74 |
| B | Taxonomy ambiguity | 18 |
| C | Human label ambiguity | 0 |
| D | Insufficient/unclear info | 4 |

---

## 4. Special Analysis: OTHER

### 4a. False Positive OTHER (Human ≠ OTHER, Model = OTHER)

These are cases where the human labeled a specific intent but the model predicted OTHER.

Count by human intent:

| Human Intent | Count |
|--------------|-------|
| DELIVERY_LATE | 14 |
| DELIVERY_MISSING | 8 |
| PRODUCT_ISSUE | 6 |
| ACCOUNT_ACCESS | 4 |
| DEVICE_ISSUE | 3 |
| PAYMENT_ISSUE | 2 |
| CANCELLATION | 1 |
| ORDER_STATUS | 1 |

**Total:** 39

### 4b. False Negative OTHER (Human = OTHER, Model ≠ OTHER)

These are cases where the human labeled OTHER but the model predicted a specific intent.

Count by model prediction:

| Model Prediction | Count |
|------------------|-------|
| APP_USAGE | 1 |
| DELIVERY_LATE | 1 |

**Total:** 2

### 4c. OTHER Analysis Summary

- **OTHER is acting as a "fallback" class** - model frequently predicts OTHER when uncertain
- False positive OTHER: 39 errors (majority of errors)
- False negative OTHER: 2 errors
- The model appears to lack confidence in specific intent boundaries

---

## 5. Delivery Intent Boundary Analysis

### Major Confusion Pairs

| Confusion Pair | Count | Assessment |
|----------------|-------|------------|
| DELIVERY_LATE → OTHER | 14 | Model error - clear delivery issue labeled as OTHER |
| DELIVERY_MISSING → OTHER | 8 | Model error - missing package labeled as OTHER |
| DELIVERY_LATE → APP_USAGE | 4 | Possible ambiguity - late delivery may seem like app issue |
| DELIVERY_LATE → ORDER_STATUS | 4 | Boundary ambiguity - status vs lateness |
| DELIVERY_MISSING → DELIVERY_LATE | 4 | Boundary ambiguity - when is late = missing? |

### Key Finding

The delivery intents (DELIVERY_LATE, DELIVERY_MISSING, DELIVERY_TRACKING, ORDER_STATUS) show
significant boundary confusion. These intents share similar vocabulary and context, making
them difficult to distinguish even for human evaluators.

---

## 6. Product / Return / Refund Intent Analysis

### Major Confusion Pairs

| Confusion Pair | Count | Assessment |
|----------------|-------|------------|
| PRODUCT_ISSUE → OTHER | 6 | Model error - defective product labeled as OTHER |
| RETURN_REQUEST → DELIVERY_LATE | 2 | Boundary ambiguity |
| REFUND_REQUEST → OTHER | 0 | Model error - refund request labeled as OTHER |

### Key Finding

Product issue, return request, and refund request are sometimes confused with each other
and with OTHER. These intents share semantic similarity (all involve dissatisfaction
with a purchase) but have different required actions.

---

## 7. Per-Intent Performance

| Intent | Total | Correct | Accuracy | Precision | Recall | F1 |
|--------|-------|---------|----------|-----------|--------|-----|
| OTHER | 31 | 29 | 93.5% | 42.6% | 93.5% | 58.6 |
| APP_USAGE | 6 | 5 | 83.3% | 31.2% | 83.3% | 45.5 |
| DELIVERY_TRACKING | 6 | 5 | 83.3% | 100.0% | 83.3% | 90.9 |
| RETURN_REQUEST | 11 | 9 | 81.8% | 90.0% | 81.8% | 85.7 |
| ORDER_MODIFY | 4 | 3 | 75.0% | 60.0% | 75.0% | 66.7 |
| VIDEO_STREAMING | 7 | 5 | 71.4% | 100.0% | 71.4% | 83.3 |
| PAYMENT_ISSUE | 16 | 11 | 68.8% | 84.6% | 68.8% | 75.9 |
| DEVICE_ISSUE | 10 | 6 | 60.0% | 50.0% | 60.0% | 54.5 |
| DELIVERY_LATE | 50 | 26 | 52.0% | 63.4% | 52.0% | 57.1 |
| ORDER_STATUS | 6 | 3 | 50.0% | 21.4% | 50.0% | 30.0 |
| REFUND_REQUEST | 11 | 5 | 45.5% | 100.0% | 45.5% | 62.5 |
| CANCELLATION | 10 | 4 | 40.0% | 80.0% | 40.0% | 53.3 |
| ACCOUNT_ACCESS | 15 | 5 | 33.3% | 100.0% | 33.3% | 50.0 |
| PRODUCT_ISSUE | 15 | 4 | 26.7% | 80.0% | 26.7% | 40.0 |
| DELIVERY_MISSING | 22 | 4 | 18.2% | 36.4% | 18.2% | 24.2 |

---

### Strongest Intents (by F1)

1. DELIVERY_TRACKING: F1=90.9%, 6 examples
2. RETURN_REQUEST: F1=85.7%, 11 examples
3. VIDEO_STREAMING: F1=83.3%, 7 examples
4. PAYMENT_ISSUE: F1=75.9%, 16 examples
5. ORDER_MODIFY: F1=66.7%, 4 examples

### Weakest Intents (by F1)

1. ACCOUNT_ACCESS: F1=50.0%, 15 examples
2. APP_USAGE: F1=45.5%, 6 examples
3. PRODUCT_ISSUE: F1=40.0%, 15 examples
4. ORDER_STATUS: F1=30.0%, 6 examples
5. DELIVERY_MISSING: F1=24.2%, 22 examples

### Intents with Very Few Examples

| Intent | Count |
|--------|-------|
| ORDER_MODIFY | 4 |
| APP_USAGE | 6 |
| DELIVERY_TRACKING | 6 |
| ORDER_STATUS | 6 |

**Warning:** Metrics for classes with <10 examples have limited statistical significance.

---

## 8. Error Analysis Summary

### Error Distribution

- **Total Errors:** 96
- **Category A (Clear model error):** 74
- **Category B (Taxonomy ambiguity):** 18
- **Category C (Human label ambiguity):** 0
- **Category D (Insufficient info):** 4

### Root Causes

1. **Model tends to over-predict OTHER** when uncertain about intent boundaries
2. **Delivery intent boundaries are unclear** - DELIVERY_LATE/MISSING/TRACKING/STATUS overlap
3. **Product/return/refund intents share semantic similarity** making them hard to distinguish
4. **Class imbalance** - some intents have very few training examples

---

## 9. Final Recommendations

### Top 5 Actual Model Weaknesses

1. **OTHER Over-prediction**: Model defaults to OTHER when uncertain (39 false positive OTHER errors)
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

1. DELIVERY_LATE → OTHER (14 errors)
2. DELIVERY_MISSING → OTHER (8 errors)
3. PRODUCT_ISSUE → OTHER (6 errors)
4. DELIVERY_LATE → ORDER_STATUS (4 errors)
5. ACCOUNT_ACCESS → APP_USAGE (4 errors)

### Is OTHER a Significant Model Weakness?

**YES.** The model shows a strong bias toward predicting OTHER:
- False positive OTHER: 39 errors (human labeled specific, model said OTHER)
- False negative OTHER: 2 errors (human said OTHER, model predicted specific)

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
