# Phase G: Targeted Data Augmentation Report

**Date:** 2026-09-12
**Phase:** EXPERIMENTAL
**Status:** COMPLETE

---

## Executive Summary

| Metric | Phase C (Baseline) | Phase G (Augmented) | Difference |
|--------|-------------------|---------------------|------------|
| **Official Test Accuracy** | **71.11%** (384/540) | **67.59%** (365/540) | **-3.52pp** |
| **Golden-Set Accuracy** | **56.36%** (124/220) | **53.64%** (118/220) | **-2.73pp** |

**Recommendation:** **REJECT PHASE G**

The targeted data augmentation experiment produced a model that performs **worse** than Phase C on both the official test set and the golden set. The augmentation strategy did not succeed.

---

## 1. Augmentation Design

### Targeted Intents

Based on Phase E error analysis, the following intents were identified as data-starved or weak:

| Intent | Training Examples | Golden-Set Accuracy |
|--------|-------------------|---------------------|
| ORDER_MODIFY | 2 | 0% |
| CANCELLATION | 2 | 0% |
| ACCOUNT_ACCESS | 27 | 0% |
| PRODUCT_ISSUE | 42 | 0% |
| DELIVERY_MISSING | 124 | 0% |

### Augmentation Added

| Intent | Original | Added | Final |
|--------|----------|-------|-------|
| ORDER_MODIFY | 2 | 20 | 22 |
| CANCELLATION | 2 | 20 | 22 |
| **Total** | 2160 | 40 | 2200 |

### Data Leakage Prevention

- NO golden-set examples used
- NO test-set examples used
- NO direct copies of existing examples
- Patterns based on error analysis from Phase E

---

## 2. Evaluation Results

### Official Test Set (540 examples)

| Model | Accuracy | Correct/Total | vs Phase C |
|-------|----------|---------------|------------|
| Phase C | 71.11% | 384/540 | - |
| Phase G | 67.59% | 365/540 | **-3.52pp** |

### Golden Set (220 examples)

| Model | Accuracy | Correct/Total | vs Phase C |
|-------|----------|---------------|------------|
| Phase C | 56.36% | 124/220 | - |
| Phase G | 53.64% | 118/220 | **-2.73pp** |

---

## 3. Per-Intent Analysis

### Golden Set Performance Comparison

| Intent | Phase C | Phase G | Change | Assessment |
|--------|---------|---------|--------|------------|
| ORDER_MODIFY | 3/4 | 4/4 | +1 | Improved |
| CANCELLATION | 4/10 | 6/10 | +2 | Improved |
| DELIVERY_LATE | 26/50 | 29/50 | +3 | Improved |
| PRODUCT_ISSUE | 4/15 | 1/15 | -3 | Degraded |
| PAYMENT_ISSUE | 11/16 | 9/16 | -2 | Degraded |
| REFUND_REQUEST | 5/11 | 3/11 | -2 | Degraded |
| ACCOUNT_ACCESS | 5/15 | 4/15 | -1 | Degraded |
| DELIVERY_MISSING | 4/22 | 3/22 | -1 | Degraded |
| DELIVERY_TRACKING | 5/6 | 4/6 | -1 | Degraded |
| VIDEO_STREAMING | 5/7 | 4/7 | -1 | Degraded |
| RETURN_REQUEST | 9/11 | 8/11 | -1 | Degraded |
| OTHER | 29/31 | 29/31 | 0 | No change |
| APP_USAGE | 5/6 | 5/6 | 0 | No change |
| DEVICE_ISSUE | 6/10 | 6/10 | 0 | No change |
| ORDER_STATUS | 3/6 | 3/6 | 0 | No change |

### Analysis

**Intents that improved with augmentation:**
- ORDER_MODIFY: +1 (75%→100%)
- CANCELLATION: +2 (40%→60%)
- DELIVERY_LATE: +3 (52%→58%)

