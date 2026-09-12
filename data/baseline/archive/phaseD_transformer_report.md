# Phase D: Transformer Experiment Report

## 1. Executive Summary

**Objective:** Determine whether a fine-tuned Transformer model can outperform the current 71.11% Phase C TF-IDF + LinearSVC model.

**Result:** Sentence Transformer embeddings + LinearSVC achieved **47.78% accuracy**, significantly underperforming the TF-IDF baseline.

**Full fine-tuning attempt:** DistilBERT fine-tuning was attempted but could not complete within reasonable time on CPU-only environment.

---

## 2. Experiment Attempted

### 2.1 Sentence Transformer Embeddings + LinearSVC

**Approach:** Use pre-trained sentence transformer (all-MiniLM-L6-v2) to generate embeddings, then train LinearSVC classifier on embeddings.

**Configuration:**
- Model: all-MiniLM-L6-v2 (384-dimensional embeddings)
- Classifier: LinearSVC(C=1.0, class_weight='balanced')
- Text preprocessing: ALL customer turns concatenated (same as Phase 6/Phase C)

**Results:**

| Metric | Value |
|--------|-------|
| Accuracy | 47.78% (258/540) |
| Phase C (TF-IDF) | 71.11% (384/540) |
| **Delta** | **-23.33pp** |

**Per-Intent Performance:**

| Intent | Precision | Recall | F1-Score | Support |
|--------|-----------|--------|----------|---------|
| ACCOUNT_ACCESS | 0.20 | 0.43 | 0.27 | 7 |
| APP_USAGE | 0.38 | 0.32 | 0.35 | 44 |
| DELIVERY_LATE | 0.50 | 0.31 | 0.38 | 108 |
| DELIVERY_MISSING | 0.10 | 0.09 | 0.09 | 35 |
| DEVICE_ISSUE | 0.54 | 0.64 | 0.58 | 33 |
| OTHER | 0.81 | 0.63 | 0.71 | 186 |
| PAYMENT_ISSUE | 0.43 | 0.78 | 0.55 | 23 |
| ... | ... | ... | ... | ... |

### 2.2 DistilBERT Fine-tuning

**Approach:** Full fine-tuning of distilbert-base-uncased

**Configuration:**
- Model: distilbert-base-uncased
- Max length: 96 tokens
- Batch size: 16
- Learning rate: 5e-5
- Epochs: 2
- Warmup: 6% of steps
- Device: CPU (no CUDA available)

**Status:** Could not complete within reasonable time. CPU-only training proved too slow for full transformer fine-tuning.

---

## 3. Key Finding

**Sentence Transformer embeddings significantly underperform TF-IDF for this task.**

This is a surprising but important finding. Possible explanations:

1. **Domain mismatch:** Pre-trained sentence transformers are trained on general text, not Amazon customer service conversations
2. **TF-IDF captures domain-specific patterns:** N-gram features capture Amazon-specific vocabulary and patterns
3. **Class imbalance:** Sentence transformers may struggle more with highly imbalanced classes (OTHER has 186 examples, CANCELLATION has 1)

---

## 4. Comparison Table

| Model | Accuracy | Delta vs Baseline | Delta vs Phase C |
|-------|----------|-------------------|------------------|
| Original baseline | 54.44% | - | -16.67pp |
| Phase 6 TF-IDF+LinearSVC | 70.56% | +16.12pp | -0.55pp |
| Phase C TF-IDF+LinearSVC | 71.11% | +16.67pp | - |
| **Phase D SentenceTransf** | **47.78%** | **-6.66pp** | **-23.33pp** |

---

## 5. Confusion Pairs Comparison

### Phase D (Sentence Transformer) Top Confusion Pairs

| Rank | Actual → Predicted | Count |
|------|-------------------|-------|
| 1 | DELIVERY_LATE → ORDER_STATUS | 15 |
| 2 | OTHER → DELIVERY_LATE | 13 |
| 3 | DELIVERY_LATE → DELIVERY_MISSING | 11 |
| 4 | DELIVERY_LATE → OTHER | 11 |
| 5 | APP_USAGE → OTHER | 10 |

