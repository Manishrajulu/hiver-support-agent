# Architecture/Implementation Plan: Phase 7 Integration

## Current Project State

### What Exists
1. **Pipeline** (`data/pipeline.py`) - integrates classifier + RAG + Groq + escalation
2. **Old classifier** (`baseline_model.joblib`) - TF-IDF + LogisticRegression, ~57% accuracy
3. **New Phase 6 classifier** (`phase6_best_model.joblib`) - Word+Char TF-IDF + LinearSVC, **70.56% accuracy**
4. **RAG index** - sentence-transformers + FAISS, built from training data
5. **Escalation policy** - rule-based with confidence thresholds

### Critical Issue
**The Phase 6 model (LinearSVC) does NOT output probabilities** via `predict_proba`.
- Current pipeline uses `classifier.predict_proba()` for confidence
- LinearSVC uses `decision_function()` which returns raw margins
- **Integration requires confidence computation modification**

---

## Assignment Requirements (from Sprint Roadmap)

| Requirement | Status |
|-------------|--------|
| Runnable pipeline | Exists but uses old model |
| README with reproduction | Needs update |
| 150-250 golden evaluation examples | Not verified |
| Evaluation harness + LLM-as-judge | Partial |
| Final report | Phases 0-6 done |
| Decision log | Partial |

---

## Analysis: Is RAG Actually Required?

### Phase 5 Error Analysis Findings

The 159 remaining errors (29.4%) are distributed as:
- ~55 genuine model errors (model prediction wrong)
- ~19 wrong labels (model was correct)
- ~35 ambiguous cases
- ~30 taxonomy issues (boundary confusion)
- ~10 representation limitations

**Conclusion: RAG does NOT solve these errors.**

RAG retrieves similar historical cases by semantic embedding similarity. The errors are:
1. **Classification errors** - wrong intent predicted
2. **Label noise** - human label may be wrong
3. **Taxonomy ambiguity** - boundaries unclear
4. **Representation limits** - TF-IDF can't capture semantic nuance

None of these are solved by retrieving similar cases. RAG would only help if:
- The error was caused by **lack of domain knowledge** (not applicable)
- The system needed **specific policy information** (retrieved cases provide this)

### RAG Role Clarification

RAG is useful for **reply generation** (Stage 3), not for **intent classification**:
- RAG provides evidence for generating grounded replies
- RAG does NOT improve classification accuracy
- RAG may help AUTO_HANDLE decisions by providing similar cases

**Recommendation: Keep RAG for reply generation, but recognize its limitations.**

---

## Proposed Architecture

### Option A: Minimal Update (Recommended)

Update the pipeline to use the Phase 6 classifier with margin-based confidence.

```
Customer conversation text
        ↓
Stage 1: Classification (Word+Char TF-IDF + LinearSVC)
        ↓
        → Intent + Margin Score
        ↓
Stage 2: RAG Retrieval (sentence-transformers + FAISS)
        ↓
        → Top-5 similar cases + similarity scores
        ↓
Stage 3: Reply Generation (Groq) - ONLY if AUTO_HANDLE
        ↓
Stage 4: Escalation Decision (margin-based thresholds)
        ↓
Structured JSON response
```

**Changes Required:**
1. Replace `baseline_model.joblib` with `phase6_best_model.joblib`
2. Replace `predict_proba` with `decision_function` for confidence
3. Calibrate margin-to-confidence mapping
4. Update escalation thresholds for LinearSVC margins

### Option B: Full Redesign

Remove RAG, simplify to: Classify → Generate → Escalate.

**Not recommended** - RAG provides value for reply generation even if not for classification.

---

## Implementation Tasks

### Task 1: Update Pipeline for Phase 6 Model

**Files to modify:** `data/pipeline.py`

**Changes:**

1. **Confidence computation** (replace lines 208-211):
```python
# OLD (LogisticRegression):
proba = classifier.predict_proba([conversation_text])[0]
predicted_class = classifier.classes_[np.argmax(proba)]
confidence = float(np.max(proba))

# NEW (LinearSVC):
decision_scores = classifier.decision_function([conversation_text])[0]
predicted_idx = np.argmax(decision_scores)
predicted_class = classifier.classes_[predicted_idx]
# Convert margin to 0-1 confidence-like score using sigmoid
margin = decision_scores[predicted_idx]
confidence = float(1 / (1 + np.exp(-margin)))  # Sigmoid
```

2. **Escalation thresholds** - calibrate for LinearSVC margins:
- Current: `CONF_THRESHOLD = 0.25`
- Need to calibrate based on margin distribution

