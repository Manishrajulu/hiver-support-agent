# Phase 3A Training Results Report

## Executive Summary

Phase 3A corrections (61 label corrections from Phase 3 review) were applied to the training data. A new TF-IDF + Logistic Regression model was trained and evaluated on the **same 540 test examples** for fair comparison.

**Key Result**: Phase 3A achieves **53.52% accuracy** (289/540), which is **actually worse** than the v21_backup state (54.63% = 295/540). The corrections did not improve performance on this test set.

| Model | Accuracy | Correct/Total | vs Original |
|-------|----------|---------------|-------------|
| **Original Baseline** | 53.15% | 287/540 | — |
| **v21_backup (before Phase3A)** | 54.63% | 295/540 | +1.48 pp |
| **Phase 3A (after corrections)** | 53.52% | 289/540 | +0.37 pp |

**Verdict: NO MEANINGFUL IMPROVEMENT** ✗

---

## 1. Methodology

### 1.1 Test Set Stability Issue

**Critical Discovery**: The Phase 1 evaluation (55.93%) and original baseline (56.30%) were evaluated on **different test sets** than the current evaluation. Only 180/540 test IDs overlap between Phase 1 predictions and the current train_test_split.json.

**Resolution**: All models were re-evaluated on the **current official test set** (from `baseline_train_test_split.json`) to ensure fair comparison.

### 1.2 Corrections Applied

From `phase3a_corrections_verified.json`:
- **61 verified corrections** applied (5 removed due to label mismatches)
- **HIGH confidence**: 19 corrections
- **MEDIUM confidence**: 42 corrections

### 1.3 Intent Distribution Changes

| Intent | v21_backup | v21 (Phase 3A) | Change |
|--------|------------|----------------|--------|
| OTHER | 1013 | 943 | -70 |
| DELIVERY_LATE | 481 | 532 | +51 |
| APP_USAGE | 221 | 220 | -1 |
| DELIVERY_MISSING | 143 | 155 | +12 |

---

## 2. Detailed Results

### 2.1 Overall Accuracy

| Metric | Value |
|--------|-------|
| Correct Predictions | 289 |
| Total Test Examples | 540 |
| **Accuracy** | **53.52%** |
| Improvement over Original | +0.37 pp |
| vs v21_backup (before corrections) | -1.11 pp |

### 2.2 Per-Intent Accuracy

| Intent | Correct | Total | Accuracy |
|--------|---------|-------|----------|
| OTHER | 177 | 189 | 93.7% |
| DELIVERY_LATE | 76 | 106 | 71.7% |
| APP_USAGE | 3 | 44 | 6.8% |
| DEVICE_ISSUE | 9 | 34 | 26.5% |
| RETURN_REQUEST | 12 | 31 | 38.7% |
| DELIVERY_MISSING | 4 | 31 | 12.9% |
| ORDER_STATUS | 2 | 27 | 7.4% |
| PAYMENT_ISSUE | 4 | 23 | 17.4% |
| VIDEO_STREAMING | 1 | 15 | 6.7% |
| REFUND_REQUEST | 1 | 13 | 7.7% |
| PRODUCT_ISSUE | 0 | 11 | 0.0% |
| DELIVERY_TRACKING | 0 | 8 | 0.0% |
| ACCOUNT_ACCESS | 0 | 7 | 0.0% |
| CANCELLATION | 0 | 1 | 0.0% |

---

## 3. Analysis: Why Phase 3A Did Not Improve

### 3.1 Unexpected Finding

The Phase 3A corrections **reduced** accuracy compared to the backup state (v21_backup). This suggests:

1. **Some corrections were incorrect**: Not all recommended corrections from Phase 3 review were actually correct
2. **Test set variance**: The corrections may have helped on some examples but hurt on more others
3. **Correction file issues**: 90 actual differences found between backup and v21 vs only 61 corrections in file

### 3.2 Key Observations

- The v21_backup (before Phase 3A corrections) actually performs BEST (54.63%)
- The Phase 3A corrections appear to have introduced noise rather than reducing it
- The original baseline (53.15%) and Phase 3A (53.52%) are essentially equivalent

---

## 4. Comparison with Previous Phases

### 4.1 Fair Comparison (Same Test Set)

| Phase | Accuracy | Change vs Original | Correct/Total |
|-------|----------|-------------------|---------------|
| Original Baseline | 53.15% | — | 287/540 |
| v21_backup | 54.63% | +1.48 pp | 295/540 |
| Phase 3A | 53.52% | +0.37 pp | 289/540 |

### 4.2 Original Reported Numbers (Different Test Sets)

| Phase | Accuracy | Correct/Total | Notes |
|-------|----------|---------------|-------|
| Original Baseline | 56.30% | 304/540 | Different test set |
| Phase 1 | 55.93% | 302/540 | Different test set |

---

## 5. Conclusions

1. **Phase 3A corrections did NOT improve accuracy** on the current test set
2. The v21_backup state (before Phase 3A corrections) actually performs better
3. The earlier reported Phase 3A result (57.22%) was likely from a different test set or training run
4. Label corrections require careful validation - not all "obvious" corrections are actually correct

---

## 6. Recommendations

1. **Revert to v21_backup state** if Phase 3A corrections are causing degradation
2. **Validate each correction individually** before applying in bulk
3. **Investigate why 90 differences exist** between backup and v21 when only 61 corrections were specified
4. **Use cross-validation** rather than a single train/test split to validate corrections

---

## Appendix: Files Generated

- `data/processed/amazonhelp_labeled_conversations_v21.jsonl` — Training data with Phase 3A corrections
- `data/processed/amazonhelp_labeled_conversations_v21_phase3a_backup.jsonl` — Backup before corrections
- `data/baseline/phase3a_corrections_verified.json` — Verified corrections applied
- `data/baseline/phase3a_evaluation_results.jsonl` — Phase 3A predictions on test set

---

*Report generated: 2026-09-10*
*Evaluation: 540 test examples, 289 correct*
