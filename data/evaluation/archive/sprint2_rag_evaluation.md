# Sprint 2: RAG / Similar Case Retrieval — Evaluation Report

## Status: COMPLETE

## Objective
Given a new customer conversation, retrieve the most relevant historical conversations that can later be used to ground reply generation.

---

## Implementation Plan

### 1. Embedding Model
- **Model**: `all-MiniLM-L6-v2` (sentence-transformers)
- **Dimension**: 384
- **Type**: Local model (no API required)

### 2. Corpus
- **Source**: `data/processed/amazonhelp_labeled_conversations_v21.jsonl`
- **Corpus size**: 2160 TRAIN conversations (80% of 2700)
- **Text embedded**: Customer messages only (concatenated)

### 3. Index
- **Type**: FAISS IndexFlatIP (cosine similarity via vector normalization)
- **Corpus type**: TRAIN ONLY (to prevent evaluation leakage)
- **Index file**: `data/rag/faiss_index_train.bin`

### 4. Top-K
- **Default top-k**: 5
- (Retrieval returns top-5 similar conversations)

### 5. Metadata Stored
- `conversation_id`
- `primary_intent` (rule-based label)
- `customer_text`
- `full_turns` (for full conversation display)

---

## Retrieval Quality Metrics (NO LEAKAGE)

Evaluated on 540 TEST conversations against TRAIN-only index.

### Intent Match Rate
| Metric | Score |
|--------|-------|
| Top-1 match rate | 38.7% (209/540) |
| Top-3 match rate | 63.3% (342/540) |
| **Top-5 match rate** | **73.9% (399/540)** |

**Top-5 match rate = 73.9%** means that for ~74% of test conversations, a conversation with the SAME INTENT appears in the top-5 retrieved results.

### Per-Intent Top-5 Accuracy
| Intent | Accuracy | Support |
|--------|----------|---------|
| OTHER | 90.1% | 203 |
| DELIVERY_LATE | 79.2% | 96 |
| PAYMENT_ISSUE | 78.3% | 23 |
| VIDEO_STREAMING | 71.4% | 14 |
| DEVICE_ISSUE | 70.6% | 34 |
| DELIVERY_TRACKING | 62.5% | 8 |
| REFUND_REQUEST | 61.5% | 13 |
| APP_USAGE | 56.8% | 44 |
| ORDER_STATUS | 57.7% | 26 |
| DELIVERY_MISSING | 51.7% | 29 |
| RETURN_REQUEST | 48.4% | 31 |
| ACCOUNT_ACCESS | 33.3% | 6 |
| PRODUCT_ISSUE | 27.3% | 11 |
| ORDER_MODIFY | 0.0% | 2 |

### Average Similarity Scores
- Top-1 similarity: 0.7315
- Top-5 average similarity: 0.6681

---

## Retrieval Examples

Query: "My package was supposed to arrive yesterday but it's still not here"
- Rank 1: DELIVERY_LATE (score: 0.74)
- Rank 2: DELIVERY_LATE (score: 0.74)
- Rank 3: OTHER (score: 0.73)
- Rank 4: OTHER (score: 0.68)
- Rank 5: DELIVERY_LATE (score: 0.68)

Query: "I want to return my order and get a refund"
- Rank 1: RETURN_REQUEST (score: 0.63)
- Rank 2: RETURN_REQUEST (score: 0.62)
- Rank 3: REFUND_REQUEST (score: 0.61)
- Rank 4: REFUND_REQUEST (score: 0.61)
- Rank 5: RETURN_REQUEST (score: 0.60)

---

## Known Limitations

1. **Labels are rule-based, not human-verified**
   - Actual retrieval relevance to human-assessed intent is unknown

2. **No outcome/resolution data**
   - Retrieved conversations do not include resolution information
   - Cannot filter by "successfully resolved"

3. **Rare intents have low accuracy**
   - ORDER_MODIFY: 0% (only 2 test samples)
   - PRODUCT_ISSUE: 27.3% (only 11 test samples)

4. **Intent match is a proxy metric**
   - We measure "same intent in top-k", not true semantic relevance
   - A conversation with same intent but different details may still be retrieved

5. **No cross-validation**
   - Single train/test split only
   - Results may vary with different splits

---

## Artifacts

| File | Description |
|------|-------------|
| `data/rag/faiss_index_train.bin` | FAISS index (2160 TRAIN conversations) |
| `data/rag/corpus_metadata_train.jsonl` | Metadata (id, intent, text) |
| `data/rag/corpus_full_train.jsonl` | Full conversations with turns |
| `data/rag/config_train.json` | Configuration |
| `data/rag_retrieval.py` | Retrieval script |
| `data/evaluate_rag.py` | Evaluation script |

---

## Sprint 2: COMPLETE