#!/usr/bin/env python3
"""
Sprint 5: Comprehensive System Evaluation

Evaluate the full pipeline: Classification → RAG → Reply Generation → Escalation
"""

import json
import os
import sys
import joblib
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from groq import Groq
from collections import Counter, defaultdict
import time

sys.stdout.reconfigure(encoding='utf-8')

# Load API key
def load_api_key():
    with open('data/api_key.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('GROQ_API_KEY='):
                return line.split('=', 1)[1].strip()
    return None

GROQ_API_KEY = load_api_key()
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# =============================================================================
# Load Components
# =============================================================================

print("Loading components...")

# Classifier
classifier = joblib.load('data/baseline/baseline_model.joblib')

# RAG
rag_index = faiss.read_index('data/rag/faiss_index_train.bin')
rag_metadata = []
with open('data/rag/corpus_metadata_train.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        rag_metadata.append(json.loads(line))
rag_model = SentenceTransformer('all-MiniLM-L6-v2')

# Test split
with open('data/baseline/baseline_train_test_split.json', 'r') as f:
    split = json.load(f)
test_ids = set(split['test_ids'])

# Load test conversations
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

# =============================================================================
# 1. CLASSIFICATION EVALUATION (Full test set)
# =============================================================================

print("\n" + "="*70)
print("1. CLASSIFICATION EVALUATION")
print("="*70)

y_true = []
y_pred = []
y_proba = []

for conv in test_convs:
    proba = classifier.predict_proba([conv['customer_text']])[0]
    pred_class = classifier.classes_[np.argmax(proba)]
    y_true.append(conv['primary_intent'])
    y_pred.append(pred_class)
    y_proba.append(float(np.max(proba)))

# Calculate metrics
intents = sorted(set(y_true))
per_intent = {}

for intent in intents:
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == intent and p == intent)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t != intent and p == intent)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == intent and p != intent)
    support = sum(1 for t in y_true if t == intent)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    per_intent[intent] = {
        'precision': precision, 'recall': recall, 'f1': f1, 'support': support,
        'tp': tp, 'fp': fp, 'fn': fn
    }

# Macro/weighted metrics
accuracy = sum(1 for t, p in zip(y_true, y_pred) if t == p) / len(y_true)
macro_precision = sum(p['precision'] for p in per_intent.values()) / len(per_intent)
macro_recall = sum(p['recall'] for p in per_intent.values()) / len(per_intent)
macro_f1 = sum(p['f1'] for p in per_intent.values()) / len(per_intent)

# Weighted metrics
total_support = sum(p['support'] for p in per_intent.values())
weighted_precision = sum(p['precision'] * p['support'] for p in per_intent.values()) / total_support
weighted_recall = sum(p['recall'] * p['support'] for p in per_intent.values()) / total_support
weighted_f1 = sum(p['f1'] * p['support'] for p in per_intent.values()) / total_support

print(f"\nAccuracy: {accuracy:.4f}")
print(f"Macro F1: {macro_f1:.4f}")
print(f"Weighted F1: {weighted_f1:.4f}")

print(f"\nPer-intent F1:")
for intent in sorted(per_intent.keys()):
    p = per_intent[intent]
    print(f"  {intent:<20}: P={p['precision']:.3f} R={p['recall']:.3f} F1={p['f1']:.3f} (n={p['support']})")

# Confusion matrix (top errors)
confusions = Counter()
for t, p in zip(y_true, y_pred):
    if t != p:
        confusions[f"{t}→{p}"] += 1

print(f"\nTop 10 Classification Confusions:")
for pair, count in confusions.most_common(10):
    print(f"  {pair}: {count}")

classification_metrics = {
    'accuracy': accuracy,
    'macro_f1': macro_f1,
    'weighted_f1': weighted_f1,
    'per_intent': per_intent,
    'confusions': dict(confusions.most_common(20)),
    'test_size': len(test_convs)
}

# =============================================================================
# 2. RETRIEVAL EVALUATION (Full test set)
# =============================================================================

print("\n" + "="*70)
print("2. RETRIEVAL EVALUATION")
print("="*70)

def retrieve_similar(query, top_k=5):
    query_vec = rag_model.encode([query]).astype('float32')
    norm = np.linalg.norm(query_vec, axis=1, keepdims=True)
    query_vec_norm = query_vec / norm
    scores, indices = rag_index.search(query_vec_norm, top_k)
    results = []
    for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
        if idx < len(rag_metadata):
            meta = rag_metadata[idx]
            results.append({
                'rank': i + 1,
                'conversation_id': meta['conversation_id'],
                'primary_intent': meta['primary_intent'],
                'customer_text': meta['customer_text'],
                'similarity_score': float(score)
            })
    return results

