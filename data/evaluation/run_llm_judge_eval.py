#!/usr/bin/env python3
"""
Run LLM-as-judge evaluation on the human review examples.

This script evaluates AI-generated replies using the Groq LLM according to
the 5-dimension rubric and produces results for agreement analysis.

Requires GROQ_API_KEY environment variable.
"""

import json
import os
import sys
import argparse

# Add project root to path (project root is 2 levels up from data/evaluation/)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
sys.path.insert(0, project_root)
sys.stdout.reconfigure(encoding='utf-8')

from groq import Groq
from data.llm_judge import evaluate_reply, format_evidence

INPUT_FILE = "data/evaluation/human_review_with_replies.jsonl"
OUTPUT_FILE = "data/evaluation/llm_judge_results.jsonl"

# Rubric for reference
RUBRIC = """
EVALUATION RUBRIC (1-5 scale per dimension):
1. FACTUAL ACCURACY: Does the reply address the customer's actual issue?
2. POLICY ALIGNMENT: Does the reply follow Amazon customer service policies?
3. EMPATHY & TONE: Does the reply show appropriate empathy and professional tone?
4. COMPLETENESS: Does the reply fully address the customer's needs?
5. COHERENCE: Is the reply well-structured and easy to understand?

OVERALL: ACCEPT if average >= 3.0, else REVISE
"""


def get_groq_client():
    """Get Groq client from environment."""
    api_key = os.environ.get('GROQ_API_KEY')
    if not api_key:
        print("ERROR: GROQ_API_KEY environment variable not set")
        print("Please set your Groq API key: export GROQ_API_KEY=your_key")
        return None
    return Groq(api_key=api_key)


