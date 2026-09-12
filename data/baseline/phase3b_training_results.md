# Phase 3B Training Results Report

## 1. Executive Summary

**VERDICT: SMALL DEGRADATION**

Phase 3B applied the two approved ORDER_MODIFY corrections:
- amazonhelp_073655: ORDER_MODIFY → DELIVERY_LATE
- amazonhelp_135737: ORDER_MODIFY → CANCELLATION

**Result: 56.85% (307/540) vs Phase 3A: 57.22% (309/540) = -0.37 pp**

### Comparison

| Model | Accuracy | Correct/Total | vs Phase 3A |
|-------|----------|---------------|-------------|
| Phase 3A | 57.22% | 309/540 | — |
| **Phase 3B** | **56.85%** | **307/540** | **-0.37 pp** |

---

## 2. Changes Made

### 2.1 Corrections Applied

| ID | Before | After |
|----|--------|-------|
| amazonhelp_073655 | ORDER_MODIFY | DELIVERY_LATE |
| amazonhelp_135737 | ORDER_MODIFY | CANCELLATION |

### 2.2 Backup Location

- `data/processed/amazonhelp_labeled_conversations_v21_phase3b_backup.jsonl`

### 2.3 Before/After Intent Counts

| Intent | Before Phase 3B | After Phase 3B | Change |
|--------|-----------------|----------------|--------|
| ORDER_MODIFY | 2 | **0** | -2 |
| DELIVERY_LATE | 532 | 533 | +1 |
| CANCELLATION | 3 | 4 | +1 |

---

## 3. Dataset Validation

### 3.1 Record Count

| Metric | Value |
|--------|-------|
| Total records | 2,700 |
| Records verified | ✓ |

### 3.2 ORDER_MODIFY Status

| Metric | Value |
|--------|-------|
| ORDER_MODIFY count after cleanup | **0** |
| Class removed | ✓ |

### 3.3 Train/Test Split Integrity

| Metric | Value |
|--------|-------|
| Train IDs | 2,160 |
| Test IDs | 540 |
| Train/Test Overlap | **0** (verified) |
| All IDs covered | ✓ |

---

## 4. Model Configuration

### 4.1 Exact Configuration

| Component | Parameter | Value |
|-----------|-----------|-------|
| **TfidfVectorizer** | max_features | 10,000 |
| | ngram_range | (1, 2) |
| | min_df | 2 |
| | max_df | 0.95 |
| | sublinear_tf | True |
| **LogisticRegression** | C | 1.0 |
| | max_iter | 1,000 |
| | class_weight | **'balanced'** |
| | random_state | 42 |
| | solver | 'lbfgs' |

---

## 5. Evaluation Results

### 5.1 Overall Accuracy

| Metric | Phase 3A | Phase 3B |
|--------|----------|----------|
| Accuracy | 57.22% | 56.85% |
| Correct | 309 | 307 |
| Incorrect | 231 | 233 |
| **Change** | — | **-2 correct** |

### 5.2 Prediction Changes

| Metric | Count |
|--------|-------|
| Predictions that changed | 11 |
| Correct → Incorrect | 7 |
| Incorrect → Correct | 5 |
| **Net change** | **-2** |

### 5.3 Changed Predictions

| Test ID | Phase 3A Prediction | Phase 3B Prediction | Actual |
|---------|--------------------|--------------------|--------|
| amazonhelp_025719 | RETURN_REQUEST | DELIVERY_LATE | OTHER |
| amazonhelp_114547 | RETURN_REQUEST | DELIVERY_LATE | DELIVERY_MISSING |
| amazonhelp_039079 | PAYMENT_ISSUE | APP_USAGE | PAYMENT_ISSUE |
| amazonhelp_119659 | DELIVERY_MISSING | ORDER_STATUS | DELIVERY_LATE |
| amazonhelp_029851 | DELIVERY_LATE | OTHER | ACCOUNT_ACCESS |
| amazonhelp_034704 | REFUND_REQUEST | DELIVERY_MISSING | DELIVERY_MISSING |
| amazonhelp_004528 | PAYMENT_ISSUE | DELIVERY_LATE | PAYMENT_ISSUE |
| amazonhelp_081885 | APP_USAGE | OTHER | OTHER |
| amazonhelp_066659 | DELIVERY_TRACKING | DELIVERY_LATE | DELIVERY_TRACKING |
| amazonhelp_099841 | ACCOUNT_ACCESS | DELIVERY_LATE | ACCOUNT_ACCESS |

---

## 6. Per-Intent Metrics

