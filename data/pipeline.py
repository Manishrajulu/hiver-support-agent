#!/usr/bin/env python3
"""
Phase 7: Updated Pipeline with Phase 6 Model (Word+Char TF-IDF + LinearSVC)

Key changes from Phase 6 integration:
1. Uses phase6_best_model.joblib (70.56% accuracy) instead of baseline_model.joblib
2. LinearSVC confidence using margin-based approach (not predict_proba)
3. Updated escalation thresholds calibrated for LinearSVC margins
4. ORDER_MODIFY removed from HIGH_RISK (only 2 training examples, 0 in test)

Output schema:
{
    "intent": "...",
    "confidence": 0.0,
    "decision": "AUTO_HANDLE | ESCALATE",
    "reason": "...",
    "draft_reply": "..." or null,
    "evidence": [...],
    "retrieved_case_ids": [...]
}
"""

import json
import os
import sys
import logging
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from scipy.sparse import hstack
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables from project root .env file
_dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
load_dotenv(_dotenv_path)

# =============================================================================
# Configuration
# =============================================================================

# Base directory - assume script runs from project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

RAG_INDEX_DIR = os.path.join(PROJECT_ROOT, 'data', 'rag')
# Phase C model (71.11%) - BEST MODEL, do not replace
PHASEC_MODEL_PATH = os.path.join(PROJECT_ROOT, 'data', 'baseline', 'phaseC_model.joblib')
# Legacy path for backwards compatibility
PHASE6_MODEL_PATH = PHASEC_MODEL_PATH
TOP_K = 5

# Groq config
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logging.warning("Groq not available - reply generation disabled")

GENERATION_MODEL = 'qwen/qwen3.8-27b'

# =============================================================================
# ESCALATION THRESHOLDS - Calibrated for LinearSVC margins
# =============================================================================

# Margin = decision_score[predicted] - decision_score[second_best]
# This measures how close the decision boundary is

# From Phase 6 evaluation:
# - Margin < 0.5: 43.9% of predictions (high uncertainty)
# - Margin < 1.0: 66.9% of predictions
# - Mean margin: 0.768, Median: 0.603

# Escalation thresholds for LinearSVC margin-based confidence
CONF_THRESHOLD_MARGIN = 0.50  # Below this: ESCALATE
SIM_THRESHOLD = 0.30  # RAG retrieval similarity threshold (unchanged)

# HIGH_RISK intents - these always escalate regardless of confidence
# NOTE: ORDER_MODIFY removed - only 2 training examples, 0 in test set
HIGH_RISK_INTENTS = {
    'REFUND_REQUEST',
    'PAYMENT_ISSUE',
    'ACCOUNT_ACCESS',
}

# =============================================================================
# Logging Setup
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('pipeline')


# =============================================================================
# Utility Functions
# =============================================================================

def load_api_key():
    """Load Groq API key from environment variable."""
    return os.getenv("GROQ_API_KEY")


def sigmoid(x):
    """Sigmoid function for margin-to-confidence mapping."""
    return 1 / (1 + np.exp(-x))


# =============================================================================
# Component Loading
# =============================================================================

