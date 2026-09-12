#!/usr/bin/env python3
"""
Sprint 2: RAG / Similar Case Retrieval - Build Train-Only Index

Build a retrieval index from historical AmazonHelp conversations (TRAIN SET ONLY).
This prevents evaluation leakage when measuring retrieval quality.
"""

import json
import os
import sys
from collections import Counter

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

sys.stdout.reconfigure(encoding='utf-8')

# Config
DATA_PATH = 'data/processed/amazonhelp_labeled_conversations_v21.jsonl'
INDEX_DIR = 'data/rag'
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
EMBEDDING_DIM = 384
TOP_K = 5

print("=== Building RAG Index (TRAIN SET ONLY) ===")
print()

# Load train/test split
with open('data/baseline/baseline_train_test_split.json', 'r') as f:
    split = json.load(f)
train_ids = set(split['train_ids'])
test_ids = set(split['test_ids'])

print(f"Train IDs: {len(train_ids)}")
print(f"Test IDs: {len(test_ids)}")

# Step 1: Load conversations - only train set
print("\nStep 1: Loading TRAIN conversations...")
train_conversations = []
with open(DATA_PATH, 'r', encoding='utf-8') as f:
    for line in f:
        conv = json.loads(line)
        if conv['conversation_id'] in train_ids:
            # Extract customer messages only
            customer_texts = []
            for turn in conv.get('turns', []):
                if turn.get('speaker') == 'Customer':
                    text = turn.get('text', '').strip()
                    if text:
                        customer_texts.append(text)
            customer_text = ' '.join(customer_texts)

            train_conversations.append({
                'conversation_id': conv['conversation_id'],
                'primary_intent': conv['primary_intent'],
                'customer_text': customer_text,
                'full_turns': conv.get('turns', [])
            })

print(f"Loaded {len(train_conversations)} TRAIN conversations")

# Intent distribution in train
intent_dist = Counter(c['primary_intent'] for c in train_conversations)
print("\nIntent distribution in train corpus:")
for intent, cnt in intent_dist.most_common():
    print(f"  {intent}: {cnt}")

# Step 2: Build embeddings
print("\nStep 2: Building embeddings...")
model = SentenceTransformer(EMBEDDING_MODEL)
print(f"Model: {EMBEDDING_MODEL}")

texts = [c['customer_text'] for c in train_conversations]
print(f"Embedding {len(texts)} texts...")

embeddings = model.encode(texts, show_progress_bar=True, batch_size=64)
print(f"Embeddings shape: {embeddings.shape}")

# Step 3: Build FAISS index
print("\nStep 3: Building FAISS index...")
embeddings = embeddings.astype('float32')

# Normalize for cosine similarity
norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
embeddings_normalized = embeddings / norms

index = faiss.IndexFlatIP(EMBEDDING_DIM)
index.add(embeddings_normalized)

print(f"Index size: {index.ntotal}")

# Step 4: Save index and metadata
print("\nStep 4: Saving index and metadata...")

# Save FAISS index
index_path = os.path.join(INDEX_DIR, 'faiss_index_train.bin')
faiss.write_index(index, index_path)
print(f"Saved index: {index_path}")

# Save metadata
metadata_path = os.path.join(INDEX_DIR, 'corpus_metadata_train.jsonl')
with open(metadata_path, 'w', encoding='utf-8') as f:
    for c in train_conversations:
        f.write(json.dumps({
            'conversation_id': c['conversation_id'],
            'primary_intent': c['primary_intent'],
            'customer_text': c['customer_text'],
        }, ensure_ascii=False) + '\n')
print(f"Saved metadata: {metadata_path}")

# Save full conversations
full_conv_path = os.path.join(INDEX_DIR, 'corpus_full_train.jsonl')
with open(full_conv_path, 'w', encoding='utf-8') as f:
    for c in train_conversations:
        f.write(json.dumps({
            'conversation_id': c['conversation_id'],
            'primary_intent': c['primary_intent'],
            'full_turns': c['full_turns'],
        }, ensure_ascii=False) + '\n')
print(f"Saved full conversations: {full_conv_path}")

# Save config
config = {
    'embedding_model': EMBEDDING_MODEL,
    'embedding_dim': EMBEDDING_DIM,
    'corpus_size': len(train_conversations),
    'corpus_type': 'train_only',
    'top_k': TOP_K,
    'index_type': 'FlatIP (cosine similarity via normalization)'
}
config_path = os.path.join(INDEX_DIR, 'config_train.json')
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)
print(f"Saved config: {config_path}")

print("\n=== Train Index built successfully ===")
print(f"Corpus size: {len(train_conversations)} TRAIN conversations")
print(f"Embedding model: {EMBEDDING_MODEL}")
print(f"Embedding dimension: {EMBEDDING_DIM}")