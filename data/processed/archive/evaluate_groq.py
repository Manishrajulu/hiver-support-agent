#!/usr/bin/env python3
"""
Evaluate Groq LLM on the exact same 540 test conversations as the baseline.
"""

import json
import os
import time
from groq import Groq
from dotenv import load_dotenv

# Load API key
load_dotenv(os.path.join(os.path.dirname(__file__), 'api_key.env'))

# Groq client
client = Groq(api_key=os.environ.get('GROQ_API_KEY'))
MODEL = "allam-2-7b"

# Taxonomy
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

Respond with ONLY the intent name (e.g., DELIVERY_LATE). Do not explain.
"""

def get_customer_text(conv):
    """Extract customer text from conversation."""
    texts = []
    for turn in conv.get('turns', []):
        if turn.get('speaker') == 'Customer':
            texts.append(turn.get('text', ''))
    return ' '.join(texts)

def classify(client, text):
    """Classify using Groq."""
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": TAXONOMY},
                {"role": "user", "content": f"Classify this conversation:\n\n{text}"}
            ],
            temperature=0.1,
            max_tokens=50
        )
        intent = response.choices[0].message.content.strip()

        # Validate
        valid_intents = [
            'DELIVERY_MISSING', 'DELIVERY_LATE', 'DELIVERY_TRACKING',
            'ORDER_STATUS', 'ORDER_MODIFY', 'PRODUCT_ISSUE', 'RETURN_REQUEST',
            'REFUND_REQUEST', 'PAYMENT_ISSUE', 'ACCOUNT_ACCESS', 'APP_USAGE',
            'DEVICE_ISSUE', 'VIDEO_STREAMING', 'OTHER'
        ]
        if intent not in valid_intents:
            for valid in valid_intents:
                if valid in intent.upper():
                    intent = valid
                    break
            else:
                intent = 'OTHER'

        return {'intent': intent, 'success': True}
    except Exception as e:
        return {'intent': 'ERROR', 'error': str(e), 'success': False}

# Load test split
with open('data/baseline/baseline_train_test_split.json', 'r') as f:
    split = json.load(f)
test_ids = set(split['test_ids'])

# Load test conversations
convos = {}
with open('data/processed/amazonhelp_labeled_conversations_v21.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        conv = json.loads(line)
        if conv['conversation_id'] in test_ids:
            convos[conv['conversation_id']] = conv

print(f"Loaded {len(convos)} test conversations")

# Run Groq classification
results = []
for i, conv_id in enumerate(sorted(convos.keys())):
    conv = convos[conv_id]
    customer_text = get_customer_text(conv)
    actual = conv['primary_intent']

    print(f"[{i+1}/540] {conv_id}...", end=' ')

    result = classify(client, customer_text)

    if result['success']:
        print(f"-> {result['intent']}")

        results.append({
            'conversation_id': conv_id,
            'actual_intent': actual,
            'groq_predicted_intent': result['intent'],
            'success': True
        })
    else:
        print(f"ERROR: {result.get('error', 'Unknown')}")
        results.append({
            'conversation_id': conv_id,
            'actual_intent': actual,
            'groq_predicted_intent': 'ERROR',
            'success': False
        })

    # Rate limiting
    if (i + 1) % 60 == 0:
        print(f"\n--- Pause at {i+1} ---")
        time.sleep(2)

# Save results
output_path = 'data/evaluation/groq_test_predictions.jsonl'
with open(output_path, 'w', encoding='utf-8') as f:
    for r in results:
        f.write(json.dumps(r, ensure_ascii=False) + '\n')

print(f"\nSaved: {output_path}")
print(f"Total: {len(results)}")
print(f"Success: {sum(1 for r in results if r['success'])}")
print(f"Errors: {sum(1 for r in results if not r['success'])}")
