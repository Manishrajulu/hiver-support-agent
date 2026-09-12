# Phase 9: Reproducibility Audit Report

## 1. Executive Summary

**Problem Discovered in Phase 8:**
- Phase 8 API implementation discovered that `phase6_best_model.joblib` appeared to produce ~57.2% accuracy instead of the recorded 70.56%

**Root Cause:**
- **EVALUATION CODE BUG** - not model corruption
- The Phase 8/9 evaluation code was only using the FIRST customer turn for classification
- The original Phase 6 training used ALL customer turns concatenated
- When evaluated correctly with ALL customer turns, the model correctly produces **70.56% (381/540)**

**Resolution:**
- Model is verified correct
- Phase 9 freshly trained model also produces **70.56%**
- No changes needed to pipeline or model

---

## 2. Problem Discovered

Phase 8 API implementation found that when evaluating the model offline, accuracy was ~57.2% instead of the recorded 70.56%.

Initial investigation showed:
- `phase6_final_predictions.json`: 381/540 correct (70.56%)
- `phase6_best_model.joblib` evaluation: ~57.2% (309/540)

This discrepancy triggered a full reproducibility audit.

---

## 3. Artifact Inventory

### Model Files

| File | Purpose | Status |
|------|---------|--------|
| `phase6_best_model.joblib` | Phase 6 production model | **CORRECT** - 70.56% verified |
| `phase6_verified_model.joblib` | Phase 9 freshly trained | **CORRECT** - 70.56% verified |
| `baseline_model.joblib` | Original baseline | Corrupted (unreadable) |

### Prediction Files

| File | Purpose | Status |
|------|---------|--------|
| `phase6_final_predictions.json` | Phase 6 predictions | 381/540 correct (70.56%) |
| `phase9_verified_predictions.json` | Phase 9 verification | 381/540 correct (70.56%) |

### Dataset Files

| File | Purpose | Status |
|------|---------|--------|
| `amazonhelp_labeled_conversations_v21_phase6c.jsonl` | Phase 6C cleaned dataset | 2700 examples |
| `baseline_train_test_split.json` | Official train/test split | 2160 train / 540 test |

---

## 4. Test Set Verification

```
Test IDs count: 540
Train IDs count: 2160
Total: 2700

Duplicate test IDs: 0
Duplicate train IDs: 0
Train/Test overlap: 0
v21: Test IDs in dataset: 540/540, Train IDs in dataset: 2160/2160
phase6c: Test IDs in dataset: 540/540, Train IDs in dataset: 2160/2160
```

**Verified:** Test split is valid with no issues.

---

## 5. Model Forensic Inspection

### phase6_best_model.joblib Configuration

| Component | Parameter | Value | Expected |
|-----------|-----------|-------|----------|
| Word TF-IDF | ngram_range | (1, 2) | (1, 2) ✓ |
| Word TF-IDF | max_features | 8000 | 8000 ✓ |
| Word TF-IDF | min_df | 2 | 2 ✓ |
| Word TF-IDF | sublinear_tf | True | True ✓ |
| Char TF-IDF | analyzer | char_wb | char_wb ✓ |
| Char TF-IDF | ngram_range | (3, 6) | (3, 6) ✓ |
| Char TF-IDF | max_features | 8000 | 8000 ✓ |
| Classifier | type | LinearSVC | LinearSVC ✓ |
| Classifier | C | 5.0 | 5.0 ✓ |
| Classifier | class_weight | balanced | balanced ✓ |
| Classifier | random_state | 42 | 42 ✓ |

**Verified:** Model configuration matches Phase 6 documentation exactly.

---

## 6. Historical Phase 6 Configuration

From `phase6_model_comparison.md`:

```
Word TF-IDF:
- ngram_range=(1, 2)
- max_features=8,000
- min_df=2
- max_df=0.95
- sublinear_tf=True

Char TF-IDF:
- analyzer='char_wb'
- ngram_range=(3, 6)
- max_features=8,000
- min_df=2
- max_df=0.95
- sublinear_tf=True

Classifier:
- LinearSVC
- C=5.0
- class_weight='balanced'
- random_state=42

Dataset: amazonhelp_labeled_conversations_v21_phase6c.jsonl
```

---

## 7. Reproduction Experiments

### Experiment 1: Initial Buggy Evaluation (First Turn Only)

```
Accuracy: 309/540 = 0.5722 (57.22%)
```

### Experiment 2: Correct Evaluation (All Customer Turns)

```
Accuracy: 381/540 = 0.7056 (70.56%)
```

### Experiment 3: Fresh Training (Phase 9)

```
Configuration: Exact Phase 6 documented config
Training samples: 2160
Test samples: 540
Accuracy: 381/540 = 0.7056 (70.56%)
```

---

## 8. Comparison Table

| Model | Accuracy | Correct/540 | Configuration | Reproducible? |
|-------|----------|-------------|---------------|---------------|
| A. Recorded Phase 6 | 70.56% | 381/540 | Phase 6 config + phase6c | YES |
| B. Current saved model | 70.56% | 381/540 | Phase 6 config + phase6c | YES |
| C. Fresh Phase 9 model | 70.56% | 381/540 | Exact Phase 6 config | YES |

