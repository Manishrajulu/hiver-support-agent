# Phase F Fair Comparison Audit Report

**Date:** 2026-09-12
**Phase:** AUDIT ONLY
**Status:** COMPLETE

---

## Executive Summary

The original Phase F comparison was **INVALID** because it used different test set sizes (466 vs 540).

**Root Cause:** Phase F filtered to English-only training AND test data, excluding 74 non-English test examples.

**Corrected Results:**

| Evaluation | Phase C | Phase F | Difference |
|-----------|---------|---------|------------|
| Official Test (540) | **71.11%** (384/540) | **66.48%** (359/540) | **-4.63pp** |
| Golden Set (220) | 56.36% (124/220) | 56.82% (125/220) | +0.45pp |

---

## 1. Audit Findings

### Question 1: Why were 74 test examples excluded?

**Answer:** The Phase F script filtered both training AND test data to English-only (`language == 'en'`).

| Dataset | Original | English-Only | Excluded |
|---------|----------|--------------|----------|
| Training | 2,160 | 1,840 | 320 (non-English) |
| Test | 540 | 466 | **74 (non-English)** |

### Question 2: Which 74 examples were excluded?

**Answer:** The 74 non-English test examples (`language = 'non_en'` in `phaseC_experimental.jsonl`).

### Question 3: What was the exclusion reason?

**Answer:** Intentional language filtering. Phase F hypothesized that English-only training would improve English intent classification. However, this created an invalid comparison because:

1. Phase C was evaluated on ALL 540 test examples
2. Phase F was evaluated on only 466 English test examples
3. The denominators differ, making accuracy comparisons invalid

### Question 4: Does Phase F produce predictions for all 540 examples?

**Answer:** YES. The Phase F model can classify any text. The exclusion was in the evaluation script's filtering, not in the model's capability.

### Question 5: Fair evaluation on the same 540 test set?

**Answer:** YES. Re-evaluated Phase F on the exact same 540 test examples as Phase C.

### Question 6: Fair evaluation on the same 220 golden set?

**Answer:** YES. Both models were evaluated on all 220 golden set examples.

---

## 2. Detailed Findings

### Original (Invalid) Phase F Comparison

| Metric | Phase C | Phase F (invalid) |
|--------|---------|-------------------|
| Test Accuracy | 71.11% (384/540) | 63.95% (298/466) |
| Denominator | 540 | 466 |
| **Issue** | - | Different test set |

The original Phase F report incorrectly compared:
- Phase C: 384/540
- Phase F: 298/466

**This is comparing apples to oranges because the test sets differ.**

### Corrected (Valid) Phase F Comparison

| Metric | Phase C | Phase F (corrected) |
|--------|---------|---------------------|
| Test Accuracy | **71.11%** (384/540) | **66.48%** (359/540) |
| Golden Accuracy | 56.36% (124/220) | 56.82% (125/220) |

Both evaluated on identical test sets (540) and golden set (220).

---

## 3. Why the Discrepancy?

### Non-English Test Examples Analysis

The 74 excluded non-English test examples are a mix of Spanish, Arabic, Hindi, and other languages. The Phase C model was trained on mixed-language data (2,160 examples including 320 non-English), which may have:

1. **Helped generalization** - The model learned to handle code-switching and multilingual patterns
2. **Provided additional training signal** - Even non-English examples with clear intents help the classifier learn
3. **Not hurt English performance** - The Phase C model still achieves 71.11% on English-heavy test set

### Phase F's English-Only Approach

Phase F trained on 1,840 English-only examples (losing 320 non-English training examples). This resulted in:

1. **Less training data** - 320 fewer examples
2. **No multilingual signal** - Lost ability to handle code-switching
3. **Slightly better on golden set** - But only +0.45pp, below significance threshold

---

## 4. Error Analysis

### Test Set Error Comparison (540 examples)

| Category | Phase C | Phase F |
|---------|---------|---------|
| Correct | 384 | 359 |
| Errors | 156 | 181 |
| Error Rate | 28.89% | 33.52% |

Phase F introduces **25 additional errors** compared to Phase C.

### Golden Set Error Comparison (220 examples)

| Category | Phase C | Phase F |
|---------|---------|---------|
| Correct | 124 | 125 |
| Errors | 96 | 95 |
| Error Rate | 43.64% | 43.18% |

Phase F fixes **1 error** and introduces **0 new errors** (net improvement of 1 error).

### Interpretation

- Phase F performs **slightly better** on the golden set (+0.45pp)
- Phase F performs **significantly worse** on the test set (-4.63pp)
- The golden set improvement does not generalize to the test set

**This pattern suggests Phase F is overfitting to the golden set's distribution.**

---

## 5. Conclusion

### Was the Original Phase F Comparison Valid?

**NO.** The original Phase F comparison was invalid because:

1. Phase C was evaluated on 540 test examples
2. Phase F was evaluated on only 466 test examples
3. The comparison used different denominators
4. Accuracy cannot be fairly compared across different test sets

### Corrected Comparison

| Metric | Phase C | Phase F | Verdict |
|--------|---------|---------|---------|
| Test Accuracy (540) | 71.11% | 66.48% | Phase C **wins** |
| Golden Accuracy (220) | 56.36% | 56.82% | Phase F wins (marginal) |
| Improvement Generalizes? | - | NO | Phase C **wins** |

### Recommendation

**KEEP PHASE C**

The Phase F English-only experiment shows:
- **-4.63pp on test set** (significant degradation)
- **+0.45pp on golden set** (marginal improvement, below 1pp threshold)
- Does not improve generalization

The non-English training examples provide valuable signal that helps the model's English intent classification.

---

## Phase Status

```
PHASE F STATUS: AUDIT COMPLETE
ORIGINAL COMPARISON: INVALID (different test set sizes)
CORRECTED COMPARISON: VALID (same 540 test examples)

Phase C Official Test Accuracy: 71.11% (384/540)
Phase F on SAME 540 Test Set: 66.48% (359/540)

Phase C Golden-Set Accuracy: 56.36% (124/220)
Phase F Golden-Set Accuracy: 56.82% (125/220)

PRODUCTION MODEL CHANGED: NO
RECOMMENDATION: KEEP PHASE C
```

---

*Report generated: 2026-09-12*
*Phase F Fair Comparison Audit*
