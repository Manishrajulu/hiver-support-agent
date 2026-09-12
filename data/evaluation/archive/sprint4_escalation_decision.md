# Sprint 4: Escalation Decision — Evaluation Report

## Status: COMPLETE

---

## Architecture

```
Customer conversation
        ↓
TF-IDF + Logistic Regression (baseline_model.joblib)
        ↓
Intent + confidence
        ↓
RAG retrieval (faiss_index_train.bin, top-k=5)
        ↓
LLM reply generation
        ↓
Escalation Decision Engine
        ↓
AUTO_HANDLE or ESCALATE
```

---

## Escalation Decision Logic

```
IF HIGH_RISK_INTENT → ESCALATE
   (REFUND_REQUEST, PAYMENT_ISSUE, ACCOUNT_ACCESS, ORDER_MODIFY)

ELSE IF LOW_CONFIDENCE (< 0.3) → ESCALATE

ELSE IF NO_EVIDENCE or WEAK_EVIDENCE (avg_sim < 0.4) → ESCALATE

ELSE → AUTO_HANDLE
```

### Why This Logic?
1. **HIGH_RISK intents** have financial/security implications → escalate to human
2. **LOW confidence** means classifier is uncertain → escalate to human
3. **NO/WEAK evidence** means retrieval failed → can't generate grounded reply

---

## Evaluation

### Test Set
- **Sample size**: 50 conversations (random seed 42)
- **Source**: 540 test conversations

### Results
| Decision | Count | Rate |
|----------|-------|------|
| ESCALATE | 40 | 80% |
| AUTO_HANDLE | 10 | 20% |

### Per-Intent Escalation Rate
| Intent | Escalated | Total | Rate |
|--------|-----------|-------|------|
| APP_USAGE | 1 | 1 | 100% |
| DELIVERY_LATE | 4 | 5 | 80% |
| DELIVERY_MISSING | 2 | 5 | 40% |
| DELIVERY_TRACKING | 1 | 1 | 100% |
| DEVICE_ISSUE | 3 | 3 | 100% |
| ORDER_STATUS | 2 | 2 | 100% |
| OTHER | 18 | 23 | 78% |
| PAYMENT_ISSUE | 3 | 3 | 100% |
| PRODUCT_ISSUE | 0 | 1 | 0% |
| REFUND_REQUEST | 1 | 1 | 100% |
| RETURN_REQUEST | 2 | 2 | 100% |
| VIDEO_STREAMING | 3 | 3 | 100% |

### AUTO_HANDLE Quality
- **Correct intent**: 90% (9/10)
- **Average confidence**: Higher than ESCALATE cases

### Top Escalation Reasons
| Reason | Count |
|--------|-------|
| LOW_CONF (<0.3) | 15 |
| HIGH_RISK | 2 (REFUND_REQUEST) |

---

## Example Decisions

### AUTO_HANDLE Example
**Customer**: "My package was supposed to arrive yesterday but it's still not here."
- Intent: DELIVERY_LATE (conf: 0.48)
- Evidence: avg_sim=0.71
- Decision: **AUTO_HANDLE**
- Reason: confidence>=0.3, evidence strong, not high-risk

### ESCALATE Example (Low Confidence)
**Customer**: "Hello?" (vague)
- Intent: OTHER (conf: 0.15)
- Evidence: avg_sim=0.28
- Decision: **ESCALATE**
- Reason: LOW_CONF:0.148, WEAK_EVIDENCE

### ESCALATE Example (High Risk)
**Customer**: "I want a refund for my order"
- Intent: REFUND_REQUEST (conf: 0.52)
- Decision: **ESCALATE**
- Reason: HIGH_RISK:REFUND_REQUEST

---

## Known Limitations

1. **High escalation rate (80%)**
   - Many cases escalate even though AUTO_HANDLE could work
   - LOW_CONFIDENCE threshold (0.3) is conservative

2. **Misclassification propagates**
   - If classifier predicts PAYMENT_ISSUE (high-risk) but actual is OTHER, still escalates
   - Wrong high-risk prediction causes unnecessary escalation

3. **No outcome tracking**
   - Don't know if AUTO_HANDLE cases are actually resolved
   - Can't learn from escalation outcomes

4. **Threshold tuning needed**
   - 0.3 for LOW_CONFIDENCE is arbitrary
   - 0.4 for WEAK_EVIDENCE is arbitrary
   - Should be tuned on actual resolution outcomes

---

## Output Format

```json
{
  "intent": "DELIVERY_LATE",
  "confidence": 0.48,
  "draft_reply": "I am very sorry to hear...",
  "evidence": [...],
  "retrieved_case_ids": [...],
  "escalation": {
    "decision": "AUTO_HANDLE",
    "reason": "AUTO_HANDLE - conf=0.48, intent=DELIVERY_LATE",
    "risk_flags": [],
    "evidence_summary": {
      "case_count": 5,
      "avg_similarity": 0.71,
      "max_similarity": 0.75
    }
  }
}
```

---

## Artifacts

| File | Description |
|------|-------------|
| `data/escalation_decision.py` | Main implementation |
| `data/evaluate_escalation.py` | Evaluation script |
| `data/escalation/evaluation_results.json` | Evaluation results |

---

## Sprint 4: COMPLETE