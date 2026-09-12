# Phase 10: Model Optimization Report

## 1. Executive Summary

**Objective:** Determine if the verified 70.56% baseline classifier can be improved.

**Result:** Marginal improvements found (+0.18pp), but within acceptable noise threshold. **70.56% remains the production baseline.**

---

## 2. Protected Baseline Configuration

| Component | Parameter | Value |
|-----------|-----------|-------|
| Word TF-IDF | ngram_range | (1, 2) |
| Word TF-IDF | max_features | 8,000 |
| Word TF-IDF | min_df | 2 |
| Word TF-IDF | max_df | 0.95 |
| Word TF-IDF | sublinear_tf | True |
| Char TF-IDF | analyzer | char_wb |
| Char TF-IDF | ngram_range | (3, 6) |
| Char TF-IDF | max_features | 8,000 |
| Char TF-IDF | min_df | 2 |
| Char TF-IDF | max_df | 0.95 |
| Char TF-IDF | sublinear_tf | True |
| Classifier | type | LinearSVC |
| Classifier | C | 5.0 |
| Classifier | class_weight | balanced |
| Dataset | version | phase6c |
| Text Prep | method | ALL customer turns concatenated |

**Baseline Accuracy:** 70.56% (381/540)

---

## 3. Baseline Reproduction

| Metric | Value |
|--------|-------|
| Reproduced Accuracy | 70.56% (381/540) |
| Historical Recorded | 70.56% (381/540) |
| Match | YES |
| Train/Test Overlap | 0 |
| Test Size | 540 |

**Verified:** Baseline reproduction matches exactly.

---

## 4. Experiments Performed

### A. Word TF-IDF Variations

| Configuration | Accuracy | Delta |
|--------------|----------|-------|
| (1,1,8k) | 65.37% | -5.19pp |
| (1,3,8k) | 69.63% | -0.93pp |
| (1,2,6k) | 69.26% | -1.30pp |
| (1,2,10k) | 69.63% | -0.93pp |
| (1,2,12k) | 70.00% | -0.56pp |
| (1,2,8k) no sub | 69.81% | -0.75pp |
| min_df=1 | 69.63% | -0.93pp |
| min_df=3 | 70.00% | -0.56pp |
| min_df=5 | 69.07% | -1.49pp |

**Finding:** (1,2,8k) remains optimal for word features.

### B. Char TF-IDF Variations

| Configuration | Accuracy | Delta |
|--------------|----------|-------|
| (3,5,8k) | 70.19% | -0.37pp |
| (4,6,8k) | 68.70% | -1.86pp |
| (4,7,8k) | 69.81% | -0.75pp |
| (3,6,6k) | 70.56% | 0.00pp |
| (3,6,10k) | 70.19% | -0.37pp |
| (3,6,12k) | 69.81% | -0.75pp |
| (3,6,8k) no sub | 70.00% | -0.56pp |
| min_df=1 | **70.74%** | **+0.18pp** |
| min_df=3 | 70.56% | 0.00pp |

**Finding:** char min_df=1 shows marginal improvement (+0.18pp).

### C. Classifier C Variations

| C Value | Accuracy | Delta |
|---------|----------|-------|
| 0.5 | 69.63% | -0.93pp |
| 1.0 | 70.00% | -0.56pp |
| 2.0 | 70.00% | -0.56pp |
| 3.0 | 70.56% | 0.00pp |
| 5.0 | 70.56% | 0.00pp (baseline) |
| 7.5 | 70.56% | 0.00pp |
| 10.0 | **70.74%** | **+0.18pp** |

**Finding:** C=10 shows marginal improvement (+0.18pp).

### D. Combined Experiments

| Configuration | Accuracy | Delta |
|--------------|----------|-------|
| (1,2,8k)+(3,6,8k) C=10 | **70.74%** | **+0.18pp** |
| (1,2,8k)+(3,6,8k) char_min1 | **70.74%** | **+0.18pp** |
| (1,2,8k)+(3,6,8k) char_min1 C=10 | 70.37% | -0.19pp |
| Others | <70.56% | negative |

**Finding:** Combined variations do not improve beyond individual bests.

### E. Alternative Classifiers

| Classifier | Accuracy | Delta |
|------------|----------|-------|
| LinearSVC (baseline) | 70.56% | 0.00pp |
| LogisticRegression C=1.0 | 65.56% | -5.00pp |
| LogisticRegression C=0.5 | 61.67% | -8.89pp |

**Finding:** LinearSVC is substantially better than LogisticRegression for this task.

---

## 5. Complete Experiment Comparison Table

| Rank | Configuration | Accuracy | Correct/540 | Delta |
|------|---------------|----------|-------------|-------|
| 1 | (1,2,8k)+(3,6,8k) C=10 | 70.74% | 382/540 | +0.18pp |
| 1 | (1,2,8k)+(3,6,8k) char_min1 | 70.74% | 382/540 | +0.18pp |
| 3 | Baseline (1,2,8k)+(3,6,8k) C=5 | 70.56% | 381/540 | 0.00pp |
| 3 | (3,6,8k) min_df=3 | 70.56% | 381/540 | 0.00pp |
| 3 | (1,2,8k)+(3,6,8k) C=7.5 | 70.56% | 381/540 | 0.00pp |
| ... | (all others) | <70.56% | <381 | negative |

---

## 6. Best Configuration Found

**Marginal Improvement Candidates:**