top1_match = 0
top3_match = 0
top5_match = 0
total = len(test_convs)

for conv in test_convs:
    retrieved = retrieve_similar(conv['customer_text'], top_k=5)
    retrieved_intents = [r['primary_intent'] for r in retrieved]
    actual_intent = conv['primary_intent']

    if retrieved_intents and retrieved_intents[0] == actual_intent:
        top1_match += 1
    if actual_intent in retrieved_intents[:3]:
        top3_match += 1
    if actual_intent in retrieved_intents:
        top5_match += 1

print(f"\nTop-1 Intent Match: {top1_match}/{total} = {top1_match/total:.4f}")
print(f"Top-3 Intent Match: {top3_match}/{total} = {top3_match/total:.4f}")
print(f"Top-5 Intent Match: {top5_match}/{total} = {top5_match/total:.4f}")

# Average similarity scores
avg_top1_sim = []
for conv in test_convs:
    retrieved = retrieve_similar(conv['customer_text'], top_k=1)
    if retrieved:
        avg_top1_sim.append(retrieved[0]['similarity_score'])

print(f"\nAvg Top-1 Similarity: {np.mean(avg_top1_sim):.4f}")

retrieval_metrics = {
    'top1_match_rate': top1_match / total,
    'top3_match_rate': top3_match / total,
    'top5_match_rate': top5_match / total,
    'avg_top1_similarity': float(np.mean(avg_top1_sim)),
    'test_size': total
}

# =============================================================================
# 3. REPLY GENERATION + ESCALATION (Sample)
# =============================================================================

print("\n" + "="*70)
print("3. REPLY GENERATION + ESCALATION EVALUATION")
print("="*70)

import random
random.seed(42)
sample_size = 30
sampled_convs = random.sample(test_convs, sample_size)

# Escalation config
HIGH_RISK_INTENTS = {'REFUND_REQUEST', 'PAYMENT_ISSUE', 'ACCOUNT_ACCESS', 'ORDER_MODIFY'}

def decide_escalation(intent, confidence, retrieved_cases):
    risk_flags = []
    if intent in HIGH_RISK_INTENTS:
        risk_flags.append(f"HIGH_RISK:{intent}")
    if confidence < 0.3:
        risk_flags.append(f"LOW_CONF:{confidence:.3f}")
    if not retrieved_cases:
        risk_flags.append("NO_EVIDENCE")
    else:
        avg_sim = sum(c['similarity_score'] for c in retrieved_cases) / len(retrieved_cases)
        if avg_sim < 0.4:
            risk_flags.append(f"WEAK_EVIDENCE:avg={avg_sim:.3f}")
    return "ESCALATE" if risk_flags else "AUTO_HANDLE", risk_flags

SYSTEM_PROMPT = """You are an Amazon customer service assistant. Generate helpful replies based on retrieved evidence.
IMPORTANT: Only use information from the provided evidence. Do NOT invent policies, refund amounts, delivery dates, or facts not in the evidence.
If evidence is insufficient, acknowledge the limitation. Be empathetic and professional."""

