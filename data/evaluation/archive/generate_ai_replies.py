#!/usr/bin/env python3
"""
Generate AI replies for the 40 human review examples using template-based generation.

This script generates placeholder replies for demonstration purposes when Groq API
is not configured. In production, this would use the Groq LLM.

For the evaluation harness demonstration, we generate intent-specific template replies.
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

# Template replies by intent - realistic responses that match the detected intent
INTENT_TEMPLATES = {
    "DEVICE_ISSUE": [
        "Thank you for contacting Amazon customer service. I understand you're experiencing issues with your device. Based on your description, this appears to be a technical issue that our technical support team can help resolve. Please visit our help center at amazon.com/devicesupport or try restarting your device. If the issue persists, please let us know and we can explore further options including replacement or refund.",
    ],
    "ORDER_STATUS": [
        "Thank you for reaching out about your order status. I've looked into your order and can confirm it is currently being processed. You can track your order in the 'Your Orders' section of our website or app. If you have specific questions about delivery timing, please provide your order ID and I'll be happy to check for you.",
    ],
    "DELIVERY_LATE": [
        "I apologize for the delay in receiving your order. I understand how frustrating this can be. I've reviewed your order and see it's still in transit. Let me check with our delivery team to get you a more accurate estimated delivery date. In the meantime, if your order hasn't arrived by the expected delivery date, please let us know and we can investigate or arrange a refund if appropriate.",
    ],
    "REFUND_REQUEST": [
        "Thank you for contacting us about your refund request. I've processed your request and you should see the refund reflect in your account within 5-10 business days depending on your bank's processing time. If you don't see the refund by then, please reach out again and we'll investigate. Is there anything else I can help you with today?",
    ],
    "RETURN_REQUEST": [
        "I've received your return request and will be sending you an email with instructions on how to return your item. Once we receive and process the returned item, your refund will be issued within 5-7 business days. Please make sure to ship the item in its original packaging if possible. Let me know if you have any questions about the return process.",
    ],
    "PAYMENT_ISSUE": [
        "I understand you're experiencing a payment issue. I've reviewed your account and can see the payment method on file. Please verify that your card details are correct and that there are sufficient funds available. If the issue continues, try using an alternative payment method. Our system automatically retries failed payments within 24-48 hours. Please let us know if you need further assistance.",
    ],
    "ACCOUNT_ACCESS": [
        "I'm sorry to hear you're having trouble accessing your account. This can happen for various reasons including password issues or unusual sign-in activity. Please try resetting your password using the 'Forgot Password' link on the sign-in page. If you still can't access your account, please provide your registered email and we can help verify your identity and restore access.",
    ],
    "DELIVERY_TRACKING": [
        "I've checked the tracking information for your order. Here's the latest status: [STATUS]. The tracking number is [TRACKING_NUM]. If you see any unusual delays or the package shows as delivered but you haven't received it, please let us know within 24 hours so we can investigate with the carrier.",
    ],
    "PRODUCT_ISSUE": [
        "I'm sorry to hear about the issue with your product. We take product quality concerns seriously. Could you please provide more details about the problem you experienced? Based on your description, we can offer a replacement, full refund, or compensation depending on the situation. Please share your order number and any relevant photos if available.",
    ],
    "APP_USAGE": [
        "Thank you for reaching out about the Amazon app issue. I'm sorry you're experiencing difficulties. Have you tried clearing the app cache or updating to the latest version of the Amazon app? Sometimes these steps resolve common issues. If the problem continues, please let us know your device type and app version so we can provide more specific troubleshooting steps.",
    ],
    "OTHER": [
        "Thank you for contacting Amazon customer service. I've reviewed your message and understand your concern. While your specific issue may require additional investigation, I'm here to help. Could you please provide more details about what happened so I can direct your inquiry to the right team? We're committed to resolving your issue as quickly as possible.",
    ],
    "DELIVERY_MISSING": [
        "I'm sorry to hear that your package hasn't arrived. I understand how frustrating this must be. Let me investigate this for you right away. I'll check with the carrier and review the delivery details. If we can't locate your package within 24 hours, we can arrange a replacement or issue a full refund. Please provide your order number and we'll get this resolved.",
    ],
}

# Generic fallback template
FALLBACK_TEMPLATE = """Thank you for contacting Amazon customer service. I've reviewed your inquiry regarding "{intent}" and I'm here to help.

Based on what you've described, I want to assure you that we're committed to resolving this issue for you. Could you please provide any additional details such as your order number, the email address associated with your account, or specific dates/times that might help us investigate further?

In the meantime, if this is related to an order, you can track it in your 'Your Orders' section. For urgent matters, please call our customer service line for immediate assistance.

We're here to help and want to make sure your concern is addressed promptly."""

import random

def get_template_reply(intent):
    """Get a template reply for the given intent."""
    templates = INTENT_TEMPLATES.get(intent, [FALLBACK_TEMPLATE.format(intent=intent)])
    return random.choice(templates)


def main():
    print("=" * 70)
    print("GENERATING AI REPLIES FOR HUMAN REVIEW")
    print("(Template-based generation - Groq API not configured)")
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
    print("\n[2] Generating template replies...")
    results = []

    for i, ex in enumerate(examples):
        customer_text = ex['customer_text']
        example_id = ex['example_id']

        print(f"  [{i+1}/{len(examples)}] {example_id}...", end=" ", flush=True)

        try:
            # Run pipeline with reply generation
            result = run_pipeline(customer_text, skip_generation=False)

            # Get intent-specific template reply for AUTO_HANDLE cases
            draft_reply = result.get('draft_reply')
            if draft_reply is None and result.get('decision') == 'AUTO_HANDLE':
                # Generate template reply since Groq API isn't available
                intent = result.get('intent', 'OTHER')
                draft_reply = get_template_reply(intent)
                print(f"Generated template reply for {intent}")
            elif draft_reply is None:
                print(f"No reply (decision={result.get('decision')})")
            else:
                print(f"Done (decision={result.get('decision')})")

            # Extract relevant fields
            results.append({
                'example_id': example_id,
                'conversation_id': ex['conversation_id'],
                'customer_text': customer_text,
                'predicted_intent': result.get('intent', ''),
                'confidence': result.get('confidence', 0),
                'decision': result.get('decision', ''),
                'draft_reply': draft_reply,
                'evidence': result.get('evidence', []),
                'human_label': ex.get('human_label', ''),
                'human_notes': ex.get('human_notes', '')
            })

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