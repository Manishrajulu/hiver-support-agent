# Final Classifier Decision Report

## Dataset Information
- **Dataset**: `amazonhelp_labeled_conversations_v21.jsonl`
- **Total conversations**: 2700
- **Train split**: 2160 (80%)
- **Test split**: 540 (20%)
- **Random state**: 42 (stratified)
- **Label source**: Rule-based (v2.1) - NOT human-verified

## Label Quality Warning
The labels used for training and evaluation are **rule-based**, not human-annotated ground truth.
- Earlier manual review found ~43.5% error rate in rule-based labels
- The 200-conversation validation set (`amazonhelp_200_validation.jsonl`) has labels from Groq LLM, not human verification
- **We cannot claim true model accuracy without human-annotated ground truth**

---

## Models Evaluated

### 1. Majority Baseline
| Metric | Value |
|--------|-------|
| Accuracy | 37.59% |
| Macro F1 | 0.039 |
| Weighted F1 | 0.205 |

### 2. TF-IDF + Logistic Regression (Baseline)
| Metric | Value |
|--------|-------|
| Accuracy | **56.30%** |
| Macro F1 | **0.507** |
| Weighted F1 | **0.560** |

### 3. Groq LLM (allam-2-7b)
| Metric | Value |
|--------|-------|
| Accuracy | 19.44% |
| Macro F1 | 0.229 |
| Weighted F1 | 0.223 |

### 4. Groq Prompt Experiment (100-case subset)
| Metric | Value |
|--------|-------|
| Original prompt accuracy | 19.00% |
| Improved prompt accuracy | 9.00% (all 100) / 13.85% (65 valid) |
| Rate limit failures | 35/100 |

---

## Confusion Analysis (TF-IDF + LR)

### Per-Intent F1 Scores
| Intent | F1 | Support |
|--------|-----|---------|
| DELIVERY_TRACKING | 0.667 | 8 |
| DEVICE_ISSUE | 0.667 | 34 |
| RETURN_REQUEST | 0.658 | 31 |
| OTHER | 0.630 | 203 |
| REFUND_REQUEST | 0.606 | 13 |
| ORDER_STATUS | 0.586 | 26 |
| PAYMENT_ISSUE | 0.566 | 23 |
| VIDEO_STREAMING | 0.563 | 14 |
| DELIVERY_MISSING | 0.563 | 29 |
| DELIVERY_LATE | 0.493 | 96 |
| ACCOUNT_ACCESS | 0.500 | 6 |
| PRODUCT_ISSUE | 0.333 | 11 |
| APP_USAGE | 0.267 | 44 |
| ORDER_MODIFY | 0.000 | 2 |

### Top Confusions (Baseline)
| Actual → Predicted | Count |
|---------------------|-------|
| OTHER → DELIVERY_LATE | 39 |
| APP_USAGE → OTHER | 15 |
| DELIVERY_LATE → OTHER | 13 |

### Observations
1. **OTHER** is the largest class (203/540 = 37.6%) - model handles it reasonably (F1=0.630)
2. **ORDER_MODIFY** has only 2 test samples and 0 predictions - too rare to evaluate
3. **APP_USAGE** has low F1 (0.267) despite 44 samples - confused with OTHER
4. **DELIVERY_LATE** is often confused with OTHER (39 cases)

---

## Train/Test Split Validation
- **Method**: Stratified 80/20 split, random_state=42
- **No data leakage**: Model is trained only on train_ids, evaluated only on test_ids
- **Reproducible**: Same split used for all experiments

---

## Known Limitations

1. **Labels are rule-based, not human-verified**
   - Actual model accuracy on human intent is unknown
   - We are evaluating against imperfect rules, not ground truth

2. **No cross-validation performed**
   - Single train/test split only
   - Results may vary with different splits

3. **Groq LLM experiment is inconclusive**
   - Rate limiting (429 errors) affected the prompt experiment
   - The improved prompt did NOT reduce ORDER_STATUS over-prediction

4. **TF-IDF + LR has poor performance on rare intents**
   - ORDER_MODIFY (2 samples), PRODUCT_ISSUE (11), ACCOUNT_ACCESS (6)
   - F1 scores for rare intents are unreliable

---

## Best-Supported Classifier

**TF-IDF + Logistic Regression** is the best-supported classifier based on available evidence.

### Why TF-IDF + LR was selected:
1. **Highest accuracy**: 56.30% vs 37.59% (majority) vs 19.44% (Groq)
2. **Highest Macro F1**: 0.507 vs 0.039 (majority) vs 0.229 (Groq)
3. **Highest Weighted F1**: 0.560 vs 0.205 (majority) vs 0.223 (Groq)
4. **Stable**: Same test set used for all comparisons
5. **Reproducible**: Deterministic split and model

### Why Groq was NOT selected:
- Groq accuracy (19.44%) is **below** majority baseline (37.59%)
- Groq prompt experiment showed no improvement
- Rate limiting makes Groq unreliable for large-scale deployment

---

## What Should NOT Be Done Next

1. **Do NOT claim TF-IDF + LR has 56% true accuracy** - labels are rule-based, not human ground truth
2. **Do NOT deploy Groq as the classifier** - performance is worse than majority baseline
3. **Do NOT create another rule version (V3/V4/V5)** - we have spent too much time on deterministic rules
4. **Do NOT modify the taxonomy** - no evidence the taxonomy is broken
5. **Do NOT run another large Groq experiment** - rate limiting is a blocker
6. **Do NOT use 200-validation set as ground truth** - it was labeled by Groq LLM

---

## What Must Be Frozen Before Moving Forward

1. **Classifier**: `data/baseline/baseline_model.joblib` (TF-IDF + Logistic Regression)
2. **Train/test split**: `data/baseline/baseline_train_test_split.json`
3. **Metrics**: Accuracy 56.30%, Macro F1 0.507, Weighted F1 0.560
4. **Label source**: Rule-based v2.1 (NOT human-verified)

---

## Artifact for Next Sprint

**File**: `data/baseline/baseline_model.joblib`

**Usage**:
```python
import joblib
model = joblib.load('data/baseline/baseline_model.joblib')
prediction = model.predict([customer_text])
```

---

## Final Status

CLASSIFICATION STAGE:
- **Status**: READY (with caveats)
- **Selected classifier**: TF-IDF + Logistic Regression
- **Accuracy**: 56.30% (on rule-based labels, not human-verified)
- **Macro F1**: 0.507
- **Weighted F1**: 0.560
- **Main limitation**: Labels are rule-based, not human ground truth; actual accuracy on true human intent is unknown
- **Artifact to use**: `data/baseline/baseline_model.joblib`
- **Next stage**: RAG / Reply Generation (after accepting the 56.30% is on imperfect labels)

---

*Report generated: 2026-09-10*