class PipelineComponents:
    """Lazy-loaded pipeline components for Phase C model."""

    def __init__(self):
        self._phasec_model = None
        self._rag_model = None
        self._rag_index = None
        self._rag_metadata = None
        self._groq_client = None
        self._loaded = False

    def load(self):
        """Load all components."""
        if self._loaded:
            return

        logger.info("Loading Phase C pipeline components...")

        # Phase C Model (Word+Char TF-IDF + LinearSVC) - 71.11% accuracy
        logger.info("Loading Phase C model from %s", PHASEC_MODEL_PATH)
        with open(PHASEC_MODEL_PATH, 'rb') as f:
            self._phasec_model = pickle.load(f)

        vec_word = self._phasec_model['vectorizer_word']
        vec_char = self._phasec_model['vectorizer_char']
        clf = self._phasec_model['classifier']

        logger.info("  Phase C model loaded:")
        logger.info("    - Word vectorizer: ngram=%s, max_features=%d",
                   vec_word.ngram_range, vec_word.max_features)
        logger.info("    - Char vectorizer: ngram=%s, max_features=%d, analyzer=%s",
                   vec_char.ngram_range, vec_char.max_features, vec_char.analyzer)
        logger.info("    - Classifier: LinearSVC(C=%.1f, class_weight=%s)",
                   clf.C, clf.class_weight)
        logger.info("    - Classes: %d", len(clf.classes_))

        # RAG index (TRAIN only for production)
        index_path = os.path.join(RAG_INDEX_DIR, 'faiss_index_train.bin')
        metadata_path = os.path.join(RAG_INDEX_DIR, 'corpus_metadata_train.jsonl')

        logger.info("Loading RAG index from %s", index_path)
        self._rag_index = faiss.read_index(index_path)

        logger.info("Loading RAG metadata from %s", metadata_path)
        self._rag_metadata = []
        with open(metadata_path, 'r', encoding='utf-8') as f:
            for line in f:
                self._rag_metadata.append(json.loads(line))
        logger.info("RAG metadata loaded: %d cases", len(self._rag_metadata))

        # RAG model
        logger.info("Loading RAG embedding model: all-MiniLM-L6-v2")
        self._rag_model = SentenceTransformer('all-MiniLM-L6-v2')

        # Groq client
        if GROQ_AVAILABLE:
            api_key = load_api_key()
            if api_key:
                self._groq_client = Groq(api_key=api_key)
                logger.info("Groq client initialized")
            else:
                logger.warning("Groq API key not found - reply generation disabled")
        else:
            logger.warning("Groq library not available - reply generation disabled")

        self._loaded = True
        logger.info("All pipeline components loaded successfully")

    @property
    def phasec_model(self):
        if not self._loaded:
            self.load()
        return self._phasec_model

    # Backwards compatibility alias
    @property
    def phase6_model(self):
        if not self._loaded:
            self.load()
        return self._phasec_model

    @property
    def rag_model(self):
        if not self._loaded:
            self.load()
        return self._rag_model

    @property
    def rag_index(self):
        if not self._loaded:
            self.load()
        return self._rag_index

    @property
    def rag_metadata(self):
        if not self._loaded:
            self.load()
        return self._rag_metadata

    @property
    def groq_client(self):
        if not self._loaded:
            self.load()
        return self._groq_client


# Global components instance
_components = PipelineComponents()


def load_components():
    """Load all components (legacy function for compatibility)."""
    _components.load()
    return _components


# =============================================================================
# Pipeline Stages
# =============================================================================

SYSTEM_PROMPT = """You are an Amazon customer service assistant. Generate helpful replies based on retrieved evidence.

IMPORTANT:
1. Only use information from the provided evidence.
2. Do NOT invent policies, refund amounts, delivery dates, or facts not in the evidence.
3. If evidence is insufficient or irrelevant, acknowledge the limitation.
4. Be empathetic and professional.
"""


def classify(conversation_text, phasec_model):
    """
    Stage 1: Classify intent using Phase C model (Word+Char TF-IDF + LinearSVC).

    Returns:
        (intent, confidence_score, margin, top_candidates)

    Note: confidence_score is sigmoid(margin) - a calibrated-like score between 0.5 and 1.0
    margin is the raw decision_function difference between top 2 classes
    """
    logger.info("Stage 1: Phase C Classification")

    vec_word = phasec_model['vectorizer_word']
    vec_char = phasec_model['vectorizer_char']
    clf = phasec_model['classifier']
    classes = clf.classes_

    try:
        # Vectorize input
        X_word = vec_word.transform([conversation_text])
        X_char = vec_char.transform([conversation_text])
        X = hstack([X_word, X_char])

        # Get decision scores (one per class)
        decision_scores = clf.decision_function(X)[0]

        # Get top prediction
        predicted_idx = np.argmax(decision_scores)
        predicted_class = classes[predicted_idx]
        predicted_score = decision_scores[predicted_idx]

        # Compute margin = difference between top and second best
        sorted_scores = np.sort(decision_scores)[::-1]
        margin = sorted_scores[0] - sorted_scores[1]

        # Convert margin to confidence-like score using sigmoid
        # This maps margin to [0.5, 1.0) range
        confidence = sigmoid(margin)

        # Get top 3 candidates for analysis
        top_indices = np.argsort(decision_scores)[::-1][:3]
        top_candidates = [
            (classes[i], decision_scores[i]) for i in top_indices
        ]

        logger.info("  Predicted intent: %s", predicted_class)
        logger.info("  Margin: %.3f, Confidence: %.3f", margin, confidence)
        logger.info("  Top-3: %s", [(c, f"{s:.2f}") for c, s in top_candidates])

        return predicted_class, float(confidence), float(margin), top_candidates

    except Exception as e:
        logger.error("  Classification failed: %s", str(e))
        raise


