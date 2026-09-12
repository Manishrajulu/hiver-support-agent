#!/usr/bin/env python3
"""
Sprint 4: Escalation Decision Evaluation

Evaluate escalation decisions on test conversations.
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

RAG_INDEX_DIR = 'data/rag'
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
CLASSIFIER_PATH = 'data/baseline/baseline_model.joblib'

# Load components
print("Loading components...")
classifier = joblib.load(CLASSIFIER_PATH)

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

print(f"Loaded {len(test_convs)} test conversations")

# Sample for evaluation
import random
random.seed(42)
sample_size = 50
sampled_convs = random.sample(test_convs, sample_size)

print(f"Evaluating on {sample_size} sampled test conversations...")

# =============================================================================
# Escalation Decision (from escalation_decision.py)
# =============================================================================

HIGH_RISK_INTENTS = {'REFUND_REQUEST', 'PAYMENT_ISSUE', 'ACCOUNT_ACCESS', 'ORDER_MODIFY'}

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

def decide_escalation(intent, confidence, retrieved_cases):
    risk_flags = []

    if intent in HIGH_RISK_INTENTS:
        risk_flags.append(f"HIGH_RISK:{intent}")

    if confidence < 0.3:
        risk_flags.append(f"LOW_CONF:{confidence:.3f}")

    if not retrieved_cases:
        risk_flags.append("NO_EVIDENCE")
    else:
        avg_similarity = sum(c['similarity_score'] for c in retrieved_cases) / len(retrieved_cases)
        if avg_similarity < 0.4:
            risk_flags.append(f"WEAK_EVIDENCE:avg={avg_similarity:.3f}")

    decision = "ESCALATE" if risk_flags else "AUTO_HANDLE"

    return {
        "decision": decision,
        "risk_flags": risk_flags,
        "confidence": confidence,
        "intent": intent
    }

# =============================================================================
# Evaluation
# =============================================================================

results = []
escalation_counts = Counter()
intent_escalation = Counter()

print("\n" + "=" * 70)
print("ESCALATION DECISION EVALUATION")
print("=" * 70)

for i, conv in enumerate(sampled_convs):
    intent, confidence = classify(conv['customer_text'])
    retrieved = retrieve_similar(conv['customer_text'], top_k=5)
    escalation = decide_escalation(intent, confidence, retrieved)

    results.append({
        'conversation_id': conv['conversation_id'],
        'actual_intent': conv['primary_intent'],
        'predicted_intent': intent,
        'confidence': confidence,
        'decision': escalation['decision'],
        'risk_flags': escalation['risk_flags']
    })

    escalation_counts[escalation['decision']] += 1
    intent_escalation[(conv['primary_intent'], escalation['decision'])] += 1

print(f"\n=== ESCALATION SUMMARY ===")
for decision, count in escalation_counts.items():
    print(f"  {decision}: {count}/{len(results)} = {count/len(results):.1%}")

print(f"\n=== PER-INTENT ESCALATION RATE ===")
intent_totals = Counter(r['actual_intent'] for r in results)
for intent in sorted(intent_totals.keys()):
    total = intent_totals[intent]
    escalated = sum(1 for r in results if r['actual_intent'] == intent and r['decision'] == 'ESCALATE')
    esc_rate = escalated / total if total > 0 else 0
    print(f"  {intent:<20}: {escalated:>3}/{total:<3} ({esc_rate:.0%})")

# Auto-handle analysis
auto_handle = [r for r in results if r['decision'] == 'AUTO_HANDLE']
print(f"\n=== AUTO_HANDLE CASES ANALYSIS ===")
print(f"Total AUTO_HANDLE: {len(auto_handle)}")

# Check if AUTO_HANDLE cases have high confidence and correct intent
auto_correct = sum(1 for r in auto_handle if r['predicted_intent'] == r['actual_intent'])
auto_high_conf = sum(1 for r in auto_handle if r['confidence'] >= 0.5)
print(f"AUTO_HANDLE with correct intent: {auto_correct}/{len(auto_handle)} = {auto_correct/len(auto_handle):.1%}" if auto_handle else "N/A")
print(f"AUTO_HANDLE with high confidence (>=0.5): {auto_high_conf}/{len(auto_handle)}" if auto_handle else "N/A")

# Escalate analysis
escalate = [r for r in results if r['decision'] == 'ESCALATE']
print(f"\n=== ESCALATE CASES ANALYSIS ===")
print(f"Total ESCALATE: {len(escalate)}")

# Why escalated?
flag_counts = Counter()
for r in escalate:
    for flag in r['risk_flags']:
        flag_counts[flag] += 1

print("Top reasons for escalation:")
for flag, count in flag_counts.most_common(10):
    print(f"  {flag}: {count}")

# Save results
output = {
    'sample_size': sample_size,
    'escalation_counts': dict(escalation_counts),
    'intent_escalation': {f"{k[0]}|{k[1]}": v for k, v in intent_escalation.items()},
    'results': results
}

with open('data/escalation/evaluation_results.json', 'w') as f:
    json.dump(output, f, indent=2)

print(f"\nSaved: data/escalation/evaluation_results.json")