**All three independently verify 70.56% accuracy.**

---

## 9. Root Cause Analysis

**Initial Finding (Misleading):**
- Model appeared to give ~57% instead of 70.56%

**Investigation Steps:**
1. Verified test split: 540 test IDs, no duplicates, no overlap ✓
2. Inspected model configuration: Matches Phase 6 exactly ✓
3. Trained fresh model: Also gave ~49% initially ❌
4. Discovered text preprocessing bug: Using first turn vs all turns
5. Fixed preprocessing: Fresh model gave 70.56% ✓
6. Re-evaluated phase6_best_model.joblib with correct preprocessing: 70.56% ✓

**Root Cause:**
```
BUGGY EVALUATION CODE - using only FIRST customer turn
instead of ALL customer turns concatenated
```

**Evidence:**
- Original Phase 6 training used `get_customer_text()` which concatenates ALL customer turns
- Phase 8/9 evaluation code only used `turns[0]` (first customer turn)
- When fixed to use ALL customer turns, all models produce 70.56%

---

## 10. Corrective Action

**No changes required to:**
- `phase6_best_model.joblib` - Already correct
- `data/pipeline.py` - Works correctly
- `api.py` - Works correctly
- `test_api.py` - All 8 tests pass

**Added for verification:**
- `data/baseline/phase9_verified_model.joblib` - Freshly trained, 70.56%
- `data/baseline/phase9_verified_predictions.json` - Verification predictions

**Created backup:**
- `data/backup_phase9/` - Empty directory for future backups

---

## 11. Final Verified Accuracy

| Metric | Value |
|--------|-------|
| **Verified Accuracy** | **70.56% (381/540)** |
| Historical Recorded | 70.56% (381/540) |
| Match | YES |
| Train/Test Leakage | 0 |
| Test Set Size | 540 |

---

## 12. Difference Between Historical and Verified

| Aspect | Historical | Verified | Difference |
|--------|------------|----------|------------|
| Accuracy | 70.56% | 70.56% | 0pp |
| Model | phase6_best_model.joblib | phase9_verified_model.joblib | Same accuracy |
| Predictions | 381/540 correct | 381/540 correct | Identical |

**No difference - results are identical.**

---

## 13. Model Artifact Used by API

The API (`api.py`) uses `data/pipeline.py` which loads `phase6_best_model.joblib`.

**Verified correct:** The API produces 70.56% accuracy when:
1. Using ALL customer turns concatenated (correct text preprocessing)
2. Using the Phase 6 model configuration
3. Evaluating on the official 540-example test set

---

## 14. Test Results

### API Tests (test_api.py)

```
8/8 PASSED

TestHealthEndpoint:
  PASS: test_health_returns_success

TestPredictEndpoint:
  PASS: test_empty_message_rejected
  PASS: test_escalate_decision
  PASS: test_missing_message_rejected
  PASS: test_predict_returns_structure

TestPhase6ModelIntegration:
  PASS: test_model_uses_phase6_classifier

TestResponseSchema:
  PASS: test_confidence_in_range

TestAPIKeySecurity:
  PASS: test_api_key_not_in_response
```

### Pipeline Verification

```
Accuracy: 381/540 = 0.7056 (70.56%)
Match with historical: YES
```

---

## 15. Train/Test Leakage Analysis

```
Train IDs: 2160
Test IDs: 540
Overlap: 0
Duplicates in test: 0
Duplicates in train: 0
```

**Verified: No train/test leakage.**

---

## 16. Final Recommendation

### Status: PASS

**Findings:**
1. The Phase 6 model (70.56%) was correctly implemented
2. No model corruption or reproducibility issue exists
3. The apparent discrepancy was caused by buggy evaluation code
4. All three independent evaluations confirm 70.56% accuracy

**No changes needed to:**
- Model files
- Pipeline
- API
- Backend

**No modifications to production artifacts.**

### Commands Used to Verify

```bash
# Verify model accuracy
python -c "
from data.pipeline import load_components, classify
import json
...evaluate on 540 test examples...
"

# Fresh model training (Phase 9)
python -c "
...retrain with exact Phase 6 config...
"
# Result: 70.56% (381/540)

# API tests
python test_api.py
# Result: 8/8 PASSED
```

---

## 17. Files Created/Modified

| File | Action | Description |
|------|--------|-------------|
| `data/baseline/phase9_verified_model.joblib` | Created | Freshly trained model, 70.56% |
| `data/baseline/phase9_verified_predictions.json` | Created | Verification predictions |
| `data/backup_phase9/` | Created | Backup directory |

**No production files modified.**

---

## 18. Conclusion

**The Phase 6 model is verified correct at 70.56% accuracy.**

The apparent reproducibility issue was a false alarm caused by evaluation code that only used the first customer turn instead of all customer turns concatenated.

**Ready to proceed to Phase 10 (Frontend Integration).**

---

*Report generated: 2026-09-11*
*Phase 9 Reproducibility Audit: COMPLETE*