def retrieve_similar(query, model, index, metadata, top_k=5):
    """
    Stage 2: Retrieve similar cases using RAG.

    Returns:
        list of retrieved case dicts
    """
    logger.info("Stage 2: RAG Retrieval (top_k=%d)", top_k)

    try:
        query_vec = model.encode([query]).astype('float32')
        norm = np.linalg.norm(query_vec, axis=1, keepdims=True)
        query_vec_norm = query_vec / norm
        scores, indices = index.search(query_vec_norm, top_k)

        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx < len(metadata):
                case = {
                    'rank': i + 1,
                    'conversation_id': metadata[idx]['conversation_id'],
                    'primary_intent': metadata[idx]['primary_intent'],
                    'customer_text': metadata[idx]['customer_text'],
                    'similarity_score': float(score)
                }
                results.append(case)

        avg_sim = np.mean([r['similarity_score'] for r in results]) if results else 0
        logger.info("  Retrieved %d cases, avg similarity: %.3f", len(results), avg_sim)

        return results

    except Exception as e:
        logger.error("  Retrieval failed: %s", str(e))
        raise


def generate_reply(customer_text, intent, confidence, margin, retrieved_cases, groq_client):
    """
    Stage 3: Generate reply using Groq LLM.
    Only called when AUTO_HANDLE decision is made.

    Returns:
        draft_reply string or None on failure
    """
    logger.info("Stage 3: Reply Generation")

    if not groq_client:
        logger.warning("  Groq client not available - skipping generation")
        return None

    if not retrieved_cases:
        logger.warning("  No retrieved cases - cannot generate grounded reply")
        return None

    # Build evidence text
    evidence_text = ""
    for i, case in enumerate(retrieved_cases):
        evidence_text += f"""
Case {i+1} (Intent: {case['primary_intent']}, Similarity: {case['similarity_score']:.2f}):
Customer: {case['customer_text']}
---
"""

    prompt = f"""Customer Issue: {customer_text}

Detected Intent: {intent} (Confidence: {confidence:.2f}, Margin: {margin:.3f})

Retrieved Evidence:
{evidence_text}

Based on the evidence, generate a reply."""

    try:
        logger.debug("  Sending request to Groq...")
        response = groq_client.chat.completions.create(
            model=GENERATION_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )

        reply = response.choices[0].message.content
        logger.info("  Reply generated successfully (%d chars)", len(reply))
        return reply

    except Exception as e:
        logger.error("  Reply generation failed: %s", str(e))
        return None


def decide_escalation(intent, confidence, margin, retrieved_cases):
    """
    Stage 4: Make escalation decision using margin-based confidence.

    Policy:
    - HIGH_RISK intent → ESCALATE
    - margin < CONF_THRESHOLD_MARGIN (0.50) → ESCALATE
    - avg_sim < SIM_THRESHOLD (0.30) → ESCALATE
    - Otherwise → AUTO_HANDLE

    Note: ORDER_MODIFY is NOT in HIGH_RISK because it has only 2 training
    examples and 0 test examples - insufficient for reliable classification.

    Returns:
        {"decision": "AUTO_HANDLE|ESCALATE", "reason": "...", "risk_flags": [...]}
    """
    logger.info("Stage 4: Escalation Decision (margin-based)")

    risk_flags = []

    # Rule 1: High-risk intent
    if intent in HIGH_RISK_INTENTS:
        risk_flags.append(f"HIGH_RISK:{intent}")
        logger.info("  Risk flag: HIGH_RISK (%s)", intent)

    # Rule 2: Low margin (uncertain prediction)
    if margin < CONF_THRESHOLD_MARGIN:
        risk_flags.append(f"LOW_MARGIN:{margin:.3f}<{CONF_THRESHOLD_MARGIN}")
        logger.info("  Risk flag: LOW_MARGIN (%.3f < %.2f)", margin, CONF_THRESHOLD_MARGIN)

    # Rule 3: Weak or no evidence
    if not retrieved_cases:
        risk_flags.append("NO_EVIDENCE")
        logger.info("  Risk flag: NO_EVIDENCE")
    else:
        avg_similarity = np.mean([c['similarity_score'] for c in retrieved_cases])
        if avg_similarity < SIM_THRESHOLD:
            risk_flags.append(f"WEAK_EVIDENCE:avg={avg_similarity:.3f}<{SIM_THRESHOLD}")
            logger.info("  Risk flag: WEAK_EVIDENCE (avg=%.3f < %.2f)",
                        avg_similarity, SIM_THRESHOLD)

    # Final decision
    decision = "ESCALATE" if risk_flags else "AUTO_HANDLE"
    logger.info("  Decision: %s", decision)

    # Build reason string
    if decision == "ESCALATE":
        primary_reason = risk_flags[0]
        reason = f"ESCALATE - {primary_reason}"
        if len(risk_flags) > 1:
            reason += f" (+{len(risk_flags)-1} other factors)"
    else:
        avg_sim = np.mean([c['similarity_score'] for c in retrieved_cases]) if retrieved_cases else 0
        reason = f"AUTO_HANDLE - intent={intent}, margin={margin:.3f}, conf={confidence:.3f}, avg_sim={avg_sim:.3f}"

    return {
        "decision": decision,
        "reason": reason,
        "risk_flags": risk_flags
    }


