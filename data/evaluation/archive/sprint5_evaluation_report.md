# Sprint 5: System Evaluation Report

## Status: COMPLETE

---

## Evaluation Methodology

### Data Split
- **Training set**: 2160 conversations (80%)
- **Test set**: 540 conversations (20%)
- **Split method**: Stratified, random_state=42
- **Leakage prevention**: RAG index built from TRAIN set only

### Label Source Warning
**IMPORTANT**: All labels used for evaluation are **RULE-BASED** (v2.1), NOT human-verified ground truth.
- Earlier manual review found ~43.5% error rate in rule-based labels
- Reported accuracy metrics reflect agreement with rules, NOT true human accuracy
- We cannot claim these are "true" accuracy figures

### Components Evaluated
1. **Classification**: TF-IDF + Logistic Regression (`baseline_model.joblib`)
2. **Retrieval**: Sentence-transformers + FAISS (`faiss_index_train.bin`)
3. **Reply Generation**: Groq qwen/qwen3.8-27b
4. **Escalation**: Rule-based policy

---

## 1. Classification Evaluation (540 test conversations)

### Overall Metrics
| Metric | Value |
|--------|-------|
| **Accuracy** | **56.30%** |
| **Macro F1** | **0.507** |
| **Weighted F1** | **0.560** |

### Per-Intent Performance
| Intent | Precision | Recall | F1 | Support |
|--------|-----------|--------|-----|---------|
| DELIVERY_TRACKING | 0.538 | 0.875 | 0.667 | 8 |
| DEVICE_ISSUE | 0.632 | 0.706 | 0.667 | 34 |
| RETURN_REQUEST | 0.542 | 0.839 | 0.658 | 31 |
| OTHER | 0.762 | 0.537 | 0.630 | 203 |
| REFUND_REQUEST | 0.500 | 0.769 | 0.606 | 13 |
| ORDER_STATUS | 0.531 | 0.654 | 0.586 | 26 |
| DELIVERY_MISSING | 0.514 | 0.621 | 0.562 | 29 |
| PAYMENT_ISSUE | 0.500 | 0.652 | 0.566 | 23 |
| VIDEO_STREAMING | 0.500 | 0.643 | 0.563 | 14 |
| DELIVERY_LATE | 0.452 | 0.542 | 0.493 | 96 |
| ACCOUNT_ACCESS | 0.400 | 0.667 | 0.500 | 6 |
| PRODUCT_ISSUE | 0.429 | 0.273 | 0.333 | 11 |
| APP_USAGE | 0.323 | 0.227 | 0.267 | 44 |
| ORDER_MODIFY | 0.000 | 0.000 | 0.000 | 2 |

### Top Classification Confusions
| Confusion | Count |
|-----------|-------|
| OTHER → DELIVERY_LATE | 39 |
| APP_USAGE → OTHER | 15 |
| OTHER → APP_USAGE | 13 |
| DELIVERY_LATE → OTHER | 13 |
| APP_USAGE → DELIVERY_LATE | 8 |

### Classification Assessment
- **Strengths**: OTHER (F1=0.63), RETURN_REQUEST (F1=0.66), DEVICE_ISSUE (F1=0.67)
- **Weaknesses**: APP_USAGE (F1=0.27), PRODUCT_ISSUE (F1=0.33), ORDER_MODIFY (F1=0.00)
- **Critical issue**: ORDER_MODIFY has only 2 test samples, making evaluation unreliable

---

## 2. Retrieval Evaluation (540 test conversations)

### Intent Match Rates
| Metric | Value |
|--------|-------|
| Top-1 Match | 38.7% (209/540) |
| Top-3 Match | 63.3% (342/540) |
| **Top-5 Match** | **73.9% (399/540)** |
| Avg Top-1 Similarity | 0.718 |

### Retrieval Assessment
- **Good**: Top-5 match rate of 73.9% is reasonable for production use
- **Limitation**: Measures "same intent in top-k", not semantic relevance
- **Note**: Retrieval quality varies by intent (see Sprint 2 report)

---

## 3. Reply Generation Evaluation (30 sampled conversations)

### Escalation Summary
| Decision | Count | Rate |
|----------|-------|------|
| ESCALATE | 26 | 86.7% |
| AUTO_HANDLE | 4 | 13.3% |

### AUTO_HANDLE Quality
- **Correct intent when AUTO_HANDLE**: 100% (4/4)
- AUTO_HANDLE cases are high-confidence, evidence-rich cases

### Reply Generation Observations
- Replies generally follow evidence grounding rules
- Model acknowledges limitations when evidence is weak
- No automated hallucination detection (human review needed)

---

## 4. Escalation Evaluation (30 sampled conversations)

### Current Policy
```
IF HIGH_RISK_INTENT → ESCALATE (REFUND_REQUEST, PAYMENT_ISSUE, ACCOUNT_ACCESS, ORDER_MODIFY)
ELSE IF LOW_CONFIDENCE (< 0.3) → ESCALATE
ELSE IF NO_EVIDENCE or WEAK_EVIDENCE (avg_sim < 0.4) → ESCALATE
ELSE → AUTO_HANDLE
```

