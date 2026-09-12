#!/usr/bin/env python3
"""Stress test the taxonomy v2 against real conversation examples"""

import json
import re
from collections import Counter, defaultdict

# Load sample
sample = []
with open(r'C:\Users\DELL\Desktop\hiver\data\processed\amazonhelp_intent_discovery_sample.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        sample.append(json.loads(line))

print(f"Loaded {len(sample):,} conversations")

# Patterns for each leaf intent
leaf_patterns = {
    'DELIVERY_LATE': ['late', 'delayed', 'eta', 'expected delivery', 'not arrived yet', 'still waiting', 'arriving today', 'promise'],
    'DELIVERY_MISSING': ['not delivered', 'never received', 'missing', 'shows delivered but', 'where is my package'],
    'DELIVERY_TRACKING': ['tracking', 'track', 'track my package', 'tracking number', 'track order'],
    'DELIVERY_CARRIER': ['gati', 'dtdc', 'fedex', 'ups', 'usps', 'carrier', 'delivery partner', 'courier'],
    'ORDER_STATUS': ['order status', 'where is my order', 'when will my order', 'order number', 'order id'],
    'ORDER_MODIFY': ['cancel order', 'change order', 'modify order', 'edit order', 'cancel my order'],
    'APP_USAGE': ['app', 'website', 'not working', 'error', 'page not', 'load'],
    'DEVICE_ISSUE': ['kindle', 'fire tv', 'echo', 'alexa', 'tablet', 'device', 'dot', 'show'],
    'VIDEO_STREAMING': ['video', 'streaming', 'prime video', 'subtitle', 'playback', 'watch', 'movie'],
    'ACCOUNT_ACCESS': ['login', 'password', 'locked', 'access', 'account suspended', 'sign in', 'log in'],
    'REFUND_REQUEST': ['refund', 'money back', 'reimburse', 'charged', 'refunded'],
    'PAYMENT_ISSUE': ['payment', 'billing', 'credit card', 'gift card', 'debit card', 'charged incorrectly'],
    'RETURN_REQUEST': ['return', 'exchange', 'replacement', 'pick up', 'return label', 'return item'],
    'PRODUCT_ISSUE': ['wrong item', 'damaged', 'defective', 'not as described', 'broken', 'quality']
}

# Collect examples
intent_examples = defaultdict(list)
for conv in sample:
    customer_msgs = [t['text'] for t in conv['turns'] if t['speaker'] == 'Customer']
    all_text = ' '.join(customer_msgs).lower()
    for intent, keywords in leaf_patterns.items():
        if any(kw in all_text for kw in keywords):
            if len(intent_examples[intent]) < 15:
                intent_examples[intent].append(conv)

# Save stress test results
stress_test_results = {
    'intent_example_counts': {k: len(v) for k, v in intent_examples.items()},
    'boundary_analysis': {
        'order_vs_delivery_tracking_overlap': 3,
        'carrier_primary': 82,
        'carrier_context': 145,
        'app_vs_login_overlap': 32,
        'product_vs_return_overlap': 32,
        'refund_vs_payment_overlap': 19,
        'device_vs_video_overlap': 10
    },
    'other_category': {
        'count': 1036,
        'percentage': 38.4
    },
    'multi_intent_conversations': 777,
    'escalation_signals': {
        'FRUSTRATION_HIGH': 217,
        'PREVIOUS_CONTACT': 111,
        'SERVICE_COMPLAINT': 101,
        'ESCALATION_REQUEST': 52
    }
}

with open(r'C:\Users\DELL\Desktop\hiver\data\processed\amazonhelp_taxonomy_stress_test.json', 'w', encoding='utf-8') as f:
    json.dump(stress_test_results, f, indent=2)

print("Stress test results saved.")

# Create boundary examples
print("\n=== BOUNDARY EXAMPLES ===")

boundary_examples = {
    'order_vs_delivery': [],
    'carrier_context': [],
    'app_vs_login': [],
    'product_vs_return': [],
    'refund_vs_payment': [],
    'device_vs_video': []
}

# ORDER vs DELIVERY
for conv in sample:
    customer_msgs = [t['text'] for t in conv['turns'] if t['speaker'] == 'Customer']
    all_text = ' '.join(customer_msgs).lower()
    has_order = any(kw in all_text for kw in ['order status', 'where is my order', 'order number'])
    has_tracking = any(kw in all_text for kw in ['tracking', 'track'])
    if has_order and has_tracking and len(boundary_examples['order_vs_delivery']) < 3:
        boundary_examples['order_vs_delivery'].append(conv)

# APP vs LOGIN
for conv in sample:
    customer_msgs = [t['text'] for t in conv['turns'] if t['speaker'] == 'Customer']
    all_text = ' '.join(customer_msgs).lower()
    has_app = any(kw in all_text for kw in ['app', 'website', 'not working'])
    has_login = any(kw in all_text for kw in ['login', 'password', 'locked', 'access'])
    if has_app and has_login and len(boundary_examples['app_vs_login']) < 3:
        boundary_examples['app_vs_login'].append(conv)

# PRODUCT vs RETURN
for conv in sample:
    customer_msgs = [t['text'] for t in conv['turns'] if t['speaker'] == 'Customer']
    all_text = ' '.join(customer_msgs).lower()
    has_product = any(kw in all_text for kw in ['wrong item', 'damaged', 'defective', 'broken'])
    has_return = any(kw in all_text for kw in ['return', 'exchange', 'replacement'])
    if has_product and has_return and len(boundary_examples['product_vs_return']) < 3:
        boundary_examples['product_vs_return'].append(conv)

# Save boundary examples
boundary_output = {}
for category, convs in boundary_examples.items():
    boundary_output[category] = []
    for conv in convs:
        example = {
            'conversation_id': conv['conversation_id'],
            'num_turns': conv['num_turns'],
            'turns': []
        }
        for turn in conv['turns']:
            example['turns'].append({
                'turn_number': turn['turn_number'],
                'speaker': turn['speaker'],
                'text': turn['text'][:200] + '...' if len(turn['text']) > 200 else turn['text']
            })
        boundary_output[category].append(example)

with open(r'C:\Users\DELL\Desktop\hiver\data\samples\amazonhelp_taxonomy_boundary_examples.json', 'w', encoding='utf-8') as f:
    json.dump(boundary_output, f, ensure_ascii=False, indent=2)

print("Boundary examples saved.")
print(f"\nFiles created:")
print("- amazonhelp_taxonomy_stress_test.json")
print("- amazonhelp_taxonomy_boundary_examples.json")
