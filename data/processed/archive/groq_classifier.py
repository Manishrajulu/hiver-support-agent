#!/usr/bin/env python3
"""
Groq-powered Intent Classification for AmazonHelp Conversations
==============================================================
Uses LLM for semantic understanding instead of rule-based matching.
"""

import json
import os
import time
from groq import Groq
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv(os.path.join(os.path.dirname(__file__), 'api_key.env'))

# Initialize Groq client
# Set GROQ_API_KEY environment variable or pass --api-key argument
def get_client(api_key=None):
    if api_key:
        return Groq(api_key=api_key)
    env_key = os.environ.get("GROQ_API_KEY")
    if env_key:
        return Groq(api_key=env_key)
    raise ValueError("Groq API key not found. Set GROQ_API_KEY env var or pass --api-key")

# Model to use
MODEL = "allam-2-7b"  # Available on your API

# Taxonomy for classification
TAXONOMY = """
You are an Amazon customer service intent classifier. Classify each customer conversation into ONE of the following 14 intents:

1. DELIVERY_MISSING - Package never arrived, marked delivered but not received
2. DELIVERY_LATE - Package is late, delayed, taking too long
3. DELIVERY_TRACKING - Customer wants to track a package
4. ORDER_STATUS - Customer asking about order status or updates
5. ORDER_MODIFY - Customer wants to cancel or change an order
6. PRODUCT_ISSUE - Wrong, damaged, or defective item received
7. RETURN_REQUEST - Customer wants to return an item
8. REFUND_REQUEST - Customer explicitly requesting a money refund
9. PAYMENT_ISSUE - Payment failed, card declined, incorrect charge
10. ACCOUNT_ACCESS - Login, password, or account access problems
11. APP_USAGE - App or website not working, crashes, errors
12. DEVICE_ISSUE - Kindle, Echo, Fire TV, tablet issues
13. VIDEO_STREAMING - Prime Video or streaming playback problems
14. OTHER - No clear actionable intent, venting, general complaints

IMPORTANT:
- Classify based on the CUSTOMER'S ACTUAL PROBLEM, not keywords
- "fraud" or "scam" complaints = OTHER (not PAYMENT_ISSUE)
- Promotional tweets = OTHER
- Venting without specific request = OTHER
- Only assign a specific intent if customer has a clear, actionable problem
"""

def build_prompt(conversation_text: str) -> str:
    """Build the classification prompt from conversation text."""
    return f"""{TAXONOMY}

Customer Conversation:
{conversation_text}

Respond with ONLY the intent name (e.g., DELIVERY_LATE). Do not explain."""


def get_customer_text(review):
    """Extract customer text from conversation turns."""
    customer_texts = []
    for turn in review.get('turns', []):
        if turn.get('speaker') == 'Customer':
            customer_texts.append(turn.get('text', ''))
    return ' '.join(customer_texts)


def classify_conversation(client, conversation_text: str) -> dict:
    """
    Classify a conversation using Groq LLM.
    Returns dict with intent, reasoning, and confidence.
    """
    prompt = build_prompt(conversation_text)

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": TAXONOMY},
                {"role": "user", "content": f"Classify this conversation:\n\n{conversation_text}"}
            ],
            temperature=0.1,  # Low temp for consistency
            max_tokens=50
        )

        intent = response.choices[0].message.content.strip()

        # Validate intent is in our taxonomy
        valid_intents = [
            'DELIVERY_MISSING', 'DELIVERY_LATE', 'DELIVERY_TRACKING',
            'ORDER_STATUS', 'ORDER_MODIFY', 'PRODUCT_ISSUE', 'RETURN_REQUEST',
            'REFUND_REQUEST', 'PAYMENT_ISSUE', 'ACCOUNT_ACCESS', 'APP_USAGE',
            'DEVICE_ISSUE', 'VIDEO_STREAMING', 'OTHER'
        ]

        if intent not in valid_intents:
            # Try to match partial
            for valid in valid_intents:
                if valid in intent.upper():
                    intent = valid
                    break
            else:
                intent = 'OTHER'  # Default if no match

        return {
            'intent': intent,
            'model': MODEL,
            'success': True
        }

    except Exception as e:
        return {
            'intent': 'ERROR',
            'error': str(e),
            'success': False
        }


def classify_sample(input_file: str, output_file: str, api_key: str, limit: int = None):
    """
    Classify conversations from input file and save results.
    """
    # Get Groq client
    client = get_client(api_key)

    # Load conversations
    with open(input_file, 'r', encoding='utf-8') as f:
        reviews = json.load(f)

    if limit:
        reviews = reviews[:limit]

    print(f"Loaded {len(reviews)} conversations to classify")

    results = []
    errors = 0

    for i, review in enumerate(reviews):
        conv_id = review.get('conversation_id', f'unknown_{i}')
        customer_text = get_customer_text(review)

        print(f"[{i+1}/{len(reviews)}] Classifying {conv_id}...", end=' ')

        result = classify_conversation(client, customer_text)

        if result['success']:
            print(f"-> {result['intent']}")

            # Compare with assigned if available
            assigned = review.get('assigned_primary_intent', 'N/A')
            if assigned != 'N/A':
                match = "OK" if assigned == result['intent'] else "X"
                print(f"    Assigned: {assigned}, Match: {match}")

            results.append({
                'conversation_id': conv_id,
                'llm_intent': result['intent'],
                'assigned_intent': review.get('assigned_primary_intent'),
                'customer_text': customer_text[:200] + '...' if len(customer_text) > 200 else customer_text,
                'success': True
            })
        else:
            print(f"ERROR: {result.get('error', 'Unknown error')}")
            errors += 1
            results.append({
                'conversation_id': conv_id,
                'llm_intent': 'ERROR',
                'error': result.get('error'),
                'success': False
            })

        # Rate limiting - Groq has limits, be nice
        if (i + 1) % 60 == 0:
            print("\n--- Rate limit pause (60 requests) ---")
            time.sleep(2)

    # Save results
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Print summary
    correct = sum(1 for r in results if r['success'] and r['llm_intent'] == r['assigned_intent'])
    total_with_assign = sum(1 for r in results if r['success'] and r['assigned_intent'] != 'N/A')

    print(f"\n{'='*60}")
    print(f"CLASSIFICATION COMPLETE")
    print(f"{'='*60}")
    print(f"Total: {len(results)}")
    print(f"Errors: {errors}")
    if total_with_assign > 0:
        print(f"Match with assigned: {correct}/{total_with_assign} ({100*correct/total_with_assign:.1f}%)")

    # Intent distribution
    intent_counts = {}
    for r in results:
        if r['success']:
            intent_counts[r['llm_intent']] = intent_counts.get(r['llm_intent'], 0) + 1

    print(f"\nLLM Intent Distribution:")
    for intent, count in sorted(intent_counts.items(), key=lambda x: -x[1]):
        print(f"  {intent}: {count}")

    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Classify conversations using Groq LLM')
    parser.add_argument('--input', default='data/samples/v21_manual_validation_review.json',
                        help='Input JSON file')
    parser.add_argument('--output', default='data/samples/groq_classification_results.json',
                        help='Output JSON file')
    parser.add_argument('--api-key', type=str, default=None,
                        help='Groq API key (or set GROQ_API_KEY env var)')
    parser.add_argument('--limit', type=int, default=None,
                        help='Limit number of conversations to process')

    args = parser.parse_args()

    classify_sample(args.input, args.output, args.api_key, args.limit)
