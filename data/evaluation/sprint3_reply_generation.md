# Sprint 3: Reply Generation — Evaluation Report

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
Retrieved historical cases (conversation_id, intent, text)
        ↓
LLM prompt (qwen/qwen3.8-27b)
        ↓
Generated reply (grounded in evidence)
```

---

## Components

### Classifier
- **Model**: TF-IDF + Logistic Regression
- **Artifact**: `data/baseline/baseline_model.joblib`
- **Classes**: 14 intents

### RAG Retrieval
- **Model**: `all-MiniLM-L6-v2` (sentence-transformers)
- **Index**: `data/rag/faiss_index_train.bin` (2160 TRAIN conversations)
- **Top-k**: 5 similar cases

### Reply Generation
- **Model**: `qwen/qwen3.8-27b` (Groq API)
- **Temperature**: 0.3
- **Max tokens**: 400

---

## Prompt Strategy

### System Prompt
```
You are an Amazon customer service assistant. Generate helpful replies based on retrieved evidence.

IMPORTANT:
1. Only use information from the provided evidence.
2. Do NOT invent policies, refund amounts, delivery dates, or facts not in the evidence.
3. If evidence is insufficient or irrelevant, acknowledge the limitation.
4. Be empathetic and professional.
```

### User Prompt Template
```
Customer Issue: {customer_text}

Detected Intent: {intent} (Confidence: {confidence:.2f})

Retrieved Evidence:
Case 1 (Intent: {case1_intent}, Similarity: {case1_score:.2f}):
Customer: {case1_text}
---
[Case 2-5 similar]

Based on the evidence, generate a reply.
```

---

## Evaluation

### Test Set
- **Sample size**: 20 conversations (random seed 42)
- **Source**: 540 test conversations (20% of 2700)
- **Corpus**: 2160 TRAIN conversations (no leakage)

### Metrics
| Metric | Score |
|--------|-------|
| Classification Accuracy | 60.0% (12/20) |
| Top-5 Retrieval Intent Match | 75.0% (15/20) |
| Generation Success Rate | 100% (20/20) |

---

## Example Outputs

### Example 1: Delivery Late
**Customer**: "My package was supposed to arrive yesterday but it's still not here. I'm very frustrated!"

- **Detected Intent**: DELIVERY_LATE (conf: 0.38)
- **Retrieved**: DELIVERY_LATE cases (scores: 0.75, 0.71, 0.69)
- **Generated Reply**:
  > "I am very sorry to hear that your package has not arrived yet. I completely understand how frustrating it is to wait for an order that was supposed to be delivered yesterday, especially when there is no clear update on its status. Based on similar situations, packages can sometimes show as 'out for delivery' or in transit for longer than expected... To help resolve this, please check your order details in your Amazon account for the most up-to-date tracking information."

### Example 2: Return/Refund
**Customer**: "I want to return my order and get a refund. The item is damaged."

- **Detected Intent**: ORDER_STATUS (conf: 0.30) - **Incorrect** (actual: RETURN_REQUEST)
- **Retrieved**: Mixed intents (ORDER_STATUS, PRODUCT_ISSUE, RETURN_REQUEST)
- **Generated Reply**:
  > "I am very sorry to hear that you received a damaged item... Based on similar past interactions, customers have successfully requested the return of damaged goods and refunds. However, the retrieved evidence does not contain specific policy details... Please follow these next steps: 1. Go to 'Your Orders' 2. Initiate Return 3. Provide Evidence 4. Contact Support if needed."

### Example 3: Kindle Device Issue
**Customer**: "My Kindle screen is frozen and won't turn off. I've tried everything."

- **Detected Intent**: DEVICE_ISSUE (conf: 0.35)
- **Retrieved**: DEVICE_ISSUE cases (scores: 0.59, 0.53, 0.51, 0.50)
- **Generated Reply**:
  > "I am sorry to hear that your Kindle screen is frozen... Based on similar cases, here are a few steps: 1. Force Restart (hold power 40 seconds) 2. Re-install app if using tablet 3. Check for hardware issues... Since standard reboots don't work, I recommend contacting Amazon Technical Support for hardware diagnostics or replacement options."

---

## Failure Cases

### Case 1: Low Confidence Classification
- **ID**: amazonhelp_065905
- **Actual**: RETURN_REQUEST
- **Predicted**: RETURN_REQUEST (conf: 0.16)
- **Issue**: Correct intent but very low confidence. Retrieved cases were DELIVERY_LATE instead of RETURN_REQUEST.
- **Reply Quality**: Reply mentions "incorrect item" which is irrelevant to the query.

### Case 2: Non-English Content
- **ID**: amazonhelp_008162 (Japanese)
- **Actual**: OTHER
- **Generated Reply**: In Japanese, acknowledging insufficient evidence in retrieved cases for gift card question.

### Case 3: Wrong Classification
- **ID**: amazonhelp_134637
- **Actual**: OTHER
- **Predicted**: RETURN_REQUEST (conf: 0.13)
- **Reply**: Generic apology and guidance about Prime account issues.
- **Issue**: Low confidence + wrong intent = irrelevant retrieved cases.

---

## Known Limitations

1. **Classification errors propagate to retrieval**
   - Wrong intent → wrong retrieved cases → reply may be irrelevant
   - Low confidence cases are particularly risky

2. **No resolution/outcome data**
   - Retrieved cases don't include how the situation was resolved
   - Replies cannot mention successful resolutions

3. **Noisy retrieval for rare intents**
   - ORDER_MODIFY (0% accuracy), PRODUCT_ISSUE (27%) have poor retrieval
   - These generate replies with weak evidence

4. **Multi-language handling**
   - Model generates in detected language but training data is mostly English
   - Non-English queries get non-optimal responses

5. **No hallucination detection**
   - No automated check for unsupported claims
   - Manual review shows model generally follows evidence rules

---

## Output Format

The system returns structured JSON:
```json
{
  "intent": "DELIVERY_LATE",
  "confidence": 0.375,
  "draft_reply": "I am very sorry to hear...",
  "evidence": [
    {
      "conversation_id": "amazonhelp_006942",
      "intent": "DELIVERY_LATE",
      "similarity_score": 0.75,
      "customer_text": "I was supposed to receive my package..."
    }
  ],
  "retrieved_case_ids": ["amazonhelp_006942", "amazonhelp_143457", ...]
}
```

---

## Artifacts

| File | Description |
|------|-------------|
| `data/reply_generation.py` | Main implementation |
| `data/evaluate_reply_generation.py` | Evaluation script |
| `data/reply_generation/evaluation_results.json` | Full evaluation results |
| `data/reply_generation/example_outputs.json` | 5 example outputs |

---

## Sprint 3: COMPLETE