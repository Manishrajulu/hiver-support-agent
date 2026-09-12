#!/usr/bin/env python3
"""
Sprint 3: Reply Generation

Given a customer conversation:
1. Use classifier to get intent + confidence
2. Use RAG to retrieve similar historical cases
3. Generate reply grounded in retrieved cases
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

# Initialize Groq client
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Constants
RAG_INDEX_DIR = 'data/rag'
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
CLASSIFIER_PATH = 'data/baseline/baseline_model.joblib'
TOP_K = 5
GENERATION_MODEL = 'qwen/qwen3.8-27b'

# =============================================================================
# RAG Retrieval (from Sprint 2)
# =============================================================================

def load_rag_index():
    """Load the FAISS index and metadata."""
    config_path = os.path.join(RAG_INDEX_DIR, 'config_train.json')
    index_path = os.path.join(RAG_INDEX_DIR, 'faiss_index_train.bin')
    metadata_path = os.path.join(RAG_INDEX_DIR, 'corpus_metadata_train.jsonl')

    with open(config_path, 'r') as f:
        config = json.load(f)

    index = faiss.read_index(index_path)

    metadata = []
    with open(metadata_path, 'r', encoding='utf-8') as f:
        for line in f:
            metadata.append(json.loads(line))

    model = SentenceTransformer(EMBEDDING_MODEL)

    return model, index, metadata, config

def retrieve_similar(query, model, index, metadata, top_k=5):
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

# =============================================================================
# Classification
# =============================================================================

def load_classifier():
    """Load the TF-IDF + Logistic Regression classifier."""
    return joblib.load(CLASSIFIER_PATH)

def classify(conversation_text, classifier):
    """Get intent and confidence from classifier."""
    proba = classifier.predict_proba([conversation_text])[0]
    predicted_class = classifier.classes_[np.argmax(proba)]
    confidence = float(np.max(proba))
    return predicted_class, confidence

# =============================================================================
# Reply Generation
# =============================================================================

SYSTEM_PROMPT = """You are an Amazon customer service assistant. Your task is to generate helpful, accurate responses to customer inquiries based on the retrieved historical conversations.

IMPORTANT RULES:
1. ONLY use information from the provided "Retrieved Evidence" to generate your reply.
2. Do NOT invent policies, refund amounts, delivery dates, guarantees, or facts not supported by the evidence.
3. If the retrieved evidence is insufficient or unrelated, say so clearly.
4. Be empathetic, professional, and helpful.
5. If you cannot help based on the evidence, acknowledge the limitation.

Response format:
- Start with acknowledging the customer's issue
- Provide helpful information based on the evidence
- If action is needed, suggest next steps
- Keep the response concise but complete
"""

def build_generation_prompt(customer_text, intent, confidence, retrieved_cases):
    """Build the prompt for reply generation."""

    # Format retrieved cases
    evidence_text = ""
    for i, case in enumerate(retrieved_cases):
        evidence_text += f"""
Case {i+1} (Intent: {case['primary_intent']}, Similarity: {case['similarity_score']:.2f}):
Customer: {case['customer_text']}
---
"""

    prompt = f"""Customer Issue: {customer_text}

Detected Intent: {intent} (Confidence: {confidence:.2f})

Retrieved Evidence (from similar past conversations):
{evidence_text}

Based on the retrieved evidence above, generate a helpful reply to the customer's issue.

Remember:
- Only use information from the retrieved evidence
- Do not invent facts not supported by the evidence
- Be empathetic and professional
"""

    return prompt

def generate_reply(customer_text, intent, confidence, retrieved_cases, model=GENERATION_MODEL):
    """Generate a reply grounded in retrieved cases."""
    if not groq_client:
        return {"error": "Groq API client not initialized"}

    prompt = build_generation_prompt(customer_text, intent, confidence, retrieved_cases)

    try:
        response = groq_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )

        return {
            "reply": response.choices[0].message.content,
            "model": model,
            "prompt_tokens": response.usage.prompt_tokens if hasattr(response, 'usage') else None,
            "completion_tokens": response.usage.completion_tokens if hasattr(response, 'usage') else None
        }
    except Exception as e:
        return {"error": str(e)}

# =============================================================================
# Full Pipeline
# =============================================================================

def analyze_conversation(conversation_text, top_k=5):
    """
    Full pipeline:
    1. Classify intent
    2. Retrieve similar cases
    3. Generate reply

    Returns structured output:
    {
        "intent": "...",
        "confidence": 0.xx,
        "draft_reply": "...",
        "evidence": [...],
        "retrieved_case_ids": [...]
    }
    """
    # Load components
    classifier = load_classifier()
    rag_model, rag_index, rag_metadata, rag_config = load_rag_index()

    # Step 1: Classify
    intent, confidence = classify(conversation_text, classifier)

    # Step 2: Retrieve similar cases
    retrieved_cases = retrieve_similar(conversation_text, rag_model, rag_index, rag_metadata, top_k)

    # Step 3: Generate reply
    generation_result = generate_reply(conversation_text, intent, confidence, retrieved_cases)

    # Build response
    response = {
        "intent": intent,
        "confidence": confidence,
        "draft_reply": generation_result.get("reply", generation_result.get("error", "Generation failed")),
        "evidence": [
            {
                "conversation_id": case["conversation_id"],
                "intent": case["primary_intent"],
                "similarity_score": case["similarity_score"],
                "customer_text": case["customer_text"]
            }
            for case in retrieved_cases
        ],
        "retrieved_case_ids": [case["conversation_id"] for case in retrieved_cases]
    }

    return response

# =============================================================================
# Main / Testing
# =============================================================================

if __name__ == '__main__':
    print("Loading components...")

    # Test on sample conversations
    test_cases = [
        {
            "conversation_id": "test_001",
            "text": "My package was supposed to arrive yesterday but it's still not here. I'm very frustrated!"
        },
        {
            "conversation_id": "test_002",
            "text": "I want to return my order and get a refund. The item is damaged."
        },
        {
            "conversation_id": "test_003",
            "text": "My Kindle screen is frozen and won't turn off. I've tried everything."
        },
    ]

    for tc in test_cases:
        print(f"\n{'='*70}")
        print(f"Test Case: {tc['conversation_id']}")
        print(f"Customer: {tc['text']}")
        print()

        result = analyze_conversation(tc['text'])

        print(f"Intent: {result['intent']}")
        print(f"Confidence: {result['confidence']:.3f}")
        print(f"\nRetrieved Cases:")
        for case in result['evidence']:
            print(f"  [{case['conversation_id']}] {case['intent']} (score: {case['similarity_score']:.2f})")

        print(f"\nGenerated Reply:")
        print(result['draft_reply'])

        print(f"\n{'='*70}")