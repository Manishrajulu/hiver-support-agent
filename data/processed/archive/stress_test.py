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

# ============================================
# TEST 1: Analyze each leaf intent with examples
# ============================================

# Define patterns for each leaf intent
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

# Collect examples for each intent
intent_examples = defaultdict(list)
for conv in sample:
    customer_msgs = [t['text'] for t in conv['turns'] if t['speaker'] == 'Customer']
    all_text = ' '.join(customer_msgs).lower()

    for intent, keywords in leaf_patterns.items():
        if any(kw in all_text for kw in keywords):
            if len(intent_examples[intent]) < 20:  # Collect up to 20
                intent_examples[intent].append(conv)

# Print analysis for each intent
print("\n" + "="*70)
print("STRESS TEST: LEAF INTENT ANALYSIS")
print("="*70)

for intent, examples in sorted(intent_examples.items()):
    print(f"\n### {intent}: {len(examples)} examples ###")

# ============================================
# TEST 2: Analyze specific boundaries
# ============================================

print("\n\n" + "="*70)
print("BOUNDARY ANALYSIS")
print("="*70)

# A. ORDER_STATUS vs DELIVERY_TRACKING
print("\n--- A. ORDER_STATUS vs DELIVERY_TRACKING ---")
order_delivery_overlap = 0
for conv in sample:
    customer_msgs = [t['text'] for t in conv['turns'] if t['speaker'] == 'Customer']
    all_text = ' '.join(customer_msgs).lower()
    has_order = any(kw in all_text for kw in ['order status', 'where is my order', 'order number'])
    has_tracking = any(kw in all_text for kw in ['tracking', 'track'])
    if has_order and has_tracking:
        order_delivery_overlap += 1
print(f"Conversations with BOTH order and tracking keywords: {order_delivery_overlap}")

# B. DELIVERY_CARRIER as modifier vs primary
print("\n--- B. DELIVERY_CARRIER analysis ---")
carrier_primary = 0  # carrier is main issue
carrier_context = 0  # carrier mentioned but not main issue
for conv in sample:
    customer_msgs = [t['text'] for t in conv['turns'] if t['speaker'] == 'Customer']
    all_text = ' '.join(customer_msgs).lower()
    has_carrier = any(kw in all_text for kw in ['gati', 'dtdc', 'fedex', 'ups', 'usps', 'courier', 'carrier', 'delivery partner'])
    if has_carrier:
        has_delivery = any(kw in all_text for kw in ['delivery', 'delivered', 'late', 'missing'])
        if has_delivery:
            carrier_context += 1
        else:
            carrier_primary += 1
print(f"Carrier as primary issue: {carrier_primary}")
print(f"Carrier mentioned in delivery context: {carrier_context}")

# C. APP_USAGE vs ACCOUNT_ACCESS
print("\n--- C. APP_USAGE vs ACCOUNT_ACCESS ---")
app_login_overlap = 0
for conv in sample:
    customer_msgs = [t['text'] for t in conv['turns'] if t['speaker'] == 'Customer']
    all_text = ' '.join(customer_msgs).lower()
    has_app = any(kw in all_text for kw in ['app', 'website', 'not working', 'error'])
    has_login = any(kw in all_text for kw in ['login', 'password', 'locked', 'access'])
    if has_app and has_login:
        app_login_overlap += 1
print(f"Conversations with BOTH app and login keywords: {app_login_overlap}")

# D. PRODUCT_ISSUE vs RETURN_REQUEST
print("\n--- D. PRODUCT_ISSUE vs RETURN_REQUEST ---")
product_return_overlap = 0
for conv in sample:
    customer_msgs = [t['text'] for t in conv['turns'] if t['speaker'] == 'Customer']
    all_text = ' '.join(customer_msgs).lower()
    has_product = any(kw in all_text for kw in ['wrong item', 'damaged', 'defective', 'broken', 'not as described'])
    has_return = any(kw in all_text for kw in ['return', 'exchange', 'replacement'])
    if has_product and has_return:
        product_return_overlap += 1
print(f"Conversations with BOTH product and return keywords: {product_return_overlap}")

# E. REFUND_REQUEST vs PAYMENT_ISSUE
print("\n--- E. REFUND_REQUEST vs PAYMENT_ISSUE ---")
refund_payment_overlap = 0
for conv in sample:
    customer_msgs = [t['text'] for t in conv['turns'] if t['speaker'] == 'Customer']
    all_text = ' '.join(customer_msgs).lower()
    has_refund = any(kw in all_text for kw in ['refund', 'money back', 'reimburse'])
    has_payment = any(kw in all_text for kw in ['payment', 'billing', 'credit card', 'gift card'])
    if has_refund and has_payment:
        refund_payment_overlap += 1
print(f"Conversations with BOTH refund and payment keywords: {refund_payment_overlap}")

# F. DEVICE_ISSUE vs VIDEO_STREAMING
print("\n--- F. DEVICE_ISSUE vs VIDEO_STREAMING ---")
device_video_overlap = 0
for conv in sample:
    customer_msgs = [t['text'] for t in conv['turns'] if t['speaker'] == 'Customer']
    all_text = ' '.join(customer_msgs).lower()
    has_device = any(kw in all_text for kw in ['kindle', 'fire tv', 'echo', 'alexa', 'tablet', 'device'])
    has_video = any(kw in all_text for kw in ['video', 'streaming', 'prime video', 'subtitle', 'playback'])
    if has_device and has_video:
        device_video_overlap += 1
print(f"Conversations with BOTH device and video keywords: {device_video_overlap}")