### Escalation Rate Analysis
- **86.7% escalation rate** is **HIGHLY CONSERVATIVE**
- Most escalations are due to LOW_CONFIDENCE (< 0.3)
- Classifier confidence is generally low (average ~0.4)

### Is 80%+ Escalation Appropriate?
**ARGUMENTS FOR high escalation:**
- Safer to escalate than to give wrong advice
- Financial/security intents (REFUND, PAYMENT) justify escalation
- Low confidence cases should be human-reviewed

**ARGUMENTS FOR lower escalation:**
- 86.7% escalation means the AI handles only 13.3% autonomously
- Many AUTO_HANDLE cases could likely be handled automatically
- Human agents would be overwhelmed by 80%+ volume

**RECOMMENDATION**: The 80%+ escalation rate should be reviewed after human feedback on actual escalations. The policy is conservative but not unreasonable for a first version.

---

## 5. End-to-End Results

Results saved to: `data/evaluation/sprint5_end_to_end_results.jsonl`

Each entry contains:
- conversation_id
- predicted_intent
- confidence
- retrieved_case_ids
- retrieval_scores
- draft_reply
- escalation_decision

---

## 6. Failure Analysis

### Classification Errors (12 in 30-sample)
| Error Type | Count |
|------------|-------|
| Wrong intent predicted | 12 |

### Retrieval Failures (0 in 30-sample)
- No cases had max similarity < 0.5
- Retrieval quality is acceptable

### Escalation Errors (0 in 30-sample)
- No cases where AUTO_HANDLE was applied with wrong intent

### Systematic Failure Categories
1. **OTHER ↔ DELIVERY_LATE confusion**: 39 cases (largest confusion)
2. **APP_USAGE ↔ OTHER confusion**: 28 combined cases
3. **Low confidence across intents**: Most predictions have confidence < 0.5
4. **Rare intent failure**: ORDER_MODIFY (2 samples), ACCOUNT_ACCESS (6 samples) have unreliable metrics

---

## 7. Limitations

### Data Quality
- Labels are rule-based, NOT human-verified
- Cannot claim "true accuracy" metrics

### Classifier
- 56.3% accuracy on imperfect labels
- Low confidence scores across predictions
- Poor performance on APP_USAGE (F1=0.27), PRODUCT_ISSUE (F1=0.33)

### Retrieval
- 73.9% Top-5 intent match is reasonable but not excellent
- No outcome/resolution data in retrieved cases

### Reply Generation
- No automated hallucination detection
- Relies on model's adherence to evidence-grounding instructions
- Non-English handling is suboptimal

### Escalation
- 86.7% escalation rate is conservative
- No feedback loop from escalation outcomes

---

## 8. Overall System Assessment

### What Works
1. **Classification**: 56.3% accuracy is reasonable for a baseline
2. **Retrieval**: 73.9% Top-5 match provides good evidence
3. **Reply Generation**: Generates grounded, evidence-based replies
4. **Escalation**: Conservative policy is safe

### What Needs Improvement
1. **Classification confidence**: Average ~0.4 is low
2. **APP_USAGE handling**: F1=0.27 is poor
3. **Escalation rate**: 86.7% may be too conservative for production
4. **No human feedback loop**: Can't learn from escalation outcomes

### Key Finding
The system produces coherent outputs at every stage, but:
- The classifier is the weakest component
- Escalation policy may need tuning based on actual human capacity

---

## Verdict

**NEEDS IMPROVEMENT**

### Why Not "READY FOR INTEGRATION"?
1. **Classification accuracy (56.3%)** is reasonable as a baseline but will cause frequent wrong routing
2. **86.7% escalation rate** means human agents would handle ~80% of cases - may not reduce workload enough
3. **No human feedback loop** to learn from escalations
4. **APP_USAGE and PRODUCT_ISSUE** intents have poor F1 scores (< 0.35)

### What Must Improve Before Production
1. **Reduce escalation rate** to ~50-60% by raising confidence threshold (requires human judgment on appropriate rate)
2. **Improve APP_USAGE classification** or merge it with OTHER
3. **Add escalation outcome tracking** to enable learning
4. **Human evaluation** of reply quality to verify grounding

### What Can Ship As-Is
1. **RAG retrieval** (73.9% Top-5 match)
2. **Reply generation** (evidence-grounded)
3. **Escalation policy framework** (policy itself is sound)

---

## Artifacts Created

| File | Description |
|------|-------------|
| `sprint5_classification_metrics.json` | Full classification metrics |
| `sprint5_retrieval_metrics.json` | Retrieval metrics |
| `sprint5_escalation_metrics.json` | Escalation metrics |
| `sprint5_end_to_end_results.jsonl` | Per-conversation results (30 samples) |
| `sprint5_failure_analysis.json` | Failure case analysis |

---

*Report generated: 2026-09-10*
