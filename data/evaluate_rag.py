#!/usr/bin/env python3
"""
Sprint 2: RAG Retrieval Evaluation (Train-only index, Test set evaluation)

Evaluate retrieval quality WITHOUT leakage:
- Index built from TRAIN set only
- Evaluate on TEST set only
"""

import json
import os
import sys
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')

INDEX_DIR = 'data/rag'
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
TOP_K = 5

# Load TRAIN-only index
print("Loading TRAIN-only index...")
with open(os.path.join(INDEX_DIR, 'config_train.json'), 'r') as f:
    config = json.load(f)

index = faiss.read_index(os.path.join(INDEX_DIR, 'faiss_index_train.bin'))
metadata = []
with open(os.path.join(INDEX_DIR, 'corpus_metadata_train.jsonl'), 'r', encoding='utf-8') as f:
    for line in f:
        metadata.append(json.loads(line))

model = SentenceTransformer(EMBEDDING_MODEL)
print(f"Loaded index with {len(metadata)} TRAIN conversations")
print()

# Load train/test split
with open('data/baseline/baseline_train_test_split.json', 'r') as f:
    split = json.load(f)
test_ids = set(split['test_ids'])

print(f"Test IDs: {len(test_ids)}")

# Load test conversations
test_convs = []
with open('data/processed/amazonhelp_labeled_conversations_v21_phase6c.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        conv = json.loads(line)
        if conv['conversation_id'] in test_ids:
            customer_texts = []
            for turn in conv.get('turns', []):
                if turn.get('speaker') == 'Customer':
                    text = turn.get('text', '').strip()
                    if text:
                        customer_texts.append(text)
            test_convs.append({
                'conversation_id': conv['conversation_id'],
                'primary_intent': conv['primary_intent'],
                'customer_text': ' '.join(customer_texts)
            })

print(f"Test conversations loaded: {len(test_convs)}")
print()

# Evaluation
print("=" * 70)
print("RETRIEVAL EVALUATION (NO LEAKAGE)")
print("=" * 70)

def retrieve_top_k(query_vec, index, k):
    norm = np.linalg.norm(query_vec, axis=1, keepdims=True)
    query_vec_norm = query_vec / norm
    scores, indices = index.search(query_vec_norm.astype('float32'), k)
    return scores[0], indices[0]

# Metrics
intent_match_at_1 = 0
intent_match_at_3 = 0
intent_match_at_5 = 0
total = 0

per_intent_correct_at_1 = Counter()
per_intent_correct_at_5 = Counter()
per_intent_total = Counter()

# Average similarity scores
avg_scores_top1 = []
avg_scores_top5 = []

print(f"Evaluating on {len(test_convs)} test conversations...")

for conv in test_convs:
    query_vec = model.encode([conv['customer_text']])
    scores, indices = retrieve_top_k(query_vec, index, TOP_K)

    query_intent = conv['primary_intent']
    total += 1
    per_intent_total[query_intent] += 1

    retrieved_intents = []
    retrieved_scores = []
    for i, idx in enumerate(indices):
        if idx < len(metadata):
            retrieved_intents.append(metadata[idx]['primary_intent'])
            retrieved_scores.append(scores[i])

    # Top-1 match
    if retrieved_intents and retrieved_intents[0] == query_intent:
        intent_match_at_1 += 1
        per_intent_correct_at_1[query_intent] += 1
        avg_scores_top1.append(retrieved_scores[0])

    # Top-3 match
    if query_intent in retrieved_intents[:3]:
        intent_match_at_3 += 1

    # Top-5 match
    if query_intent in retrieved_intents:
        intent_match_at_5 += 1
        per_intent_correct_at_5[query_intent] += 1
        if len(retrieved_scores) >= 5:
            avg_scores_top5.append(sum(retrieved_scores) / len(retrieved_scores))

# Print results
print(f"\n=== INTENT MATCH RATE (Query Intent in Retrieved Top-K) ===")
print(f"Top-1 match rate: {intent_match_at_1}/{total} = {intent_match_at_1/total:.4f}")
print(f"Top-3 match rate: {intent_match_at_3}/{total} = {intent_match_at_3/total:.4f}")
print(f"Top-5 match rate: {intent_match_at_5}/{total} = {intent_match_at_5/total:.4f}")

print(f"\n=== PER-INTENT TOP-5 ACCURACY ===")
for intent in sorted(per_intent_total.keys()):
    count = per_intent_total[intent]
    correct = per_intent_correct_at_5[intent]
    acc = correct / count if count > 0 else 0
    print(f"  {intent:<20}: {correct:>3}/{count:<3} = {acc:.3f}")

print(f"\n=== AVERAGE SIMILARITY SCORES ===")
print(f"Average Top-1 similarity: {np.mean(avg_scores_top1):.4f}" if avg_scores_top1 else "N/A")
print(f"Average Top-5 similarity: {np.mean(avg_scores_top5):.4f}" if avg_scores_top5 else "N/A")

print(f"\n=== QUALITY ASSESSMENT ===")
avg_match = intent_match_at_5 / total
if avg_match >= 0.7:
    quality = "GOOD"
elif avg_match >= 0.5:
    quality = "MODERATE"
else:
    quality = "POOR"
print(f"Average Top-5 intent match rate: {avg_match:.3f} ({quality})")
print(f"\nNote: This measures whether a conversation with the SAME INTENT as the query")
print(f"appears in the top-5 retrieved results. This is a proxy for retrieval relevance.")