# ============================================
# TEST 3: Analyze OTHER category
# ============================================

print("\n\n" + "="*70)
print("OTHER CATEGORY ANALYSIS")
print("="*70)

other_convs = []
for conv in sample:
    customer_msgs = [t['text'] for t in conv['turns'] if t['speaker'] == 'Customer']
    all_text = ' '.join(customer_msgs).lower()

    # Check if matches any intent
    matched = False
    for intent, keywords in leaf_patterns.items():
        if any(kw in all_text for kw in keywords):
            matched = True
            break
    if not matched:
        other_convs.append(conv)

print(f"Conversations in OTHER: {len(other_convs)}")

# Analyze OTHER keywords
other_keywords = Counter()
for conv in other_convs:
    customer_msgs = [t['text'] for t in conv['turns'] if t['speaker'] == 'Customer']
    all_text = ' '.join(customer_msgs)
    words = all_text.split()
    for word in words[:30]:
        word_clean = re.sub(r'[@#]', '', word.lower())
        if len(word_clean) > 3:
            other_keywords[word_clean] += 1

print("\nTop keywords in OTHER:")
for word, count in other_keywords.most_common(25):
    print(f"  {word}: {count}")

# ============================================
# TEST 4: Multi-intent analysis
# ============================================

print("\n\n" + "="*70)
print("MULTI-INTENT ANALYSIS")
print("="*70)

multi_intent_convs = []
for conv in sample:
    customer_msgs = [t['text'] for t in conv['turns'] if t['speaker'] == 'Customer']
    all_text = ' '.join(customer_msgs).lower()

    matched_intents = []
    for intent, keywords in leaf_patterns.items():
        if any(kw in all_text for kw in keywords):
            matched_intents.append(intent)

    if len(matched_intents) >= 2:
        multi_intent_convs.append({
            'conv': conv,
            'intents': matched_intents
        })

print(f"Conversations with 2+ intents: {len(multi_intent_convs)}")

# Analyze intent pairs
intent_pairs = Counter()
for item in multi_intent_convs:
    intents = item['intents']
    for i in range(len(intents)):
        for j in range(i+1, len(intents)):
            pair = tuple(sorted([intents[i], intents[j]]))
            intent_pairs[pair] += 1

print("\nMost common intent pairs:")
for pair, count in intent_pairs.most_common(15):
    print(f"  {pair}: {count}")

# ============================================
# TEST 5: Escalation signals analysis
# ============================================

print("\n\n" + "="*70)
print("ESCALATION SIGNAL ANALYSIS")
print("="*70)

escalation_patterns = {
    'FRUSTRATION_HIGH': ['angry', 'furious', 'frustrated', 'awful', 'terrible', 'worst', 'pathetic', 'disgusting'],
    'PREVIOUS_CONTACT': ['already contacted', 'already called', 'spoken to', 'tried calling', 'multiple times', 'several times', 'days ago', 'weeks'],
    'ESCALATION_REQUEST': ['manager', 'supervisor', 'escalate', 'call me back', 'callback', 'speak to someone'],
    'SERVICE_COMPLAINT': ['worst service', 'bad service', 'poor service', 'rude', 'no response']
}

escalation_counts = Counter()
for conv in sample:
    customer_msgs = [t['text'] for t in conv['turns'] if t['speaker'] == 'Customer']
    all_text = ' '.join(customer_msgs).lower()

    for signal, keywords in escalation_patterns.items():
        if any(kw in all_text for kw in keywords):
            escalation_counts[signal] += 1

print("Escalation signal frequency:")
for signal, count in escalation_counts.most_common():
    print(f"  {signal}: {count}")

# ============================================
# TEST 6: Primary intent selection analysis
# ============================================

print("\n\n" + "="*70)
print("PRIMARY INTENT SELECTION TEST")
print("="*70)

# For multi-intent convs, determine what should be primary
# Rule being tested: first intent by keyword frequency

def determine_primary(intents, text):
    """Determine primary intent based on rules"""
    counts = []
    for intent in intents:
        keywords = leaf_patterns.get(intent, [])
        count = sum(1 for kw in keywords if kw in text)
        counts.append((intent, count))
    counts.sort(key=lambda x: x[1], reverse=True)
    return counts[0][0] if counts else intents[0]

primary_decisions = Counter()
for item in multi_intent_convs[:30]:  # Sample 30
    conv = item['conv']
    intents = item['intents']
    customer_msgs = [t['text'] for t in conv['turns'] if t['speaker'] == 'Customer']
    all_text = ' '.join(customer_msgs).lower()
    primary = determine_primary(intents, all_text)
    primary_decisions[primary] += 1

print("\nPrimary intent decisions (sample of 30):")
for intent, count in primary_decisions.most_common():
    print(f"  {intent}: {count}")

# Save results
results = {
    'intent_examples': {k: len(v) for k, v in intent_examples.items()},
    'boundary_analysis': {
        'order_delivery_overlap': order_delivery_overlap,
        'carrier_primary': carrier_primary,
        'carrier_context': carrier_context,
        'app_login_overlap': app_login_overlap,
        'product_return_overlap': product_return_overlap,
        'refund_payment_overlap': refund_payment_overlap,
        'device_video_overlap': device_video_overlap
    },
    'other_count': len(other_convs),
    'multi_intent_count': len(multi_intent_convs),
    'escalation_counts': dict(escalation_counts),
    'top_intent_pairs': dict(intent_pairs.most_common(15))
}

with open(r'C:\Users\DELL\Desktop\hiver\data\processed\stress_test_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2)

print("\n\nStress test results saved.")
