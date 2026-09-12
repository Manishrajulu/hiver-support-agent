#!/usr/bin/env python3
"""
Sprint 3: Reply Generation Evaluation

Evaluate generated replies on a sample of test conversations.
"""

import json
import os
import sys
import joblib
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from groq import Groq
import time
from collections import Counter
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables from project root .env file
_dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
load_dotenv(_dotenv_path)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Constants
RAG_INDEX_DIR = 'data/rag'
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
CLASSIFIER_PATH = 'data/baseline/baseline_model.joblib'
GENERATION_MODEL = 'qwen/qwen3.8-27b'

# Load components
print("Loading components...")

# Load classifier
classifier = joblib.load(CLASSIFIER_PATH)

# Load RAG
config_path = os.path.join(RAG_INDEX_DIR, 'config_train.json')
index_path = os.path.join(RAG_INDEX_DIR, 'faiss_index_train.bin')
metadata_path = os.path.join(RAG_INDEX_DIR, 'corpus_metadata_train.jsonl')

with open(config_path, 'r') as f:
    rag_config = json.load(f)

rag_index = faiss.read_index(index_path)

rag_metadata = []
with open(metadata_path, 'r', encoding='utf-8') as f:
    for line in f:
        rag_metadata.append(json.loads(line))

rag_model = SentenceTransformer(EMBEDDING_MODEL)

# Load test conversations
with open('data/baseline/baseline_train_test_split.json', 'r') as f:
    split = json.load(f)
test_ids = set(split['test_ids'])

test_convs = []
with open('data/processed/amazonhelp_labeled_conversations_v21.jsonl', 'r', encoding='utf-8') as f:
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

print(f"Loaded {len(test_convs)} test conversations")
print(f"Loaded RAG index with {len(rag_metadata)} conversations")
print()

# Sample for evaluation (20 test conversations)
import random
random.seed(42)
sample_size = 20
sampled_convs = random.sample(test_convs, sample_size)

print(f"Evaluating on {sample_size} sampled test conversations...")
print()

# =============================================================================
# Reply Generation Functions
# =============================================================================

SYSTEM_PROMPT = """You are an Amazon customer service assistant. Generate helpful replies based on retrieved evidence.

IMPORTANT:
1. Only use information from the provided evidence.
2. Do NOT invent policies, refund amounts, delivery dates, or facts not in the evidence.
3. If evidence is insufficient or irrelevant, acknowledge the limitation.
4. Be empathetic and professional.
"""

def retrieve_similar(query, top_k=5):
    query_vec = rag_model.encode([query]).astype('float32')
    norm = np.linalg.norm(query_vec, axis=1, keepdims=True)
    query_vec_norm = query_vec / norm
    scores, indices = rag_index.search(query_vec_norm, top_k)

    results = []
    for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
        if idx < len(rag_metadata):
            results.append({
                'rank': i + 1,
                'conversation_id': rag_metadata[idx]['conversation_id'],
                'primary_intent': rag_metadata[idx]['primary_intent'],
                'customer_text': rag_metadata[idx]['customer_text'],
                'similarity_score': float(score)
            })
    return results

def classify(text):
    proba = classifier.predict_proba([text])[0]
    predicted_class = classifier.classes_[np.argmax(proba)]
    confidence = float(np.max(proba))
    return predicted_class, confidence

def generate_reply(customer_text, intent, confidence, retrieved_cases):
    evidence_text = ""
    for i, case in enumerate(retrieved_cases):
        evidence_text += f"""
Case {i+1} (Intent: {case['primary_intent']}, Similarity: {case['similarity_score']:.2f}):
Customer: {case['customer_text']}
---
"""

    prompt = f"""Customer Issue: {customer_text}

Detected Intent: {intent} (Confidence: {confidence:.2f})

Retrieved Evidence:
{evidence_text}

Based on the evidence, generate a reply."""

    try:
        response = groq_client.chat.completions.create(
            model=GENERATION_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=400
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"ERROR: {str(e)}"

# =============================================================================
# Evaluation
# =============================================================================

results = []
intent_match_count = 0
generation_errors = 0

print("=" * 70)
print("REPLY GENERATION EVALUATION")
print("=" * 70)

for i, conv in enumerate(sampled_convs):
    print(f"\n--- Sample {i+1}/{sample_size} ---")
    print(f"ID: {conv['conversation_id']}")
    print(f"Text: {conv['customer_text'][:150]}...")
    print(f"Actual Intent: {conv['primary_intent']}")

    # Classify
    intent, confidence = classify(conv['customer_text'])
    intent_match = intent == conv['primary_intent']
    intent_match_count += intent_match

    # Retrieve
    retrieved = retrieve_similar(conv['customer_text'], top_k=5)
    retrieved_intents = [r['primary_intent'] for r in retrieved]

    # Generate
    reply = generate_reply(conv['customer_text'], intent, confidence, retrieved)

    if reply.startswith("ERROR"):
        generation_errors += 1

    result = {
        'conversation_id': conv['conversation_id'],
        'customer_text': conv['customer_text'],
        'actual_intent': conv['primary_intent'],
        'predicted_intent': intent,
        'confidence': confidence,
        'intent_match': intent_match,
        'retrieved_cases': retrieved,
        'retrieved_intents': retrieved_intents,
        'generated_reply': reply
    }
    results.append(result)

    print(f"Predicted Intent: {intent} (conf: {confidence:.2f}, match: {intent_match})")
    print(f"Retrieved Intents: {retrieved_intents}")
    print(f"Reply: {reply[:200]}...")

    time.sleep(0.3)  # Rate limiting

print("\n" + "=" * 70)
print("EVALUATION SUMMARY")
print("=" * 70)

# Calculate metrics
n = len(results)
classification_accuracy = intent_match_count / n
generation_success_rate = (n - generation_errors) / n

# Intent match in top-5
top5_intent_hits = 0
for r in results:
    if r['actual_intent'] in r['retrieved_intents']:
        top5_intent_hits += 1
top5_intent_match_rate = top5_intent_hits / n

print(f"\nClassification Accuracy (on sample): {classification_accuracy:.2%} ({intent_match_count}/{n})")
print(f"Top-5 Retrieval Intent Match: {top5_intent_match_rate:.2%} ({top5_intent_hits}/{n})")
print(f"Generation Success Rate: {generation_success_rate:.2%} ({n-generation_errors}/{n})")

# Save results
output = {
    'sample_size': sample_size,
    'random_seed': 42,
    'generation_model': GENERATION_MODEL,
    'classification_accuracy': classification_accuracy,
    'top5_intent_match_rate': top5_intent_match_rate,
    'generation_success_rate': generation_success_rate,
    'results': results
}

with open('data/reply_generation/evaluation_results.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\nSaved: data/reply_generation/evaluation_results.json")

# Save examples for manual review
examples_path = 'data/reply_generation/example_outputs.json'
with open(examples_path, 'w', encoding='utf-8') as f:
    for r in results[:5]:  # First 5 examples
        f.write(json.dumps({
            'conversation_id': r['conversation_id'],
            'customer_text': r['customer_text'],
            'actual_intent': r['actual_intent'],
            'predicted_intent': r['predicted_intent'],
            'confidence': r['confidence'],
            'retrieved_cases': [
                {
                    'id': c['conversation_id'],
                    'intent': c['primary_intent'],
                    'score': c['similarity_score']
                }
                for c in r['retrieved_cases']
            ],
            'generated_reply': r['generated_reply']
        }, ensure_ascii=False) + '\n')

print(f"Saved: {examples_path}")