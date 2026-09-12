#!/usr/bin/env python3
"""
Generate AI replies for the 40 human review examples.

This script runs the pipeline on the human_judge_subset.csv to generate
AI-generated replies for evaluation by both LLM judge and human reviewer.
"""

import csv
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
sys.stdout.reconfigure(encoding='utf-8')

from pipeline import run_pipeline

INPUT_CSV = "data/evaluation/human_judge_subset.csv"
OUTPUT_JSONL = "data/evaluation/human_review_with_replies.jsonl"


def main():
    print("=" * 70)
    print("GENERATING AI REPLIES FOR HUMAN REVIEW")
    print("=" * 70)

    # Load human review examples
    print("\n[1] Loading human review examples...")
    examples = []
    with open(INPUT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            examples.append(row)

    print(f"  Loaded {len(examples)} examples")

    # Generate replies for each example
    print("\n[2] Generating AI replies...")
    results = []

    for i, ex in enumerate(examples):
        customer_text = ex['customer_text']
        example_id = ex['example_id']

        print(f"  [{i+1}/{len(examples)}] {example_id}...", end=" ", flush=True)

        try:
            # Run pipeline with reply generation
            result = run_pipeline(customer_text, skip_generation=False)

            # Extract relevant fields
            results.append({
                'example_id': example_id,
                'conversation_id': ex['conversation_id'],
                'customer_text': customer_text,
                'predicted_intent': result.get('intent', ''),
                'confidence': result.get('confidence', 0),
                'decision': result.get('decision', ''),
                'draft_reply': result.get('draft_reply', ''),
                'evidence': result.get('evidence', []),
                'human_label': ex.get('human_label', ''),
                'human_notes': ex.get('human_notes', '')
            })

            print(f"Done (decision={result.get('decision', 'N/A')})")

        except Exception as e:
            print(f"ERROR: {e}")
            results.append({
                'example_id': example_id,
                'conversation_id': ex['conversation_id'],
                'customer_text': customer_text,
                'predicted_intent': '',
                'confidence': 0,
                'decision': 'ERROR',
                'draft_reply': '',
                'evidence': [],
                'human_label': ex.get('human_label', ''),
                'human_notes': ex.get('human_notes', ''),
                'error': str(e)
            })

    # Save results
    print("\n[3] Saving results...")
    with open(OUTPUT_JSONL, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')

    print(f"  Saved to: {OUTPUT_JSONL}")

    # Summary
    decisions = {}
    for r in results:
        d = r.get('decision', 'UNKNOWN')
        decisions[d] = decisions.get(d, 0) + 1

    print("\n[4] Summary:")
    print(f"  Total examples: {len(results)}")
    for decision, count in sorted(decisions.items()):
        print(f"  {decision}: {count}")

    # Count how many have replies
    with_replies = sum(1 for r in results if r.get('draft_reply'))
    print(f"  Examples with draft replies: {with_replies}")

    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)


if __name__ == '__main__':
    main()
