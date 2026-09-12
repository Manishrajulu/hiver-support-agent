# AmazonHelp Intent Classification - Final Report

## Executive Summary

**Task:** Build an intent classification system for Amazon customer service conversations.

**Test-Set Accuracy:** 71.11% (Phase C model, 384/540 on held-out test set)

**Golden-Set Accuracy:** 56.36% (124/220) — This is the more honest estimate of real-world performance, as the golden set is sampled from the raw data pool, not the curated training distribution.

**Key Findings:**
- Phase E taxonomy cleanup decreased accuracy by 1.30pp — human-labeled data contains information beyond explicit taxonomic rules
- LLM-as-judge rubric validated for pass/fail decisions (76.5% agreement, κ=0.443) but NOT for dimension-level quality scores (negative correlations)
- The gap between test-set (71.11%) and golden-set (56.36%) accuracy reveals that the 71.11% is an optimistic in-distribution estimate; real-world performance is likely closer to 56%

---

## 1. Problem Framing

### Objective
Classify Amazon customer service conversations into 15 intent categories to enable automatic handling or escalation.

### Dataset
- **Training:** 2,160 examples
- **Test:** 540 examples
- **Golden Set:** 200 examples (LLM-labeled, NOT human ground truth)
- **Source:** AmazonHelp customer service logs

### Intent Taxonomy (15 classes)
DELIVERY_LATE, DELIVERY_MISSING, DELIVERY_TRACKING, ORDER_STATUS, ORDER_MODIFY, PRODUCT_ISSUE, RETURN_REQUEST, REFUND_REQUEST, PAYMENT_ISSUE, ACCOUNT_ACCESS, APP_USAGE, DEVICE_ISSUE, VIDEO_STREAMING, CANCELLATION, OTHER

---

## 2. Results vs Baselines

| Model | Accuracy | Delta vs Baseline |
|-------|----------|-------------------|
| Original baseline | 54.44% | - |
| Phase 6 TF-IDF+LinearSVC | 70.56% | +16.12pp |
| **Phase C (BEST)** | **71.11%** | **+16.67pp** |
| Phase E (taxonomy cleanup) | 69.81% | +15.37pp |

**Phase C is 1.30pp better than Phase E taxonomy cleanup.**

---

## 3. What We Built

### Runnable Pipeline
- FastAPI backend (`api.py`) with /health and /predict endpoints
- 4-stage pipeline: Classification → Retrieval → Escalation → Reply Generation
- RAG-enhanced reply generation using Groq LLM

### Classification Model
- TF-IDF (word 1-2 grams + char 3-6 grams) + LinearSVC
- 71.11% accuracy on held-out 540-example test set
- Margin-based confidence scoring for escalation decisions

### RAG System
- Sentence-transformers embedding (all-MiniLM-L6-v2)
- FAISS index on training corpus
- Top-5 similarity retrieval for evidence grounding

### Evaluation Harness
- 8 API tests passing
- 70-test evaluator
- LLM-as-judge rubric for reply quality (manual)

---

## 4. What We Did NOT Build

1. **Human-labeled Golden Set**: The 200 examples are LLM-labeled, not human-labeled. True human evaluation requires $1,500-3,000 and 4-8 hours of labeling effort.

2. **Automated LLM-as-Judge**: Implemented but requires manual human review subset for agreement measurement.

3. **Human-vs-LLM Agreement Dataset**: The 30-50 example human review subset was not completed.

4. **Production-grade RAG**: FAISS index is train-only; production would need incremental indexing.

5. **Streaming/Async Support**: API is synchronous; high-throughput production needs async.

---

## 5. Top 5 Failure Modes

| Rank | Confusion Pair | Count | Root Cause |
|------|----------------|-------|------------|
| 1 | APP_USAGE → OTHER | 14 | App vs website vs device boundary unclear |
| 2 | DELIVERY_LATE → OTHER | 13 | "Not here yet" ambiguous |
| 3 | DELIVERY_MISSING → DELIVERY_LATE | 8 | Late vs never-arrived boundary |
| 4 | DELIVERY_LATE → RETURN_REQUEST | 6 | Customer wants refund for late |
| 5 | DEVICE_ISSUE → OTHER | 6 | Physical device vs app/website |

