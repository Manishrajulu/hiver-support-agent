#!/usr/bin/env python3
"""
Sprint 2: RAG Retrieval - Using TRAIN-only index for production retrieval.
"""

import json
import os
import sys
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

sys.stdout.reconfigure(encoding='utf-8')

INDEX_DIR = 'data/rag'
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'

def load_index(corpus_type='train'):
    """Load the FAISS index and metadata."""
    if corpus_type == 'train':
        config_path = os.path.join(INDEX_DIR, 'config_train.json')
        index_path = os.path.join(INDEX_DIR, 'faiss_index_train.bin')
        metadata_path = os.path.join(INDEX_DIR, 'corpus_metadata_train.jsonl')
    else:
        config_path = os.path.join(INDEX_DIR, 'config.json')
        index_path = os.path.join(INDEX_DIR, 'faiss_index.bin')
        metadata_path = os.path.join(INDEX_DIR, 'corpus_metadata.jsonl')

    with open(config_path, 'r') as f:
        config = json.load(f)

    index = faiss.read_index(index_path)

    metadata = []
    with open(metadata_path, 'r', encoding='utf-8') as f:
        for line in f:
            metadata.append(json.loads(line))

    model = SentenceTransformer(EMBEDDING_MODEL)

    return model, index, metadata, config

def retrieve(query, model, index, metadata, top_k=5):
    """Retrieve top-k similar conversations."""
    query_vec = model.encode([query]).astype('float32')
    norm = np.linalg.norm(query_vec, axis=1, keepdims=True)
    query_vec_norm = query_vec / norm

    scores, indices = index.search(query_vec_norm, top_k)

    results = []
    for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
        if idx < len(metadata):
            results.append({
                'rank': i + 1,
                'conversation_id': metadata[idx]['conversation_id'],
                'primary_intent': metadata[idx]['primary_intent'],
                'customer_text': metadata[idx]['customer_text'],
                'similarity_score': float(score)
            })

    return results

def print_result(result):
    print(f"\n  Rank {result['rank']}: {result['conversation_id']}")
    print(f"    Intent: {result['primary_intent']}")
    print(f"    Score: {result['similarity_score']:.4f}")
    print(f"    Text: {result['customer_text'][:150]}...")

if __name__ == '__main__':
    # Load TRAIN index (production use)
    print("Loading TRAIN index (production)...\n")
    model, index, metadata, config = load_index('train')
    print(f"Loaded index with {len(metadata)} TRAIN conversations")
    print()

    test_queries = [
        "My package was supposed to arrive yesterday but it's still not here",
        "I want to return my order and get a refund",
        "My Kindle is not working, the screen is frozen",
        "I was charged twice for my order",
        "I can't login to my account, password reset isn't working",
        "Prime Video keeps buffering and won't play",
    ]

    print("=" * 70)
    print("RETRIEVAL TEST RESULTS (TRAIN INDEX)")
    print("=" * 70)

    for query in test_queries:
        print(f"\nQuery: {query}")
        results = retrieve(query, model, index, metadata, 5)
        for r in results:
            print_result(r)

    print("\n" + "=" * 70)