# =============================================================================
# Main Pipeline Function
# =============================================================================

def run_pipeline(conversation_text, top_k=5, skip_generation=False):
    """
    Run the complete end-to-end pipeline with Phase C model (71.11% accuracy).

    Args:
        conversation_text: Customer conversation text
        top_k: Number of similar cases to retrieve
        skip_generation: If True, skip LLM generation (for testing/faster runs)

    Returns:
        {
            "intent": "...",
            "confidence": 0.0,
            "margin": 0.0,
            "decision": "AUTO_HANDLE | ESCALATE",
            "reason": "...",
            "draft_reply": "..." or null,
            "evidence": [...],
            "retrieved_case_ids": [...]
        }

    Raises:
        ValueError: If conversation_text is empty
        Exception: For component failures
    """
    if not conversation_text or not conversation_text.strip():
        raise ValueError("conversation_text cannot be empty")

    logger.info("=" * 60)
    logger.info("PHASE C PIPELINE START")
    logger.info("Text: %s", conversation_text[:80])
    logger.info("=" * 60)

    # Load components
    _components.load()
    phasec_model = _components.phasec_model
    rag_model = _components.rag_model
    rag_index = _components.rag_index
    rag_metadata = _components.rag_metadata
    groq_client = _components.groq_client

    # Stage 1: Classification (Phase C model - 71.11% accuracy)
    intent, confidence, margin, top_candidates = classify(conversation_text, phasec_model)

    # Stage 2: Retrieval
    retrieved_cases = retrieve_similar(
        conversation_text, rag_model, rag_index, rag_metadata, top_k
    )

    # Stage 4: Escalation decision (before generation)
    escalation = decide_escalation(intent, confidence, margin, retrieved_cases)
    decision = escalation["decision"]

    # Stage 3: Generate reply ONLY if AUTO_HANDLE
    draft_reply = None
    if decision == "AUTO_HANDLE" and not skip_generation:
        draft_reply = generate_reply(
            conversation_text, intent, confidence, margin, retrieved_cases, groq_client
        )
        if draft_reply is None:
            logger.warning("  Generation failed but decision is AUTO_HANDLE - allowing")
    elif decision == "AUTO_HANDLE" and skip_generation:
        logger.info("  Stage 3: Reply generation skipped (skip_generation=True)")

    # Build response
    response = {
        "intent": intent,
        "confidence": round(confidence, 4),
        "margin": round(margin, 4),
        "decision": decision,
        "reason": escalation["reason"],
        "draft_reply": draft_reply,
        "evidence": [
            {
                "conversation_id": case["conversation_id"],
                "intent": case["primary_intent"],
                "similarity_score": round(case["similarity_score"], 4),
                "customer_text": case["customer_text"]
            }
            for case in retrieved_cases
        ],
        "retrieved_case_ids": [case["conversation_id"] for case in retrieved_cases]
    }

    logger.info("PHASE C PIPELINE END: decision=%s, intent=%s, conf=%.3f, margin=%.3f",
                decision, intent, confidence, margin)
    logger.info("=" * 60)

    return response