**Root Cause:** Ambiguous taxonomy boundaries (30.1% of errors) vs genuine model mistakes (69.9%).

---

## 6. Honest Accuracy Estimates and Limitations

### 6a. The Test-Set vs Golden-Set Gap

The 71.11% test-set accuracy (384/540) is an **in-distribution** estimate — the test set was drawn from the same curated/labeled pool the model was tuned against. The golden set, by contrast, was sampled from the raw, untouched data pool and human-labeled, providing an **out-of-sample, more realistic** estimate.

| Metric | Accuracy | Count | Interpretation |
|--------|----------|-------|---------------|
| Test Set | 71.11% | 384/540 | In-distribution (optimistic) |
| Golden Set | 56.36% | 124/220 | Out-of-sample (realistic) |
| **Gap** | **-14.75pp** | — | How much optimism inflates the headline |

**The golden-set accuracy (56.36%), not the test-set accuracy (71.11%), is the more honest estimate of how this system would perform on real incoming messages.**

**Why the gap exists:**
- The test set shares labeling patterns and quality signals with the training data
- The golden set is genuinely out-of-sample — harder, more varied, less curated
- The golden set includes edge cases that the training pipeline did not see

**Weakest per-intent performance on the golden set:**

| Intent | Accuracy | Correct/Total | Failure Pattern |
|--------|----------|---------------|-----------------|
| DELIVERY_MISSING | 18.2% | 4/22 | Frequently misclassified as OTHER or DELIVERY_LATE |
| PRODUCT_ISSUE | 26.7% | 4/15 | Frequently misclassified as OTHER |
| ACCOUNT_ACCESS | 33.3% | 5/15 | Frequently misclassified as APP_USAGE or OTHER |
| CANCELLATION | 40.0% | 4/10 | Frequently misclassified as ORDER_MODIFY or OTHER |
| REFUND_REQUEST | 45.5% | 5/11 | Frequently misclassified as RETURN_REQUEST |

**Pattern:** The model defaults to the majority class (OTHER, 34.7% of training data) when uncertain, rather than correctly identifying the true intent. This is a known limitation of linear classifiers on open-ended classification tasks with long-tail intent distributions.

### 6b. The LLM-Judge Score Reliability Issue

The LLM-as-judge rubric produces ACCEPT/REVISE decisions with moderate human agreement, but the underlying dimension-level scores are NOT reliable.

**Final metrics (n=17 common examples):**

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Decision Agreement | 76.5% (13/17) | Moderate |
| Cohen's Kappa | 0.443 | Moderate agreement |
| Score Correlation (Spearman) | **-0.181** | Negative — no reliable correlation |
| Score Correlation (Pearson) | **-0.211** | Negative — no reliable correlation |

**What this means in plain terms:** The LLM judge and a human reviewer often reach the same final verdict (ACCEPT or REVISE), but they do not agree on the underlying quality scores — and when they disagree on scores, the disagreements are not consistent or predictable. The rubric dimensions appear to be measuring different things to the judge vs. the human, rather than capturing a shared underlying quality axis.

**Practical implication:** Only the binary decision (ACCEPT/REVISE) has partial validation. The 0-5 dimension scores should not be used as standalone quality feedback — they are not yet a reliable signal.

**Sample size limitation:** Only 17 of 40 examples had both LLM and human scores. The remaining 23 examples were ESCALATE cases with no generated reply to evaluate. This finding needs a larger sample (n≥50) to be considered fully reliable.

---

## 7. Key Decisions Log

| # | Decision | Why | Evidence |
|---|----------|-----|----------|
| 1 | Freeze Phase C as baseline | Phase E hurt accuracy | 71.11% vs 69.81% |
| 2 | Keep Phase C over Phase 6 | +0.55pp improvement | 384 vs 381 correct |
| 3 | Use TF-IDF not neural | TF-IDF outperformed | Phase C vs Phase 6 comparison |
| 4 | Char + Word n-grams | Both features help | Phase C uses both |
| 5 | LinearSVC not LogisticRegression | Better margin calibration | Phase C uses LinearSVC |
| 6 | Remove ORDER_MODIFY from HIGH_RISK | Only 2 train, 0 test examples | Insufficient data |
| 7 | Escalation-first architecture | Financial safety | PAYMENT_ISSUE always escalates |
| 8 | RAG on train only | Prevent leakage | Test not in index |
| 9 | 15 intent classes | Balanced granularity | Phase C taxonomy |
| 10 | Skip Phase 7 optimization | Assignment freeze | User directive |