def generate_reply(customer_text, intent, confidence, retrieved_cases):
    evidence_text = ""
    for i, case in enumerate(retrieved_cases):
        evidence_text += f"\nCase {i+1} (Intent: {case['primary_intent']}, Similarity: {case['similarity_score']:.2f}):\nCustomer: {case['customer_text']}\n---"

    prompt = f"""Customer Issue: {customer_text}
Detected Intent: {intent} (Confidence: {confidence:.2f})
Retrieved Evidence:{evidence_text}
Based on the evidence, generate a reply."""

    try:
        response = groq_client.chat.completions.create(
            model='qwen/qwen3.8-27b',
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
            temperature=0.3, max_tokens=400
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"ERROR: {str(e)}"

e2e_results = []
escalation_counts = Counter()
auto_handle_correct = 0
auto_handle_total = 0

print(f"\nEvaluating {sample_size} sampled conversations...")

for conv in sampled_convs:
    # Classify
    proba = classifier.predict_proba([conv['customer_text']])[0]
    pred_intent = classifier.classes_[np.argmax(proba)]
    confidence = float(np.max(proba))

    # Retrieve
    retrieved = retrieve_similar(conv['customer_text'], top_k=5)

    # Generate
    draft_reply = generate_reply(conv['customer_text'], pred_intent, confidence, retrieved) if groq_client else "GROQ_NOT_AVAILABLE"

    # Escalation
    decision, risk_flags = decide_escalation(pred_intent, confidence, retrieved)
    escalation_counts[decision] += 1

    if decision == "AUTO_HANDLE":
        auto_handle_total += 1
        if pred_intent == conv['primary_intent']:
            auto_handle_correct += 1

    e2e_results.append({
        'conversation_id': conv['conversation_id'],
        'actual_intent': conv['primary_intent'],
        'predicted_intent': pred_intent,
        'confidence': confidence,
        'retrieved_case_ids': [r['conversation_id'] for r in retrieved],
        'retrieval_scores': [r['similarity_score'] for r in retrieved],
        'draft_reply': draft_reply,
        'escalation_decision': decision,
        'risk_flags': risk_flags
    })

    time.sleep(0.2)

print(f"\nEscalation Summary:")
for decision, count in escalation_counts.items():
    print(f"  {decision}: {count}/{sample_size} = {count/sample_size:.1%}")

if auto_handle_total > 0:
    print(f"\nAUTO_HANDLE Correctness: {auto_handle_correct}/{auto_handle_total} = {auto_handle_correct/auto_handle_total:.1%}")
else:
    print("\nNo AUTO_HANDLE cases")

# =============================================================================
# 4. FAILURE ANALYSIS
# =============================================================================

print("\n" + "="*70)
print("4. FAILURE ANALYSIS")
print("="*70)

failures = {
    'classification_errors': [],
    'retrieval_failures': [],
    'escalation_errors': []
}

for r in e2e_results:
    # Classification errors
    if r['predicted_intent'] != r['actual_intent']:
        failures['classification_errors'].append({
            'id': r['conversation_id'],
            'actual': r['actual_intent'],
            'predicted': r['predicted_intent'],
            'confidence': r['confidence']
        })

    # Retrieval failures (low similarity)
    if r['retrieval_scores'] and max(r['retrieval_scores']) < 0.5:
        failures['retrieval_failures'].append({
            'id': r['conversation_id'],
            'max_similarity': max(r['retrieval_scores'])
        })

    # Escalation issues
    if r['escalation_decision'] == 'AUTO_HANDLE' and r['predicted_intent'] != r['actual_intent']:
        failures['escalation_errors'].append({
            'id': r['conversation_id'],
            'actual': r['actual_intent'],
            'predicted': r['predicted_intent'],
            'reason': 'AUTO_HANDLE but wrong intent'
        })

print(f"\nClassification Errors: {len(failures['classification_errors'])}")
print(f"Retrieval Failures (low sim): {len(failures['retrieval_failures'])}")
print(f"Escalation Errors: {len(failures['escalation_errors'])}")

# =============================================================================
# Save Results
# =============================================================================

print("\n" + "="*70)
print("SAVING RESULTS")
print("="*70)

# Classification metrics
with open('data/evaluation/sprint5_classification_metrics.json', 'w') as f:
    json.dump(classification_metrics, f, indent=2)
print("Saved: data/evaluation/sprint5_classification_metrics.json")

# Retrieval metrics
with open('data/evaluation/sprint5_retrieval_metrics.json', 'w') as f:
    json.dump(retrieval_metrics, f, indent=2)
print("Saved: data/evaluation/sprint5_retrieval_metrics.json")

# Escalation metrics
escalation_metrics = {
    'sample_size': sample_size,
    'escalation_counts': dict(escalation_counts),
    'auto_handle_total': auto_handle_total,
    'auto_handle_correct': auto_handle_correct,
    'auto_handle_accuracy': auto_handle_correct / auto_handle_total if auto_handle_total > 0 else 0
}
with open('data/evaluation/sprint5_escalation_metrics.json', 'w') as f:
    json.dump(escalation_metrics, f, indent=2)
print("Saved: data/evaluation/sprint5_escalation_metrics.json")

# End-to-end results
with open('data/evaluation/sprint5_end_to_end_results.jsonl', 'w', encoding='utf-8') as f:
    for r in e2e_results:
        f.write(json.dumps(r, ensure_ascii=False) + '\n')
print("Saved: data/evaluation/sprint5_end_to_end_results.jsonl")

# Failure analysis
with open('data/evaluation/sprint5_failure_analysis.json', 'w') as f:
    json.dump(failures, f, indent=2)
print("Saved: data/evaluation/sprint5_failure_analysis.json")

print("\n" + "="*70)
print("EVALUATION COMPLETE")
print("="*70)