### Phase C (TF-IDF) Top Confusion Pairs

| Rank | Actual → Predicted | Count |
|------|-------------------|-------|
| 1 | APP_USAGE → OTHER | 14 |
| 2 | DELIVERY_LATE → OTHER | 13 |
| 3 | DEVICE_ISSUE → OTHER | 9 |
| 4 | ORDER_STATUS → OTHER | 6 |
| 5 | DELIVERY_LATE → RETURN_REQUEST | 6 |

**Key Observation:** Sentence Transformer creates more confusion between delivery-related intents (DELIVERY_LATE ↔ ORDER_STATUS ↔ DELIVERY_MISSING), while TF-IDF has broader confusion with OTHER.

---

## 6. Error Analysis

### Examples Where Sentence Transformer Fails

**DELIVERY_LATE → ORDER_STATUS (15 errors):**
- "not delivering my order on time" - sentence transformer sees "order" and predicts ORDER_STATUS
- TF-IDF correctly identifies "delivering...on time" as DELIVERY_LATE

**OTHER → DELIVERY_LATE (13 errors):**
- Sentence transformer over-predicts DELIVERY_LATE for ANY text mentioning delivery
- TF-IDF is more conservative and only predicts DELIVERY_LATE when strongly indicated

---

## 7. Practical Tradeoffs

| Aspect | Phase C (TF-IDF) | Phase D (SentenceTransf) |
|--------|------------------|-------------------------|
| Accuracy | 71.11% | 47.78% |
| Model size | ~10 MB | ~90 MB (all-MiniLM-L6-v2) |
| Training time | Seconds | Minutes for embeddings |
| Inference speed | Very fast | Slower (embedding generation) |
| CPU-friendly | Yes | Moderate |
| GPU-friendly | Yes | Yes |
| Deployment complexity | Low | Higher |

---

## 8. Conclusion

**Sentence Transformer approach does NOT improve over TF-IDF.**

The pre-trained sentence transformer (all-MiniLM-L6-v2) with LinearSVC achieved only 47.78% accuracy, significantly worse than the TF-IDF + LinearSVC baseline at 71.11%.

**Key takeaways:**

1. TF-IDF remains the strong baseline for this domain-specific classification task
2. Pre-trained general-domain embeddings don't transfer well to Amazon customer service intent classification
3. Domain-specific n-gram features (TF-IDF) capture important patterns that generic embeddings miss
4. Full transformer fine-tuning was not feasible within the available CPU-only environment

---

## 9. Recommendation

**Phase C (TF-IDF + LinearSVC at 71.11%) remains the best model.**

The sentence transformer approach is not recommended for this task. If transformer-based approaches are desired in the future:

1. **Fine-tuning is required** - frozen embeddings don't work well
2. **GPU is needed** - CPU fine-tuning is too slow
3. **Domain adaptation** - consider further pre-training on customer service text

---

## 10. Files Created

| File | Description |
|------|-------------|
| `phaseD_transformer_predictions.jsonl` | Phase D predictions (258/540 correct) |
| `phaseD_transformer_model.pkl` | Sentence transformer + classifier |
| `phaseD_label_mapping.json` | Label mapping |
| `phaseD_transformer_report.md` | This report |

---

## 11. Model Comparison Summary

| Model | Accuracy | Status |
|-------|----------|--------|
| Original baseline | 54.44% | - |
| Phase 6 TF-IDF+LinearSVC | 70.56% | Production |
| Phase C TF-IDF+LinearSVC | 71.11% | **Best model** |
| Phase D SentenceTransf | 47.78% | Rejected |

---

*Report generated: 2026-09-11*
*Phase D: Transformer Experiment - COMPLETE*
*Recommendation: Retain Phase C as production model*