def validate_response(response):
    """
    Validate that a pipeline response has the correct schema.

    Returns:
        (is_valid, error_message)
    """
    required_fields = {
        "intent": str,
        "confidence": (float, int),
        "margin": (float, int),
        "decision": str,
        "reason": str,
        "draft_reply": (str, type(None)),
        "evidence": list,
        "retrieved_case_ids": list
    }

    for field, expected_type in required_fields.items():
        if field not in response:
            return False, f"Missing required field: {field}"
        if not isinstance(response[field], expected_type):
            return False, f"Field {field} has wrong type: {type(response[field])}"

    if response["decision"] not in ("AUTO_HANDLE", "ESCALATE"):
        return False, f"Invalid decision value: {response['decision']}"

    if response["confidence"] < 0 or response["confidence"] > 1:
        return False, f"Confidence out of range: {response['confidence']}"

    if response["margin"] < 0:
        return False, f"Margin cannot be negative: {response['margin']}"

    if len(response["evidence"]) != len(response["retrieved_case_ids"]):
        return False, "Evidence and retrieved_case_ids length mismatch"

    return True, None


# =============================================================================
# Batch Processing
# =============================================================================

def run_pipeline_batch(conversations, top_k=5, skip_generation=False):
    """
    Run pipeline on a batch of conversations.

    Args:
        conversations: List of dicts with "conversation_id" and "text" keys,
                      or list of strings (uses index as ID)
        top_k: Number of cases to retrieve
        skip_generation: Skip LLM generation

    Returns:
        List of response dicts
    """
    results = []
    for i, conv in enumerate(conversations):
        conv_id = conv.get("conversation_id", f"batch_{i}") if isinstance(conv, dict) else f"batch_{i}"
        text = conv.get("text", conv) if isinstance(conv, dict) else conv

        logger.info("Processing batch item %d: %s", i, conv_id)

        try:
            response = run_pipeline(text, top_k=top_k, skip_generation=skip_generation)
            response["conversation_id"] = conv_id
            response["pipeline_status"] = "success"
        except Exception as e:
            logger.error("Pipeline failed for %s: %s", conv_id, str(e))
            response = {
                "conversation_id": conv_id,
                "pipeline_status": "error",
                "error": str(e),
                "intent": None,
                "confidence": None,
                "margin": None,
                "decision": None,
                "reason": None,
                "draft_reply": None,
                "evidence": [],
                "retrieved_case_ids": []
            }

        results.append(response)

    return results


# =============================================================================
# Main / Testing
# =============================================================================

if __name__ == '__main__':
    print("Loading Phase C pipeline components...")

    test_cases = [
        {
            "id": "test_001",
            "text": "My package was supposed to arrive yesterday but it's still not here. I'm very frustrated!",
        },
        {
            "id": "test_002",
            "text": "I want to return my order and get a refund. The item is damaged.",
        },
        {
            "id": "test_003",
            "text": "My Kindle screen is frozen and won't turn off. I've tried everything.",
        },
        {
            "id": "test_004",
            "text": "I was charged twice for my order",
        },
        {
            "id": "test_005",
            "text": "Hello?",
        },
    ]

    for tc in test_cases:
        print(f"\n{'='*70}")
        print(f"Test: {tc['id']}")
        print(f"Text: {tc['text']}")
        print()

        result = run_pipeline(tc['text'])

        print(f"Intent: {result['intent']}")
        print(f"Confidence: {result['confidence']:.3f}")
        print(f"Margin: {result['margin']:.3f}")
        print(f"Decision: {result['decision']}")
        print(f"Reason: {result['reason']}")
        print(f"Evidence: {len(result['evidence'])} cases")
        for e in result['evidence']:
            print(f"  [{e['conversation_id']}] {e['intent']} ({e['similarity_score']:.3f})")

        if result['draft_reply']:
            print(f"\nDraft Reply ({len(result['draft_reply'])} chars):")
            print(result['draft_reply'][:300])

        is_valid, err = validate_response(result)
        print(f"\nSchema valid: {is_valid}")
        if err:
            print(f"Validation error: {err}")

        print(f"{'='*70}")
