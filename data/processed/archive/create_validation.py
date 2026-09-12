#!/usr/bin/env python3
"""Create validation examples for proposed intents"""

import json
import re
from collections import defaultdict

# Load sample
sample = []
with open(r'C:\Users\DELL\Desktop\hiver\data\processed\amazonhelp_intent_discovery_sample.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        sample.append(json.loads(line))

print(f"Loaded {len(sample):,} conversations")

# Define sub-intent patterns
sub_intent_patterns = {
    'DELIVERY_LATE': ['late', 'delayed', 'eta', 'expected delivery', 'not arrived yet', 'still waiting'],
    'DELIVERY_MISSING': ['not delivered', 'never received', 'missing', 'shows delivered'],
    'DELIVERY_TRACKING': ['tracking', 'track', 'where is my package', 'status'],
    'DELIVERY_CARRIER': ['carrier', 'gati', 'dtdc', 'fedex', 'ups', 'usps', 'delivery partner'],
    'ORDER_STATUS': ['order status', 'where is my order', 'when will', 'order number'],
    'ORDER_MODIFY': ['cancel order', 'change order', 'modify order', 'edit order'],
    'APP_USAGE': ['app', 'website', 'not working', 'error', 'page'],
    'DEVICE_ISSUE': ['kindle', 'fire tv', 'echo', 'alexa', 'tablet', 'device'],
    'VIDEO_STREAMING': ['video', 'streaming', 'prime video', 'subtitle', 'playback', 'watch'],
    'ACCOUNT_ACCESS': ['login', 'password', 'locked', 'access', 'account suspended', 'sign in'],
    'REFUND_REQUEST': ['refund', 'money back', 'reimburse', 'charged'],
    'PAYMENT_ISSUE': ['payment', 'billing', 'credit card', 'gift card'],
    'RETURN_REQUEST': ['return', 'exchange', 'replacement', 'pick up', 'return label'],
    'PRODUCT_ISSUE': ['wrong item', 'damaged', 'defective', 'not as described', 'broken']
}

# Collect examples for each sub-intent
intent_examples = defaultdict(list)

for conv in sample:
    customer_msgs = [t['text'] for t in conv['turns'] if t['speaker'] == 'Customer']
    all_text = ' '.join(customer_msgs).lower()

    for intent, keywords in sub_intent_patterns.items():
        if any(kw in all_text for kw in keywords):
            if len(intent_examples[intent]) < 8:
                # Create example structure
                example = {
                    'conversation_id': conv['conversation_id'],
                    'num_turns': conv['num_turns'],
                    'turns': []
                }
                for turn in conv['turns']:
                    example['turns'].append({
                        'turn_number': turn['turn_number'],
                        'speaker': turn['speaker'],
                        'text': turn['text'][:300] + '...' if len(turn['text']) > 300 else turn['text']
                    })
                intent_examples[intent].append(example)

# Print summary
print("\nValidation examples collected:")
for intent, examples in intent_examples.items():
    print(f"  {intent}: {len(examples)} examples")

# Save
output = {}
for intent, examples in intent_examples.items():
    output[intent] = {
        'intent_id': intent,
        'example_count': len(examples),
        'examples': examples
    }

with open(r'C:\Users\DELL\Desktop\hiver\data\samples\amazonhelp_taxonomy_validation_examples.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\nValidation examples saved to: amazonhelp_taxonomy_validation_examples.json")