1. **C=10:** 70.74% (382/540) - +0.18pp
2. **char min_df=1:** 70.74% (382/540) - +0.18pp

Both consistently produce 382/540 across multiple runs.

---

## 7. Accuracy Comparison

| Model | Accuracy | Correct/540 | Delta vs Baseline |
|-------|----------|-------------|-------------------|
| Original Baseline | 54.44% | 294/540 | - |
| Phase 3A | 57.22% | 309/540 | +2.78pp |
| Phase 4 | 69.07% | 373/540 | +14.63pp |
| Phase 6 | 70.56% | 381/540 | +16.12pp |
| **Phase 10 Best** | **70.74%** | **382/540** | **+16.30pp** |

---

## 8. Confusion/Error Analysis

### Top Confusion Pairs (Baseline)

| Actual → Predicted | Count |
|-------------------|-------|
| APP_USAGE → OTHER | 14 |
| DELIVERY_LATE → OTHER | 13 |
| DEVICE_ISSUE → OTHER | 9 |
| DELIVERY_LATE → RETURN_REQUEST | 6 |
| DELIVERY_MISSING → DELIVERY_LATE | 6 |
| ORDER_STATUS → OTHER | 6 |
| ACCOUNT_ACCESS → OTHER | 5 |

### Per-Intent Performance (Baseline)

| Intent | Precision | Recall | F1-Score | Support |
|--------|-----------|--------|----------|---------|
| ACCOUNT_ACCESS | 0.33 | 0.29 | 0.31 | 7 |
| APP_USAGE | 0.66 | 0.48 | 0.55 | 44 |
| DELIVERY_LATE | 0.75 | 0.70 | 0.72 | 109 |
| DELIVERY_MISSING | 0.68 | 0.56 | 0.61 | 34 |
| DEVICE_ISSUE | 0.73 | 0.56 | 0.63 | 34 |
| ORDER_STATUS | 0.67 | 0.37 | 0.48 | 27 |
| OTHER | 0.74 | 0.92 | 0.82 | 183 |
| ... | ... | ... | ... | ... |

**Key Finding:** Most errors are due to taxonomic ambiguity (APP_USAGE/DELIVERY_LATE/DEVICE_ISSUE confused with OTHER) and low support for minority classes.

---

## 9. Reproducibility Verification

| Configuration | Run 1 | Run 2 | Run 3 | Avg |
|---------------|-------|-------|-------|-----|
| Baseline (C=5) | 381 | 381 | 381 | 381.0 |
| C=10 | 382 | 382 | 382 | 382.0 |
| char min_df=1 | 382 | 382 | 382 | 382.0 |

**Finding:** Improvements are consistent, not noisy.

---

## 10. Leakage Verification

| Check | Result |
|-------|--------|
| Train IDs | 2160 |
| Test IDs | 540 |
| Train/Test Overlap | 0 |
| Duplicate Test IDs | 0 |
| Duplicate Train IDs | 0 |

**Verified:** No data leakage.

---

## 11. Final Recommendation

### Decision Rule Application

Based on the model selection rules:

1. **Improvement threshold:** The best improvement is +0.18pp (382/540 vs 381/540)
2. **Threshold is ~0.5pp:** +0.18pp < +0.5pp
3. **Conclusion:** Do NOT replace production model automatically

### Recommendation

**RETAIN PHASE 6 MODEL (70.56%)**

Rationale:
- Improvement is only +0.18pp (+1 example out of 540)
- Well below the 0.5pp decision threshold
- The improvement is consistent but marginal
- The baseline is already highly optimized
- Further improvement would require fundamentally different approaches (more data, different features, deep learning, etc.)
- Risk of overfitting to test set by chasing marginal gains

### Why 70.56% is Strong

- +16.12pp improvement over original baseline (54.44%)
- Phase 4 already showed sentence embeddings performed substantially worse
- Remaining errors are primarily taxonomic ambiguity and low-support classes
- The model is at a plateau where incremental gains are not reliable

---

## 12. Files Created

| File | Description |
|------|-------------|
| `data/backup_phase10/` | Backup directory (empty - no model changes) |
| `data/baseline/phase10_model_optimization_report.md` | This report |

**No new model files created** - improvement not significant enough to warrant production change.

---

## 13. Historical Progression

| Phase | Model | Accuracy | Delta |
|-------|-------|----------|-------|
| Original | TF-IDF + LR | 54.44% | - |
| Phase 3A | TF-IDF + LR (cleaned) | 57.22% | +2.78pp |
| Phase 4 | Word+Char TF-IDF + LinearSVC | 69.07% | +14.63pp |
| Phase 6 | Optimized LinearSVC | **70.56%** | +16.12pp |
| Phase 10 | Further tuning attempt | 70.74% | +16.30pp |

**Final Production Model:** Phase 6 (70.56%) - No change warranted

---

## 14. Conclusion

**70.56% remains the strongest verified classifier and further optimization is not justified at this stage.**

The Phase 10 optimization experiments confirm that:
1. The baseline is near-optimal for classical TF-IDF + LinearSVC approach
2. Marginal improvements (+0.18pp) exist but are below the significance threshold
3. The model has reached a performance plateau
4. Further significant improvement would require fundamentally different approaches

**The verified Phase 6 model at 70.56% accuracy is production-ready.**

---

*Report generated: 2026-09-11*
*Phase 10 Model Optimization: COMPLETE*
