#!/usr/bin/env python3
"""
Sprint 6: Pipeline Test Suite

Tests the end-to-end pipeline on existing evaluation data.
Tests at least 30-50 conversations and reports:
- successful pipeline runs
- AUTO_HANDLE rate
- ESCALATE rate
- classifier confidence distribution
- retrieval evidence quality
- generation success rate
- failures/errors
"""

import json
import os
import sys
import logging
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

# Set up paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
EVAL_DIR = os.path.join(DATA_DIR, 'evaluation')

# Set up logging to file
log_file = f"{EVAL_DIR}/sprint6_test_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('test_pipeline')

# Import pipeline
from pipeline import run_pipeline, validate_response, _components


# =============================================================================
# Test Data Loading
# =============================================================================

def load_test_conversations(n=None):
    """Load conversations from sprint5_end_to_end_results.jsonl for testing."""
    test_data = []

    with open(f'{EVAL_DIR}/sprint5_end_to_end_results.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            test_data.append({
                "conversation_id": data["conversation_id"],
                "text": data.get("customer_text", ""),  # May not be in e2e results
                "actual_intent": data.get("actual_intent"),
                "predicted_intent": data.get("predicted_intent"),
                "confidence": data.get("confidence"),
            })

    # If customer_text is empty, we need to get it from the corpus
    # For now, filter to those with actual data
    logger.info("Loaded %d conversations from e2e results", len(test_data))

    return test_data[:n] if n else test_data