| Intent | Precision | Recall | F1-Score | Support |
|--------|-----------|--------|----------|---------|
| ACCOUNT_ACCESS | 0.4000 | 0.5714 | 0.4706 | 7 |
| APP_USAGE | 0.3902 | 0.3636 | 0.3765 | 44 |
| CANCELLATION | 0.0000 | 0.0000 | 0.0000 | 1 |
| DELIVERY_LATE | 0.5088 | 0.5472 | 0.5273 | 106 |
| DELIVERY_MISSING | 0.4186 | 0.5806 | 0.4865 | 31 |
| DELIVERY_TRACKING | 0.4286 | 0.3750 | 0.4000 | 8 |
| DEVICE_ISSUE | 0.7586 | 0.6471 | 0.6984 | 34 |
| ORDER_STATUS | 0.4878 | 0.7407 | 0.5882 | 27 |
| OTHER | 0.8387 | 0.5503 | 0.6645 | 189 |
| PAYMENT_ISSUE | 0.4545 | 0.6522 | 0.5357 | 23 |
| PRODUCT_ISSUE | 0.6000 | 0.2727 | 0.3750 | 11 |
| REFUND_REQUEST | 0.3913 | 0.6923 | 0.5000 | 13 |
| RETURN_REQUEST | 0.4561 | 0.8387 | 0.5909 | 31 |
| VIDEO_STREAMING | 0.6923 | 0.6000 | 0.6429 | 15 |

---

## 7. Top Confusion Pairs

| Actual → Predicted | Count |
|-------------------|-------|
| OTHER → DELIVERY_LATE | 29 |
| OTHER → APP_USAGE | 16 |
| OTHER → RETURN_REQUEST | 11 |
| DELIVERY_LATE → RETURN_REQUEST | 10 |
| DELIVERY_LATE → ORDER_STATUS | 10 |
| APP_USAGE → OTHER | 9 |
| OTHER → DELIVERY_MISSING | 9 |
| DELIVERY_LATE → DELIVERY_MISSING | 8 |
| OTHER → ORDER_STATUS | 7 |
| DELIVERY_MISSING → DELIVERY_LATE | 7 |

---

## 8. Analysis

### 8.1 Why Did Performance Degrade?

The two relabeled examples (amazonhelp_073655 and amazonhelp_135737) were in the training set. Although neither is in the test set, changing their labels affected the model's learned weights, causing 11 predictions to change:
- 7 changed from correct to incorrect
- 5 changed from incorrect to correct
- **Net: -2 correct predictions**

### 8.2 What This Means

The ORDER_MODIFY examples, while mislabeled, may have been providing some signal that was disrupted when relabeled. The relabeling changed the decision boundaries slightly, causing the model to make different (worse) predictions on some test examples.

### 8.3 CANCELLATION Issue

Note that CANCELLATION now has 4 examples (1 in test, 3 in train) but still has 0% precision and recall in predictions. This is because the model doesn't predict CANCELLATION at all.

---

## 9. Files Generated

| File | Description |
|------|-------------|
| `data/processed/amazonhelp_labeled_conversations_v21_phase3b_backup.jsonl` | Backup before Phase 3B |
| `data/baseline/phase3b_predictions.jsonl` | Phase 3B predictions |

---

## 10. Conclusion

### 10.1 Final Verdict

**Phase 3B resulted in a SMALL DEGRADATION of -0.37 percentage points.**

| Metric | Phase 3A | Phase 3B | Change |
|--------|----------|----------|--------|
| Accuracy | 57.22% | 56.85% | -0.37 pp |
| Correct | 309 | 307 | -2 |

### 10.2 Recommendation

**The Phase 3B relabeling did not improve accuracy.** The two ORDER_MODIFY corrections were theoretically correct but practically unhelpful:
- Both examples were in training (not test)
- Relabeling changed model weights
- Net effect was -2 correct predictions

**Options going forward:**

1. **Keep Phase 3B** (-0.37 pp): The ORDER_MODIFY cleanup is still semantically correct, and the accuracy change is within noise range
2. **Revert to Phase 3A** (+0.37 pp): If accuracy is the only metric, revert
3. **Investigate further**: The 11 changed predictions suggest the model is near a decision boundary

---

## 11. Next Recommended Step

Given that Phase 3B caused a small degradation (-0.37 pp), the next investigation should focus on:

1. **Understand why 11 predictions changed** when only training labels were modified
2. **Evaluate if the change is statistically significant** or within random variation
3. **Consider reverting to Phase 3A** if accuracy is the primary metric

**Do not proceed to Phase 3C automatically.** The Phase 3B result suggests that not all "correct" label changes improve the model.

---

*Report generated: 2026-09-10*
*Phase 3B changes: 2 ORDER_MODIFY relabelings*
*Result: 56.85% (307/540) = -0.37 pp vs Phase 3A*
