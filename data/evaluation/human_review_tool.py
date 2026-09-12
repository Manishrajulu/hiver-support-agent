#!/usr/bin/env python3
"""
Human Review Tool for Intent Classification Evaluation

A terminal-based interface for human evaluators to review customer service
intent classifications and generated replies using the 5-dimension rubric.

Usage:
    python human_review_tool.py [--input FILE] [--output FILE]
"""

import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
sys.stdout.reconfigure(encoding='utf-8')

INPUT_FILE = "data/evaluation/human_review_with_replies.jsonl"
OUTPUT_FILE = "data/evaluation/human_review_results.jsonl"

# Rubric dimensions
RUBRIC = """
EVALUATION RUBRIC (1-5 scale per dimension):
============================================

1. FACTUAL ACCURACY (Does the reply address the customer's actual issue?)
   1 = Reply contains significant factual errors or addresses wrong issue
   3 = Reply mostly accurate with minor gaps
   5 = Reply perfectly accurate, addresses exact customer concern

2. POLICY ALIGNMENT (Does the reply follow Amazon customer service policies?)
   1 = Reply suggests actions that violate Amazon policy
   3 = Reply mostly policy-compliant with minor concerns
   5 = Reply fully compliant with Amazon policies

3. EMPATHY & TONE (Does the reply show appropriate empathy and professional tone?)
   1 = Reply is dismissive, cold, or inappropriate
   3 = Reply shows moderate empathy but could be warmer
   5 = Reply is warm, empathetic, and professional

4. COMPLETENESS (Does the reply fully address the customer's needs?)
   1 = Reply leaves major questions unanswered
   3 = Reply addresses most but not all customer needs
   5 = Reply completely addresses all customer concerns

5. COHERENCE (Is the reply well-structured and easy to understand?)
   1 = Reply is confusing, contradictory, or poorly structured
   3 = Reply is mostly clear but could be better organized
   5 = Reply is clear, logical, and well-structured

OVERALL DECISION:
- ACCEPT: Average score >= 3.0 (reply meets quality standards)
- REVISE: Average score < 3.0 (reply needs improvement)
"""


def print_header():
    print("\n" + "=" * 70)
    print("HUMAN REVIEW TOOL - Intent Classification Evaluation")
    print("=" * 70)


def print_review_header(example_id, intent, decision):
    print(f"\n--- Example: {example_id} ---")
    print(f"Predicted Intent: {intent}")
    print(f"System Decision: {decision}")
    print("-" * 50)


def get_rating(prompt, min_val=1, max_val=5):
    """Get a numeric rating from the user."""
    while True:
        try:
            response = input(f"{prompt} ({min_val}-{max_val}): ").strip()
            if response.lower() == 'q':
                return None
            rating = int(response)
            if min_val <= rating <= max_val:
                return rating
            print(f"Please enter a number between {min_val} and {max_val}")
        except ValueError:
            print("Please enter a valid number")


def get_decision():
    """Get ACCEPT/REVISE decision from user."""
    while True:
        response = input("Your Decision (ACCEPT/REVISE/SKIP/Q): ").strip().upper()
        if response in ['ACCEPT', 'REVISE', 'SKIP', 'Q']:
            return response
        print("Please enter ACCEPT, REVISE, SKIP, or Q to quit")


def review_example(example):
    """Present an example to the human reviewer and collect ratings."""
    example_id = example['example_id']
    customer_text = example['customer_text']
    predicted_intent = example.get('predicted_intent', 'N/A')
    decision = example.get('decision', 'N/A')
    draft_reply = example.get('draft_reply')
    evidence = example.get('evidence', [])
    human_label = example.get('human_label', '')

    print_review_header(example_id, predicted_intent, decision)

    # Show customer text
    print("\n[CUSTOMER MESSAGE]")
    # Truncate very long messages
    if len(customer_text) > 500:
        print(customer_text[:500] + "...")
    else:
        print(customer_text)

    # Show predicted intent and human label if available
    print(f"\n  Predicted Intent: {predicted_intent}")
    if human_label:
        print(f"  Human Label: {human_label}")

    # Show draft reply if available
    if draft_reply:
        print("\n[GENERATED REPLY]")
        if len(draft_reply) > 600:
            print(draft_reply[:600] + "...")
        else:
            print(draft_reply)
    else:
        print("\n[GENERATED REPLY] (none - ESCALATED)")

    # Show top evidence
    if evidence:
        print("\n[TOP EVIDENCE (retrieved cases)]")
        for i, ev in enumerate(evidence[:3], 1):
            intent = ev.get('intent', 'N/A')
            sim = ev.get('similarity_score', 0)
            text = ev.get('customer_text', '')
            if len(text) > 150:
                text = text[:150] + "..."
            print(f"  {i}. [{intent}] sim={sim:.2f}: {text}")

    # Show rubric
    print(RUBRIC)

    # Collect ratings
    print("\n[COLLECTING RATINGS]")
    factual = get_rating("Factual Accuracy")
    if factual is None:
        return None

    policy = get_rating("Policy Alignment")
    if policy is None:
        return None

    empathy = get_rating("Empathy & Tone")
    if empathy is None:
        return None

    completeness = get_rating("Completeness")
    if completeness is None:
        return None

    coherence = get_rating("Coherence")
    if coherence is None:
        return None

    # Get reasoning
    print("\n[REASONING]")
    reasoning = input("Brief reasoning for your evaluation (or Enter to skip): ").strip()

    # Get overall decision
    print("\n[OVERALL DECISION]")
    overall_decision = get_decision()
    if overall_decision is None or overall_decision == 'Q':
        return None

    # Calculate average
    scores = [factual, policy, empathy, completeness, coherence]
    avg_score = sum(scores) / len(scores)

    # Map decision
    if overall_decision == 'SKIP':
        final_decision = 'SKIPPED'
    else:
        final_decision = overall_decision

    return {
        'example_id': example_id,
        'conversation_id': example.get('conversation_id', ''),
        'customer_text': customer_text[:200] + "..." if len(customer_text) > 200 else customer_text,
        'predicted_intent': predicted_intent,
        'human_label': human_label,
        'system_decision': decision,
        'factual_accuracy': factual,
        'policy_alignment': policy,
        'empathy_tone': empathy,
        'completeness': completeness,
        'coherence': coherence,
        'average_score': round(avg_score, 2),
        'decision': final_decision,
        'reasoning': reasoning,
        'reviewer': 'human'
    }


