#!/usr/bin/env python3
"""
Sprint 4: Escalation Decision Engine

Decide whether to AUTO_HANDLE or ESCALATE based on:
- Classification confidence
- Intent type (high-risk)
- Retrieval evidence quality
"""

import json
import os
import sys
import joblib
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from groq import Groq
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables from project root .env file
_dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
load_dotenv(_dotenv_path)

# =============================================================================
# Configuration
# =============================================================================

# High-risk intents that should always be escalated
HIGH_RISK_INTENTS = {
    'REFUND_REQUEST',      # Financial impact
    'PAYMENT_ISSUE',       # Financial impact
    'ACCOUNT_ACCESS',      # Security sensitive
    'ORDER_MODIFY',        # Complex changes
}

# Confidence thresholds
HIGH_CONFIDENCE_THRESHOLD = 0.6
MEDIUM_CONFIDENCE_THRESHOLD = 0.35

# Retrieval quality thresholds
HIGH_SIMILARITY_THRESHOLD = 0.7
LOW_SIMILARITY_THRESHOLD = 0.5

# Evidence sufficiency (at least 1 high-similarity case with matching intent)
MIN_EVIDENCE_SCORE = 0.5

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

RAG_INDEX_DIR = 'data/rag'
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
CLASSIFIER_PATH = 'data/baseline/baseline_model.joblib'

# =============================================================================
# Escalation Decision Logic
# =============================================================================

def decide_escalation(intent, confidence, retrieved_cases):
    """
    Decide whether to AUTO_HANDLE or ESCALATE.

    Decision rules:
    1. HIGH-RISK intent → ESCALATE
    2. LOW confidence (< 0.25) → ESCALATE
    3. NO evidence or VERY WEAK evidence (avg similarity < 0.3) → ESCALATE
    4. ELSE → AUTO_HANDLE

    Returns:
        decision: "AUTO_HANDLE" or "ESCALATE"
        reason: Explanation of the decision
        risk_flags: List of risk factors identified
    """

    risk_flags = []

    # Rule 1: High-risk intent
    if intent in HIGH_RISK_INTENTS:
        risk_flags.append(f"HIGH_RISK:{intent}")

    # Rule 2: Low confidence
    if confidence < 0.25:
        risk_flags.append(f"LOW_CONF:{confidence:.3f}")

    # Rule 3: Weak or no evidence
    if not retrieved_cases:
        risk_flags.append("NO_EVIDENCE")
    else:
        avg_similarity = sum(c['similarity_score'] for c in retrieved_cases) / len(retrieved_cases)
        if avg_similarity < 0.3:
            risk_flags.append(f"WEAK_EVIDENCE:avg={avg_similarity:.3f}")

    # Final decision
    decision = "ESCALATE" if risk_flags else "AUTO_HANDLE"

    # Build reason
    if decision == "ESCALATE":
        primary_reason = risk_flags[0]
        reason = f"ESCALATE - {primary_reason}"
        if len(risk_flags) > 1:
            reason += f" (+{len(risk_flags)-1} other factors)"
    else:
        reason = f"AUTO_HANDLE - conf={confidence:.3f}, intent={intent}"

    avg_sim = sum(c['similarity_score'] for c in retrieved_cases) / len(retrieved_cases) if retrieved_cases else 0
    max_sim = max(c['similarity_score'] for c in retrieved_cases) if retrieved_cases else 0

    return {
        "decision": decision,
        "reason": reason,
        "risk_flags": risk_flags,
        "confidence": confidence,
        "intent": intent,
        "evidence_summary": {
            "case_count": len(retrieved_cases),
            "avg_similarity": round(avg_sim, 3),
            "max_similarity": round(max_sim, 3)
        }
    }

# =============================================================================
# Full Pipeline with Escalation
# =============================================================================

def load_components():
    """Load all components."""
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

    return classifier, rag_model, rag_index, rag_metadata

def retrieve_similar(query, model, index, metadata, top_k=5):
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

def classify(conversation_text, classifier):
    proba = classifier.predict_proba([conversation_text])[0]
    predicted_class = classifier.classes_[np.argmax(proba)]
    confidence = float(np.max(proba))
    return predicted_class, confidence