def run_llm_evaluation(input_path, output_path, model="qwen/qwen3.8-27b"):
    """Run LLM judge on ALL examples (including ESCALATE with template replies)."""
    # Check for API key
    client = get_groq_client()
    if not client:
        print("\nERROR: Groq API key not configured. Cannot run real evaluation.")
        return []

    # Test API key validity with a simple call
    print("\nTesting Groq API connection...")
    try:
        test_response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
        print("Groq API connection successful!")
    except Exception as e:
        print(f"Groq API test failed: {e}")
        return []

    # Load examples
    print(f"\nLoading examples from: {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        examples = [json.loads(line) for line in f]

    print(f"Total examples: {len(examples)}")

    # For ESCALATE examples without draft_reply, generate a template reply
    TEMPLATE_REPLIES = {
        "DELIVERY_LATE": "I apologize for the delay with your delivery. I understand how frustrating this must be. Let me check the status of your order and provide you with an updated delivery estimate. If your order has not arrived by the expected date, we can investigate with the carrier or arrange a refund if appropriate.",
        "DELIVERY_MISSING": "I'm sorry your package hasn't arrived yet. I know how concerning this must be. Let me investigate the delivery status right away. Please provide your order number and we can check with the carrier or arrange a replacement if necessary.",
        "ORDER_STATUS": "Thank you for checking on your order. I've looked into the status and can see your order is currently being processed. You can track your order in the 'Your Orders' section of our website. Let me know if you need any additional assistance.",
        "REFUND_REQUEST": "I've received your refund request and processed it accordingly. You should see the refund reflected in your account within 5-10 business days depending on your bank's processing time. Please let me know if you have any questions.",
        "RETURN_REQUEST": "I've received your return request and will be sending you an email with instructions on how to return your item. Once we receive and process the returned item, your refund will be issued within 5-7 business days.",
        "PAYMENT_ISSUE": "I've reviewed your payment concern. Please verify that your payment method details are correct and that there are sufficient funds available. If the issue persists, try using an alternative payment method. Our system automatically retries failed payments within 24-48 hours.",
        "ACCOUNT_ACCESS": "I'm sorry to hear you're having trouble accessing your account. This can happen for various reasons. Please try resetting your password using the 'Forgot Password' link. If you still can't access your account, please provide your registered email and we can help verify your identity.",
        "DEVICE_ISSUE": "Thank you for contacting us about your device issue. I understand this can be frustrating. Let me help troubleshoot this with you. Have you tried restarting your device or checking for software updates? Please let me know the specific issue you're experiencing.",
        "PRODUCT_ISSUE": "I'm sorry to hear about the issue with your product. We take product quality concerns seriously. Could you provide more details about the problem? Based on your description, we can offer a replacement, full refund, or compensation.",
        "OTHER": "Thank you for contacting Amazon customer service. I've reviewed your inquiry and I'm here to help. Could you please provide more details about your concern so I can direct you to the right team? We're committed to resolving your issue as quickly as possible."
    }

    FALLBACK = "Thank you for contacting Amazon customer service. I've reviewed your message and I'm here to help. Could you please provide additional details about your concern so we can resolve this together?"

    examples_to_eval = []
    for ex in examples:
        if ex.get('draft_reply'):
            examples_to_eval.append(ex)
        elif ex.get('decision') == 'ESCALATE':
            # Generate template reply for ESCALATE cases
            intent = ex.get('predicted_intent', 'OTHER')
            template = TEMPLATE_REPLIES.get(intent, FALLBACK)
            ex_copy = dict(ex)
            ex_copy['draft_reply'] = f"[AUTO-GENERATED for ESCALATE case] {template}"
            ex_copy['is_template_reply'] = True
            examples_to_eval.append(ex_copy)
        else:
            # No draft_reply and not ESCALATE - skip
            pass

    print(f"Examples to evaluate: {len(examples_to_eval)} (includes {len(examples) - len([e for e in examples if e.get('draft_reply')])} template replies for ESCALATE cases)")

    # Check for existing results
    existing_results = []
    if os.path.exists(output_path):
        print(f"Found existing results at {output_path}")
        with open(output_path, 'r', encoding='utf-8') as f:
            for line in f:
                existing_results.append(json.loads(line))
        print(f"Already evaluated: {len(existing_results)} examples")
        evaluated_ids = {r['example_id'] for r in existing_results}
    else:
        evaluated_ids = set()

    # Evaluate examples
    results = existing_results
    retry_delay = 2.0  # Start with 2 seconds

    for i, ex in enumerate(examples_to_eval):
        example_id = ex['example_id']
        if example_id in evaluated_ids:
            print(f"[{i+1}/{len(examples_to_eval)}] {example_id}... already evaluated, skipping")
            continue

        print(f"[{i+1}/{len(examples_to_eval)}] {example_id}...", end=" ", flush=True)

        # Retry loop for rate limiting
        max_retries = 3
        success = False
        for attempt in range(max_retries):
            try:
                result = evaluate_reply(
                    customer_text=ex['customer_text'],
                    intent=ex.get('predicted_intent', ''),
                    reply=ex.get('draft_reply', ''),
                    evidence=ex.get('evidence', []),
                    groq_client=client,
                    model=model
                )

                # Convert to dict
                result_dict = {
                    'example_id': example_id,
                    'conversation_id': ex.get('conversation_id', ''),
                    'customer_text': ex['customer_text'][:200] + "..." if len(ex['customer_text']) > 200 else ex['customer_text'],
                    'predicted_intent': ex.get('predicted_intent', ''),
                    'human_label': ex.get('human_label', ''),
                    'system_decision': ex.get('decision', ''),
                    'is_template_reply': ex.get('is_template_reply', False),
                    'factual_accuracy': result.factual_accuracy,
                    'policy_alignment': result.policy_alignment,
                    'empathy_tone': result.empathy_tone,
                    'completeness': result.completeness,
                    'coherence': result.coherence,
                    'overall_score': result.overall_score,
                    'decision': result.decision,
                    'reasoning': result.reasoning,
                    'judge_model': result.judge_model,
                    'reviewer': 'llm_judge'
                }

                results.append(result_dict)
                print(f"Done (score={result.overall_score:.2f}, decision={result.decision})")
                success = True
                break  # Success, exit retry loop

            except Exception as e:
                error_str = str(e)
                if 'rate limit' in error_str.lower() and attempt < max_retries - 1:
                    # Rate limit error - retry with backoff
                    print(f"Rate limited, retrying in {retry_delay}s...")
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    # Other error or max retries exceeded
                    print(f"ERROR: {error_str[:80]}")
                    result_dict = {
                        'example_id': example_id,
                        'conversation_id': ex.get('conversation_id', ''),
                        'predicted_intent': ex.get('predicted_intent', ''),
                        'system_decision': ex.get('decision', ''),
                        'is_template_reply': ex.get('is_template_reply', False),
                        'error': error_str,
                        'reviewer': 'llm_judge'
                    }
                    results.append(result_dict)
                    success = True  # Mark as handled even if error
                    break  # Exit retry loop

        # Save after each evaluation
        with open(output_path, 'w', encoding='utf-8') as f:
            for r in results:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')

    print(f"\nLLM judge evaluation complete. Total evaluated: {len(results)}")
    return results


def run_mock_evaluation(input_path, output_path):
    """Run mock evaluation for testing without Groq API."""
    print("\nRunning MOCK evaluation (Groq API not available)")
    print("This produces simulated results for demonstration purposes.")
    print("-" * 50)

    # Load examples
    with open(input_path, 'r', encoding='utf-8') as f:
        examples = [json.loads(line) for line in f]

    # Filter to examples with draft replies
    examples_with_replies = [ex for ex in examples if ex.get('draft_reply')]

    # Check for existing results
    existing_results = []
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            for line in f:
                existing_results.append(json.loads(line))
        evaluated_ids = {r['example_id'] for r in existing_results}
    else:
        evaluated_ids = set()

    results = existing_results
    for i, ex in enumerate(examples_with_replies):
        example_id = ex['example_id']
        if example_id in evaluated_ids:
            continue

        # Generate mock scores (for demonstration only)
        import random
        random.seed(hash(example_id) % (2**31))

        factual = random.randint(2, 5)
        policy = random.randint(2, 5)
        empathy = random.randint(2, 5)
        completeness = random.randint(2, 5)
        coherence = random.randint(2, 5)
        overall = (factual + policy + empathy + completeness + coherence) / 5
        decision = "ACCEPT" if overall >= 3.0 else "REVISE"

        result_dict = {
            'example_id': example_id,
            'conversation_id': ex.get('conversation_id', ''),
            'customer_text': ex['customer_text'][:200] + "..." if len(ex['customer_text']) > 200 else ex['customer_text'],
            'predicted_intent': ex.get('predicted_intent', ''),
            'human_label': ex.get('human_label', ''),
            'system_decision': ex.get('decision', ''),
            'factual_accuracy': factual,
            'policy_alignment': policy,
            'empathy_tone': empathy,
            'completeness': completeness,
            'coherence': coherence,
            'overall_score': round(overall, 2),
            'decision': decision,
            'reasoning': f"[MOCK] Simulated evaluation for demonstration without Groq API",
            'judge_model': 'mock',
            'reviewer': 'llm_judge',
            'mock': True
        }

        results.append(result_dict)
        print(f"[{i+1}/{len(examples_with_replies)}] {example_id}... mock score={overall:.2f}, decision={decision}")

        # Save after each
        with open(output_path, 'w', encoding='utf-8') as f:
            for r in results:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')

    print(f"\nMock evaluation complete. Total: {len(results)}")
    return results


def show_summary(results):
    """Show summary of LLM judge results."""
    if not results:
        print("\nNo results to summarize.")
        return

    total = len([r for r in results if not r.get('error')])
    decisions = {'ACCEPT': 0, 'REVISE': 0}

    for r in results:
        if 'error' in r:
            continue
        dec = r.get('decision', 'UNKNOWN')
        if dec in decisions:
            decisions[dec] += 1

    print("\n" + "=" * 70)
    print("LLM JUDGE EVALUATION SUMMARY")
    print("=" * 70)
    print(f"Total evaluated: {total}")
    print(f"  ACCEPT: {decisions['ACCEPT']}")
    print(f"  REVISE: {decisions['REVISE']}")

    # Average scores
    dimensions = ['factual_accuracy', 'policy_alignment', 'empathy_tone', 'completeness', 'coherence']
    print("\nAverage Scores by Dimension:")
    for dim in dimensions:
        scores = [r[dim] for r in results if dim in r and 'error' not in r]
        if scores:
            avg = sum(scores) / len(scores)
            print(f"  {dim}: {avg:.2f}")


def main():
    parser = argparse.ArgumentParser(description='Run LLM-as-judge evaluation')
    parser.add_argument('--input', '-i', default=INPUT_FILE, help='Input JSONL file')
    parser.add_argument('--output', '-o', default=OUTPUT_FILE, help='Output JSONL file')
    parser.add_argument('--model', '-m', default='qwen/qwen3.8-27b', help='Groq model')
    parser.add_argument('--summary', '-s', action='store_true', help='Show summary')
    args = parser.parse_args()

    if args.summary:
        if os.path.exists(args.output):
            with open(args.output, 'r', encoding='utf-8') as f:
                results = [json.loads(line) for line in f]
            show_summary(results)
        else:
            print(f"No existing results found at {args.output}")
        return

    results = run_llm_evaluation(args.input, args.output, args.model)
    if results:
        show_summary(results)


if __name__ == '__main__':
    main()