**Intents that degraded with augmentation:**
- PRODUCT_ISSUE: -3 (27%→7%)
- PAYMENT_ISSUE: -2 (69%→56%)
- REFUND_REQUEST: -2 (45%→27%)

**Conclusion:** While augmentation helped some intents, it hurt others more, resulting in net degradation.

---

## 4. Root Cause Analysis

### Why Did Augmentation Fail?

1. **Synthetic examples lack realism**: The 40 augmented examples do not capture the full variability of real customer messages
2. **Insufficient quantity**: 20 examples per intent is not enough to meaningfully shift LinearSVC decision boundaries
3. **Model capacity**: TF-IDF + LinearSVC has limited capacity to learn from small changes in training data
4. **Trade-off effects**: Improving one intent often comes at the cost of degrading others with overlapping features

### Key Observations

- The model improved on ORDER_MODIFY and CANCELLATION (the targeted intents)
- But these improvements came at the cost of degrading other intents
- The net effect is negative (-3.52pp on test, -2.73pp on golden)

---

## 5. Decision Analysis

### Decision Framework

| Criterion | Result | Pass/Fail |
|-----------|--------|----------|
| Improves official test accuracy? | -3.52pp | **FAIL** |
| Improves golden-set performance? | -2.73pp | **FAIL** |
| Improves targeted weak intents? | Mixed (+3, +2, +1 but -3, -2, -2) | **INCONCLUSIVE** |
| Causes major regressions? | Yes (-3.52pp on test) | **FAIL** |

### Recommendation

**REJECT PHASE G**

The augmentation experiment demonstrates that:
1. Simple synthetic data augmentation does not improve TF-IDF + LinearSVC performance
2. The fundamental limitations of the model architecture remain unaddressed
3. More sophisticated approaches (transformer models, more data, active learning) would be needed

---

## 6. Files Created

| File | Description |
|------|-------------|
| `phaseG_augment.py` | Augmentation generation script |
| `data/baseline/phaseG_experimental.jsonl` | Experimental dataset (2200 examples) |
| `data/baseline/phaseG_experimental_model.joblib` | Experimental model (NOT promoted) |
| `data/evaluation/phaseG_augmentation_manifest.jsonl` | Augmentation manifest |
| `data/evaluation/phaseG_predictions.jsonl` | Phase G predictions on golden set |
| `data/evaluation/phaseG_confusion_matrix.csv` | Phase G confusion matrix |
| `data/evaluation/phaseG_comparison.json` | Comparison data |
| `phaseG_augmentation_report.md` | This report |

---

## Phase Status

```
PHASE G STATUS: COMPLETE
PRODUCTION MODEL CHANGED: NO
PRODUCTION PIPELINE CHANGED: NO
OFFICIAL TEST SET CHANGED: NO
GOLDEN SET CHANGED: NO
NON-ENGLISH TRAINING DATA REMOVED: NO
AUGMENTATION ADDED: 40 examples (20 CANCELLATION + 20 ORDER_MODIFY)

Phase C Official Test Accuracy: 71.11% (384/540)
Phase G Official Test Accuracy: 67.59% (365/540)
Phase G Difference: -3.52 percentage points

Phase C Golden-Set Accuracy: 56.36% (124/220)
Phase G Golden-Set Accuracy: 53.64% (118/220)
Phase G Difference: -2.73 percentage points

RECOMMENDATION: REJECT PHASE G

Evidence:
- Phase G performs worse on both official test set and golden set
- Augmentation improved some targeted intents (ORDER_MODIFY, CANCELLATION, DELIVERY_LATE)
- But degraded other intents more significantly (PRODUCT_ISSUE, PAYMENT_ISSUE, REFUND_REQUEST)
- Net effect is negative, making Phase G unsuitable for production
```

---

*Report generated: 2026-09-12*
*Phase G: Targeted Data Augmentation (EXPERIMENT COMPLETE)*