def load_conversations_from_corpus(conversation_ids, corpus_path=None):
    if corpus_path is None:
        corpus_path = f'{DATA_DIR}/rag/corpus_metadata_train.jsonl'
    """Load conversation text from corpus by ID."""
    id_to_text = {}
    with open(corpus_path, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            id_to_text[data['conversation_id']] = data.get('customer_text', '')

    results = []
    missing = 0
    for cid in conversation_ids:
        if cid in id_to_text:
            results.append(cid)
        else:
            missing += 1

    if missing > 0:
        logger.warning("Could not find text for %d conversation IDs", missing)

    return results


def load_test_data_from_corpus(n=50, corpus_path=None):
    if corpus_path is None:
        corpus_path = f'{DATA_DIR}/processed/amazonhelp_labeled_conversations_v21.jsonl'
    """
    Load test conversations from the labeled corpus.
    Uses the TEST split (excludes training IDs).
    """
    # Get test IDs from baseline split
    with open(f'{DATA_DIR}/baseline/baseline_train_test_split.json', 'r') as f:
        split = json.load(f)
    test_ids = set(split.get('test_ids', []))

    logger.info("Found %d test IDs in baseline split", len(test_ids))

    # Load conversations and extract customer text from turns
    conversations = []
    with open(corpus_path, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            cid = data.get('conversation_id')
            if cid in test_ids:
                # Extract customer text from turns
                customer_texts = []
                for turn in data.get('turns', []):
                    if turn.get('speaker') == 'Customer' and turn.get('inbound'):
                        customer_texts.append(turn.get('text', ''))
                customer_text = ' '.join(customer_texts)

                if customer_text.strip():  # Only include if we have actual text
                    conversations.append({
                        "conversation_id": cid,
                        "text": customer_text,
                        "actual_intent": data.get('primary_intent'),
                    })

    logger.info("Loaded %d test conversations from corpus", len(conversations))

    # Return first n, stratified if possible
    return conversations[:n]


# =============================================================================
# Test Execution
# =============================================================================

def run_tests(conversations, skip_generation=False, max_tests=None):
    """
    Run pipeline on test conversations and collect metrics.
    """
    if max_tests:
        conversations = conversations[:max_tests]

    logger.info("=" * 70)
    logger.info("RUNNING PIPELINE TESTS ON %d CONVERSATIONS", len(conversations))
    logger.info("Skip generation: %s", skip_generation)
    logger.info("=" * 70)

    # Pre-load components once
    logger.info("Pre-loading pipeline components...")
    _components.load()
    logger.info("Components loaded successfully")

    results = []
    errors = []
    schema_errors = []

    for i, conv in enumerate(conversations):
        cid = conv.get('conversation_id', f'conv_{i}')
        text = conv.get('text', '')

        if not text:
            logger.warning("Skipping %s - no text", cid)
            errors.append({"id": cid, "error": "No text available"})
            continue

        logger.info(f"[{i+1}/{len(conversations)}] Processing: {cid}")

        try:
            response = run_pipeline(text, top_k=5, skip_generation=skip_generation)

            # Validate schema
            is_valid, err = validate_response(response)
            if not is_valid:
                logger.error("Schema validation failed for %s: %s", cid, err)
                schema_errors.append({"id": cid, "error": err})

            response["conversation_id"] = cid
            response["actual_intent"] = conv.get('actual_intent')
            response["pipeline_status"] = "success"

            results.append(response)

            # Log decision
            decision = response["decision"]
            intent = response["intent"]
            conf = response["confidence"]
            logger.info("  Result: decision=%s, intent=%s, conf=%.3f",
                        decision, intent, conf)

        except Exception as e:
            logger.error("Pipeline failed for %s: %s", cid, str(e))
            errors.append({"id": cid, "error": str(e)})

    return results, errors, schema_errors


# =============================================================================
# Metrics Computation
# =============================================================================

def compute_metrics(results, errors, schema_errors):
    """Compute summary metrics from test results."""

    total = len(results) + len(errors)
    successful = len(results)
    failed = len(errors)

    # Decision breakdown
    auto_handle = [r for r in results if r.get('decision') == 'AUTO_HANDLE']
    escalate = [r for r in results if r.get('decision') == 'ESCALATE']

    # Confidence stats
    confidences = [r['confidence'] for r in results if r.get('confidence') is not None]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
    min_confidence = min(confidences) if confidences else 0
    max_confidence = max(confidences) if confidences else 0

    # Retrieval stats
    all_avg_sims = []
    for r in results:
        if r.get('evidence'):
            avg_sim = sum(e['similarity_score'] for e in r['evidence']) / len(r['evidence'])
            all_avg_sims.append(avg_sim)
    avg_evidence_sim = sum(all_avg_sims) / len(all_avg_sims) if all_avg_sims else 0

    # Generation stats
    generation_attempted = [r for r in auto_handle if r.get('draft_reply') is not None]
    generation_failed = [r for r in auto_handle if r.get('draft_reply') is None]
    generation_success_rate = len(generation_attempted) / len(auto_handle) if auto_handle else 0

    # Intent match (if actual_intent available)
    intent_matches = 0
    for r in results:
        if r.get('actual_intent') and r.get('intent'):
            if r['actual_intent'] == r['intent']:
                intent_matches += 1
    intent_accuracy = intent_matches / len(results) if results else 0

    metrics = {
        "total_conversations": total,
        "successful_runs": successful,
        "failed_runs": failed,
        "schema_errors": len(schema_errors),
        "auto_handle_count": len(auto_handle),
        "auto_handle_rate": len(auto_handle) / successful if successful else 0,
        "escalate_count": len(escalate),
        "escalate_rate": len(escalate) / successful if successful else 0,
        "avg_confidence": round(avg_confidence, 4),
        "min_confidence": round(min_confidence, 4),
        "max_confidence": round(max_confidence, 4),
        "avg_evidence_similarity": round(avg_evidence_sim, 4),
        "generation_success_rate": round(generation_success_rate, 4) if generation_success_rate else 0,
        "generation_attempted": len(generation_attempted),
        "generation_failed": len(generation_failed),
        "intent_accuracy": round(intent_accuracy, 4) if intent_accuracy else 0,
    }

    return metrics


def print_metrics(metrics):
    """Print formatted metrics."""
    print("\n" + "=" * 70)
    print("SPRINT 6: PIPELINE TEST RESULTS")
    print("=" * 70)

    print("\n--- OVERALL ---")
    print(f"Total conversations:     {metrics['total_conversations']}")
    print(f"Successful runs:        {metrics['successful_runs']}")
    print(f"Failed runs:            {metrics['failed_runs']}")
    print(f"Schema errors:          {metrics['schema_errors']}")

    print("\n--- DECISIONS ---")
    print(f"AUTO_HANDLE:            {metrics['auto_handle_count']} ({metrics['auto_handle_rate']:.1%})")
    print(f"ESCALATE:               {metrics['escalate_count']} ({metrics['escalate_rate']:.1%})")

    print("\n--- CLASSIFIER CONFIDENCE ---")
    print(f"Average:                {metrics['avg_confidence']:.3f}")
    print(f"Min:                    {metrics['min_confidence']:.3f}")
    print(f"Max:                    {metrics['max_confidence']:.3f}")

    print("\n--- RETRIEVAL EVIDENCE ---")
    print(f"Avg similarity:         {metrics['avg_evidence_similarity']:.3f}")

    print("\n--- GENERATION (AUTO_HANDLE only) ---")
    print(f"Generation attempted:   {metrics['generation_attempted']}")
    print(f"Generation failed:      {metrics['generation_failed']}")
    print(f"Success rate:           {metrics['generation_success_rate']:.1%}")

    print("\n--- INTENT ACCURACY ---")
    print(f"Correct intents:        {metrics['intent_accuracy']:.1%}")

    print("\n" + "=" * 70)


# =============================================================================
# Report Generation
# =============================================================================

def generate_report(metrics, results, errors, schema_errors, output_path):
    """Generate detailed test report."""

    report = {
        "timestamp": datetime.now().isoformat(),
        "metrics": metrics,
        "sample_results": results[:10] if len(results) > 10 else results,
        "errors": errors,
        "schema_errors": schema_errors,
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    logger.info("Report saved to %s", output_path)


# =============================================================================
# Main
# =============================================================================

if __name__ == '__main__':
    print("Sprint 6: Pipeline Test Suite")
    print("=" * 70)

    # Load test data - use 50 conversations from test split
    print("\nLoading test conversations...")
    test_data = load_test_data_from_corpus(n=50)
    print(f"Loaded {len(test_data)} test conversations")

    # Run tests WITHOUT generation (faster for schema/decision testing)
    # Set skip_generation=False to test full pipeline with LLM
    print("\nRunning pipeline tests (skip_generation=True for speed)...")
    results, errors, schema_errors = run_tests(test_data, skip_generation=True, max_tests=50)

    # Compute and print metrics
    metrics = compute_metrics(results, errors, schema_errors)
    print_metrics(metrics)

    # Save report
    report_path = f"{EVAL_DIR}/sprint6_test_report.json"
    generate_report(metrics, results, errors, schema_errors, report_path)
    print(f"\nDetailed report saved to: {report_path}")
    print(f"Log file: {log_file}")

    # If we ran with skip_generation=True, offer to run a few with generation
    print("\n" + "=" * 70)
    print("NOTE: Tests ran with skip_generation=True (no LLM calls)")
    print("To test full pipeline with reply generation, run:")
    print("  results, errors, schema_errors = run_tests(test_data, skip_generation=False, max_tests=10)")
    print("=" * 70)