3. **HIGH_RISK intents** - update to remove ORDER_MODIFY (now has 0 test examples):
```python
HIGH_RISK_INTENTS = {
    'REFUND_REQUEST',
    'PAYMENT_ISSUE',
    'ACCOUNT_ACCESS',
    # ORDER_MODIFY removed - only 2 training examples, 0 test
}
```

### Task 2: Update RAG Index (Optional)

The current RAG index was built from the Phase 3A dataset. Since we applied 6 label fixes (Phase 6C), the RAG corpus metadata is now slightly stale. However, this is a minor issue since:
- Only 6 out of 2160 training examples changed
- Impact on retrieval is negligible

**Skip unless retrieval quality degrades noticeably.**

### Task 3: Verify Evaluation Harness

**Check existing files:**
- `data/evaluation/sprint5_classification_metrics.json`
- `data/evaluation/sprint6_test_report.json`

**Need to verify:**
- 150-250 golden evaluation examples exist
- LLM-as-judge evaluation completed
- Human agreement evidence documented

### Task 4: Update Documentation

**Files to update:**
- README.md - reproduction instructions for Phase 6 model
- Decision log - document Phase 4-6 decisions

---

## Escalation Threshold Analysis

### Current Thresholds (designed for LogisticRegression)

| Threshold | Current Value | Applies To |
|-----------|---------------|-----------|
| CONF_THRESHOLD | 0.25 | confidence from predict_proba |
| SIM_THRESHOLD | 0.30 | avg retrieval similarity |

### LinearSVC Margin Distribution

From Phase 6 evaluation:
- Min margin: 0.003
- Max margin: 4.146
- Mean margin: 0.768
- Median margin: 0.603

### Proposed New Thresholds

| Threshold | Old Value | New Value (margin) | New Value (sigmoid) |
|-----------|-----------|-------------------|---------------------|
| CONF_THRESHOLD | 0.25 | ~0.50 | 0.62 |
| SIM_THRESHOLD | 0.30 | unchanged | unchanged |

**Note**: Need to run validation to confirm exact threshold.

---

## What RAG Actually Provides

### Retrieval Quality (from Sprint 5)
- Top-1 Match: 38.7%
- Top-5 Match: 73.9%
- Avg Top-1 Similarity: 0.718

### RAG Value for Reply Generation
- Provides similar cases with same/similar intent
- Enables evidence-grounded replies
- Reduces hallucination risk

### RAG Limitations
- Does NOT improve classification
- Does NOT fix label errors
- Does NOT resolve taxonomy ambiguity

---

## Implementation Sequence

1. **Update pipeline.py** for LinearSVC compatibility
2. **Calibrate escalation thresholds** using validation set
3. **Test updated pipeline** with 50 test conversations
4. **Verify evaluation harness** completeness
5. **Update documentation**
6. **Final integration test**

---

## Optional: RAG Rebuild Check

The Phase 6C label fixes changed 6 training examples. To rebuild RAG:

```python
# Would require:
# 1. Load updated dataset (phase6c)
# 2. Extract customer text for training records
# 3. Generate embeddings with sentence-transformers
# 4. Build FAISS index
# 5. Save to data/rag/
```

**Estimated time**: 5-10 minutes for 2160 records.

**Recommendation**: Skip unless retrieval quality degrades noticeably.

---

## Deliverables Checklist

| Deliverable | Status | Action Needed |
|-------------|--------|--------------|
| Runnable pipeline | Partial | Update to use Phase 6 model |
| README reproduction | Partial | Update model path + commands |
| 150-250 golden examples | Unknown | Verify count + quality |
| LLM-as-judge eval | Partial | Verify completion |
| Human agreement evidence | Unknown | Verify exists |
| Final report | Partial | Complete |
| Decision log | Partial | Update |

---

## Recommendation

### Proceed with Option A: Minimal Update

1. **Update pipeline.py** to use Phase 6 model with margin-based confidence
2. **Keep RAG** - useful for reply generation
3. **Calibrate thresholds** for LinearSVC margins
4. **Verify evaluation harness** completeness
5. **Do NOT implement RAG rebuild** - not needed

### Why Not Option B (Remove RAG)?
- RAG provides value for reply generation
- Sprint 5 showed 73.9% Top-5 intent match
- Reply generation benefits from similar cases
- Removing RAG would require significant pipeline redesign

### Why Not More Changes?
- Phase 5 error analysis shows remaining errors are primarily classification/taxonomy issues
- Further model improvements show diminishing returns (+1.49pp from Phase 4 to Phase 6)
- RAG doesn't solve the identified error types

---

*Plan prepared: 2026-09-11*
*等待批准后实施*