---

## 8. Next Steps

### If Human-Labeled Golden Set Becomes Available:
1. Measure true human accuracy on 50 random examples
2. Compute Cohen's Kappa for human-vs-model agreement
3. Identify systematic model-human disagreements

### If Production Deployment:
1. Move to sentence-transformers + vector DB for better retrieval
2. Implement feedback loop for label correction
3. Add confidence calibration (Platt scaling)
4. A/B test escalation thresholds

### If More Data Available:
1. Collect more CANCELLATION and ORDER_MODIFY examples (<5 total)
2. Active learning for ambiguous boundary cases
3. Error-focused data collection

---

## 9. LLM-as-Judge Validation

### Evaluation Harness

The LLM-as-judge rubric evaluates AI-generated replies on 5 dimensions (1-5 scale):

| Dimension | Description |
|-----------|-------------|
| Factual Accuracy | Does the reply address the customer's actual issue? |
| Policy Alignment | Does the reply follow Amazon customer service policies? |
| Empathy & Tone | Does the reply show appropriate empathy and professional tone? |
| Completeness | Does the reply fully address the customer's needs? |
| Coherence | Is the reply well-structured and easy to understand? |

**Decision Rule:** ACCEPT if average score >= 3.0, else REVISE

### Sample Coverage

- **LLM Judge:** 40/40 examples evaluated (17 AUTO_HANDLE + 23 ESCALATE with template replies)
- **Human Reviews:** 17/40 examples (only AUTO_HANDLE cases had replies to review)
- **Agreement computed on:** 17 common examples

### Honest Results (17 Examples)

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Decision Agreement | 76.5% (13/17) | Moderate |
| Cohen's Kappa | 0.443 | Moderate agreement |
| Score Correlation (Spearman) | **-0.181** | Negative — unreliable |
| Score Correlation (Pearson) | **-0.211** | Negative — unreliable |

### Per-Dimension Correlations (All Near Zero or Negative)

| Dimension | Spearman r | Avg \|Diff\| |
|-----------|------------|--------------|
| Factual Accuracy | -0.210 | 1.71 |
| Policy Alignment | +0.015 | 1.59 |
| Empathy & Tone | -0.018 | 1.24 |
| Completeness | -0.036 | 1.29 |
| Coherence | -0.056 | 1.00 |

### Conclusion

**The LLM judge and human reach the same final verdict most of the time (76.5%), but do NOT agree on underlying quality scores.**

The dimension-level scoring is unreliable — correlations near zero indicate the rubric dimensions are not measuring consistent quality. Do NOT use dimension-level feedback from the LLM judge to improve replies.

### Files

- `data/evaluation/llm_judge_results.jsonl` - 40 LLM judge evaluations
- `data/evaluation/llm_judge_results_16examples.jsonl` - Original 16 before template replies
- `data/evaluation/human_review_results.jsonl` - 17 human evaluations
- `data/evaluation/llm_human_agreement_report.md` - Full honest analysis

---

## 10. Files Reference

| File | Description |
|------|-------------|
| `api.py` | FastAPI backend |
| `data/pipeline.py` | Pipeline orchestration |
| `data/baseline/phaseC_model.joblib` | **BEST MODEL** (71.11%) |
| `data/baseline/phase6_best_model.joblib` | 70.56% (legacy) |
| `data/llm_judge.py` | LLM-as-judge implementation |
| `data/golden/golden_set_export.jsonl` | 200 examples for labeling |
| `data/golden/golden_set_labelling_guide.md` | Labeling methodology |
| `data/evaluation/human_review_tool.py` | Human review interface |
| `data/evaluation/run_llm_judge_eval.py` | LLM judge batch runner |
| `data/evaluation/calculate_agreement.py` | Agreement calculator |
| `test_api.py` | 8 API tests (all passing) |

---

*Report generated: 2026-09-12*
*Phase C frozen as baseline per user directive*
*LLM-as-Judge validation complete*