SYSTEM_PROMPT = """You are an Amazon customer service assistant. Generate helpful replies based on retrieved evidence.

IMPORTANT:
1. Only use information from the provided evidence.
2. Do NOT invent policies, refund amounts, delivery dates, or facts not in the evidence.
3. If evidence is insufficient or irrelevant, acknowledge the limitation.
4. Be empathetic and professional.
"""

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
            model='qwen/qwen3.8-27b',
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

def analyze_conversation_with_escalation(conversation_text, top_k=5):
    """
    Full pipeline with escalation decision:
    1. Classify intent
    2. Retrieve similar cases
    3. Generate reply
    4. Decide escalation

    Returns structured output:
    {
        "intent": "...",
        "confidence": 0.xx,
        "draft_reply": "...",
        "evidence": [...],
        "retrieved_case_ids": [...],
        "escalation": {
            "decision": "AUTO_HANDLE|ESCALATE",
            "reason": "...",
            "risk_flags": [...],
            "evidence_summary": {...}
        }
    }
    """
    classifier, rag_model, rag_index, rag_metadata = load_components()

    # Step 1: Classify
    intent, confidence = classify(conversation_text, classifier)

    # Step 2: Retrieve
    retrieved_cases = retrieve_similar(conversation_text, rag_model, rag_index, rag_metadata, top_k)

    # Step 3: Generate reply (if AUTO_HANDLE)
    draft_reply = None
    if groq_client:
        draft_reply = generate_reply(conversation_text, intent, confidence, retrieved_cases)

    # Step 4: Escalation decision
    escalation = decide_escalation(intent, confidence, retrieved_cases)

    # Build response
    response = {
        "intent": intent,
        "confidence": confidence,
        "draft_reply": draft_reply,
        "evidence": [
            {
                "conversation_id": case["conversation_id"],
                "intent": case["primary_intent"],
                "similarity_score": case["similarity_score"],
                "customer_text": case["customer_text"]
            }
            for case in retrieved_cases
        ],
        "retrieved_case_ids": [case["conversation_id"] for case in retrieved_cases],
        "escalation": escalation
    }

    return response

# =============================================================================
# Testing
# =============================================================================

if __name__ == '__main__':
    print("Loading components...")

    test_cases = [
        {
            "id": "test_001",
            "text": "My package was supposed to arrive yesterday but it's still not here. I'm very frustrated!",
            "expected_decision": "AUTO_HANDLE"
        },
        {
            "id": "test_002",
            "text": "I want to return my order and get a refund. The item is damaged.",
            "expected_decision": "ESCALATE"  # REFUND_REQUEST is high-risk
        },
        {
            "id": "test_003",
            "text": "My Kindle screen is frozen and won't turn off. I've tried everything.",
            "expected_decision": "AUTO_HANDLE"
        },
        {
            "id": "test_004",
            "text": "I was charged twice for my order",
            "expected_decision": "ESCALATE"  # PAYMENT_ISSUE is high-risk
        },
        {
            "id": "test_005",
            "text": "Hello?",
            "expected_decision": "ESCALATE"  # Very low confidence
        },
    ]

    for tc in test_cases:
        print(f"\n{'='*70}")
        print(f"Test: {tc['id']}")
        print(f"Text: {tc['text']}")
        print(f"Expected: {tc['expected_decision']}")
        print()

        result = analyze_conversation_with_escalation(tc['text'])

        print(f"Intent: {result['intent']}")
        print(f"Confidence: {result['confidence']:.3f}")
        print(f"Escalation: {result['escalation']['decision']}")
        print(f"Reason: {result['escalation']['reason']}")
        print(f"Risk Flags: {result['escalation']['risk_flags']}")
        print(f"Evidence: avg_sim={result['escalation']['evidence_summary']['avg_similarity']}, "
              f"max_sim={result['escalation']['evidence_summary']['max_similarity']}, "
              f"intent_match={result['escalation']['evidence_summary']['intent_match_rate']}")

        if result['draft_reply'] and not result['draft_reply'].startswith("ERROR"):
            print(f"\nDraft Reply: {result['draft_reply'][:200]}...")

        print(f"\n{'='*70}")