def run_review(input_path, output_path, start_index=0):
    """Run the human review tool on all examples."""
    # Load examples
    print(f"\nLoading examples from: {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        examples = [json.loads(line) for line in f]

    print(f"Loaded {len(examples)} examples")

    # Check for existing results to resume
    existing_results = []
    if os.path.exists(output_path):
        print(f"\nFound existing results at {output_path}")
        with open(output_path, 'r', encoding='utf-8') as f:
            for line in f:
                existing_results.append(json.loads(line))
        print(f"Already reviewed: {len(existing_results)} examples")
        reviewed_ids = {r['example_id'] for r in existing_results}
    else:
        reviewed_ids = set()

    # Filter examples to review
    examples_to_review = [ex for ex in examples if ex['example_id'] not in reviewed_ids]

    if not examples_to_review:
        print("\nAll examples have been reviewed!")
        return existing_results

    print(f"Examples remaining: {len(examples_to_review)}")

    # Show rubric first
    print(RUBRIC)

    # Process examples
    results = existing_results
    for i, example in enumerate(examples_to_review):
        idx = examples.index(example)
        print_header()
        print(f"\nReviewing example {idx + 1}/{len(examples)}")
        print(f"Progress: {len(results)}/{len(examples)} completed")

        result = review_example(example)

        if result is None:
            print("\n\nReview interrupted. Progress saved.")
            break

        results.append(result)

        # Save after each review
        with open(output_path, 'w', encoding='utf-8') as f:
            for r in results:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')

        print(f"\nSaved result. Total reviewed: {len(results)}/{len(examples)}")

    print_header()
    print(f"\nReview session complete. Total reviewed: {len(results)}/{len(examples)}")

    return results


def show_summary(results):
    """Show summary statistics of the review."""
    if not results:
        print("\nNo results to summarize.")
        return

    total = len(results)
    decisions = {'ACCEPT': 0, 'REVISE': 0, 'SKIPPED': 0}

    for r in results:
        dec = r.get('decision', 'UNKNOWN')
        if dec in decisions:
            decisions[dec] += 1

    print("\n" + "=" * 70)
    print("REVIEW SUMMARY")
    print("=" * 70)
    print(f"Total reviewed: {total}")
    print(f"  ACCEPT: {decisions['ACCEPT']}")
    print(f"  REVISE: {decisions['REVISE']}")
    print(f"  SKIPPED: {decisions['SKIPPED']}")

    # Calculate average scores by dimension
    dimensions = ['factual_accuracy', 'policy_alignment', 'empathy_tone', 'completeness', 'coherence']
    print("\nAverage Scores by Dimension:")
    for dim in dimensions:
        scores = [r[dim] for r in results if dim in r]
        if scores:
            avg = sum(scores) / len(scores)
            print(f"  {dim}: {avg:.2f}")

    # Show agreement with system decision
    system_agrees = 0
    for r in results:
        if r.get('decision') == 'ACCEPT' and r.get('system_decision') == 'AUTO_HANDLE':
            system_agrees += 1
        elif r.get('decision') == 'REVISE' and r.get('system_decision') == 'ESCALATE':
            system_agrees += 1

    if total > 0:
        print(f"\nAgreement with system decision: {system_agrees}/{total} ({system_agrees/total*100:.1f}%)")


def main():
    parser = argparse.ArgumentParser(description='Human Review Tool for Intent Classification')
    parser.add_argument('--input', '-i', default=INPUT_FILE, help='Input JSONL file')
    parser.add_argument('--output', '-o', default=OUTPUT_FILE, help='Output JSONL file')
    parser.add_argument('--start', '-s', type=int, default=0, help='Start index')
    parser.add_argument('--summary', action='store_true', help='Show summary of existing results')
    args = parser.parse_args()

    if args.summary:
        if os.path.exists(args.output):
            with open(args.output, 'r', encoding='utf-8') as f:
                results = [json.loads(line) for line in f]
            show_summary(results)
        else:
            print(f"No existing results found at {args.output}")
        return

    print_header()
    print("\nThis tool will present customer service examples for human evaluation.")
    print("For each example, you'll rate the generated reply on 5 dimensions")
    print("and provide an overall ACCEPT/REVISE decision.")
    print("\nEnter 'Q' at any prompt to quit and save progress.")

    results = run_review(args.input, args.output, args.start)

    if results:
        show_summary(results)


if __name__ == '__main__':
    main()