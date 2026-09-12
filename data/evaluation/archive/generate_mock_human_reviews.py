#!/usr/bin/env python3
"""
Generate mock human review results for demonstration.

This script creates synthetic human evaluations that simulate what a human
reviewer would produce. Used for testing the evaluation harness when
actual human reviewers are not available.

In production, actual human reviewers would use the human_review_tool.py
to provide real evaluations.
"""

import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding='utf-8')

LLM_RESULTS = "data/evaluation/llm_judge_results.jsonl"
OUTPUT_FILE = "data/evaluation/human_review_results.jsonl"


def load_jsonl(path):
    """Load results from a JSONL file."""
    if not os.path.exists(path):
        return []
    results = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            results.append(json.loads(line))
    return results


def generate_mock_human_review(llm_result, seed_offset=1000):
    """
    Generate a mock human review based on the LLM result.

    Human reviewers tend to:
    - Be slightly harsher on empathy and completeness
    - Be more lenient on coherence
    - Have ~70-80% agreement with LLM judges on average
    """
    example_id = llm_result['example_id']

    # Use a different seed for human vs LLM
    random.seed(hash(example_id + "_human") % (2**31) + seed_offset)

    # Base scores on LLM scores but with human-like variation
    llm_factual = llm_result.get('factual_accuracy', 3)
    llm_policy = llm_result.get('policy_alignment', 3)
    llm_empathy = llm_result.get('empathy_tone', 3)
    llm_complete = llm_result.get('completeness', 3)
    llm_coherence = llm_result.get('coherence', 3)

    # Human tendencies (based on research):
    # - Slightly lower on empathy (humans are more critical)
    # - Similar on factual accuracy
    # - Slightly lower on completeness (humans expect more)
    # - Similar or higher on coherence

    # Add human-like variation (±1-2 points, biased negative)
    factual = max(1, min(5, llm_factual + random.choice([-1, 0, 0, 1])))
    policy = max(1, min(5, llm_policy + random.choice([-1, 0, 0, 1])))
    empathy = max(1, min(5, llm_empathy + random.choice([-1, -1, 0, 1])))  # Bias lower
    completeness = max(1, min(5, llm_complete + random.choice([-1, 0, 0, 1])))
    coherence = max(1, min(5, llm_coherence + random.choice([0, 0, 1, 1])))  # Bias higher

    # Calculate average
    scores = [factual, policy, empathy, completeness, coherence]
    avg_score = sum(scores) / len(scores)

    # Human decision - slightly more lenient than LLM on average
    llm_decision = llm_result.get('decision', 'ACCEPT')
    if llm_decision == 'ACCEPT':
        # 80% chance human also accepts
        decision = 'ACCEPT' if random.random() < 0.80 else 'REVISE'
    else:
        # 70% chance human also revises
        decision = 'REVISE' if random.random() < 0.70 else 'ACCEPT'

    # Generate reasoning
    if decision == 'ACCEPT':
        reasoning = f"Human review: Reply meets quality standards. Good empathy and factual accuracy."
    else:
        reasoning = f"Human review: Reply needs improvement in {random.choice(['empathy', 'completeness', 'policy alignment'])}."

    return {
        'example_id': example_id,
        'conversation_id': llm_result.get('conversation_id', ''),
        'customer_text': llm_result.get('customer_text', '')[:200] + "...",
        'predicted_intent': llm_result.get('predicted_intent', ''),
        'human_label': llm_result.get('human_label', ''),
        'system_decision': llm_result.get('system_decision', ''),
        'factual_accuracy': factual,
        'policy_alignment': policy,
        'empathy_tone': empathy,
        'completeness': completeness,
        'coherence': coherence,
        'average_score': round(avg_score, 2),
        'decision': decision,
        'reasoning': reasoning,
        'reviewer': 'human',
        'mock': True
    }


def main():
    print("=" * 60)
    print("MOCK HUMAN REVIEW GENERATOR")
    print("For demonstration/testing purposes only")
    print("=" * 60)

    # Load LLM results
    print(f"\nLoading LLM results from: {LLM_RESULTS}")
    llm_results = load_jsonl(LLM_RESULTS)
    print(f"Loaded {len(llm_results)} LLM evaluations")

    if not llm_results:
        print("No LLM results found!")
        return

    # Check for existing human results
    existing_results = []
    if os.path.exists(OUTPUT_FILE):
        print(f"\nFound existing results at {OUTPUT_FILE}")
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                existing_results.append(json.loads(line))
        print(f"Already have {len(existing_results)} human reviews")
        existing_ids = {r['example_id'] for r in existing_results}
    else:
        existing_ids = set()

    # Generate human reviews for examples that don't have them
    results = existing_results
    for llm_result in llm_results:
        example_id = llm_result['example_id']
        if example_id in existing_ids:
            print(f"Skipping {example_id} - already reviewed")
            continue

        human_review = generate_mock_human_review(llm_result)
        results.append(human_review)
        print(f"Generated human review for {example_id}: "
              f"score={human_review['average_score']:.2f}, decision={human_review['decision']}")

        # Save after each
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            for r in results:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')

    print(f"\nTotal human reviews: {len(results)}")
    print(f"Saved to: {OUTPUT_FILE}")

    # Summary
    decisions = {'ACCEPT': 0, 'REVISE': 0}
    for r in results:
        dec = r.get('decision', 'UNKNOWN')
        if dec in decisions:
            decisions[dec] += 1

    print("\nDecision distribution:")
    for dec, count in decisions.items():
        print(f"  {dec}: {count}")


if __name__ == '__main__':
    main()