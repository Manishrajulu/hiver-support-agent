#!/usr/bin/env python3
"""Taxonomy refinement analysis"""

import json
import re
from collections import Counter, defaultdict

# Load the sample conversations
sample = []
with open(r'C:\Users\DELL\Desktop\hiver\data\processed\amazonhelp_intent_discovery_sample.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        sample.append(json.loads(line))

print(f"Loaded {len(sample):,} conversations")

def identify_primary_intent(conv):
    """Identify the PRIMARY customer intent from a conversation."""
    customer_msgs = [t['text'] for t in conv['turns'] if t['speaker'] == 'Customer']
    all_text = ' '.join(customer_msgs).lower()

    # Context/modifiers (not primary intents)
    is_prime = 'prime' in all_text
    is_marketplace = any(x in all_text for x in ['amazon.fr', 'amazon.in', 'amazon.uk', 'amazon.de'])

    # Escalation signals (not primary intents)
    escalation_signals = [
        'escalate', 'manager', 'supervisor', 'call', 'phone', 'contact',
        'no response', 'never got', 'still waiting', 'still no',
        'still unresolved', 'still not resolved', 'another agent', 'different agent'
    ]
    has_escalation = any(sig in all_text for sig in escalation_signals)

    # Service complaints (sentiment, not primary intent)
    service_complaint_signals = [
        'worst service', 'terrible', 'awful', 'pathetic', 'rude', 'poor service',
        'bad service', 'disappointed', 'frustrated', 'angry'
    ]
    has_service_complaint = any(sig in all_text for sig in service_complaint_signals)

    # DELIVERY issues
    delivery_keywords = [
        'deliver', 'delivery', 'delivered', 'package', 'shipped', 'shipping',
        'tracking', 'track', 'late', 'delayed', 'lost', 'missing', 'not delivered',
        'eta', 'expected delivery', 'arriving'
    ]
    has_delivery_issue = any(kw in all_text for kw in delivery_keywords)

    # ORDER issues
    order_keywords = [
        'order', 'ordered', 'ordering', 'order status', 'order number',
        'cancel order', 'modify order', 'change order'
    ]
    has_order_issue = any(kw in all_text for kw in order_keywords)

    # REFUND issues
    refund_keywords = [
        'refund', 'money back', 'reimburse', 'reimbursement',
        'charged', 'overcharged', 'pending refund', 'where is my refund',
        'not refunded', 'refund status'
    ]
    has_refund_issue = any(kw in all_text for kw in refund_keywords)

    # RETURN/EXCHANGE issues
    return_keywords = [
        'return', 'returned', 'returning', 'exchange', 'replacement',
        'pickup', 'pick up', 'return label'
    ]
    has_return_issue = any(kw in all_text for kw in return_keywords)

    # ACCOUNT issues
    account_keywords = [
        'account', 'login', 'log in', 'password', 'locked', 'access',
        'sign in', 'suspended', 'closed account'
    ]
    has_account_issue = any(kw in all_text for kw in account_keywords)

    # PRIME issues
    prime_keywords = [
        'prime membership', 'prime member', 'prime subscription',
        'cancel prime', 'prime cancel', 'renew prime'
    ]
    has_prime_issue = any(kw in all_text for kw in prime_keywords)

    # PAYMENT issues
    payment_keywords = [
        'payment', 'pay', 'billing', 'credit card', 'debit card',
        'gift card', 'balance', 'transaction', 'charged'
    ]
    has_payment_issue = any(kw in all_text for kw in payment_keywords)

    # TECHNICAL issues
    technical_keywords = [
        'app', 'website', 'not working', 'error', 'crash', 'bug',
        'kindle', 'fire tv', 'echo', 'alexa', 'device',
        'video', 'subtitle', 'streaming', 'prime video', 'login issue'
    ]
    has_technical_issue = any(kw in all_text for kw in technical_keywords)

    # PRODUCT quality issues
    product_keywords = [
        'product', 'item', 'quality', 'damaged', 'wrong item',
        'missing parts', 'defective', 'broken', 'not as described',
        'counterfeit', 'fake'
    ]
    has_product_issue = any(kw in all_text for kw in product_keywords)

    # Count intent matches
    intents = []
    if has_delivery_issue: intents.append(('DELIVERY', sum(1 for kw in delivery_keywords if kw in all_text)))
    if has_order_issue: intents.append(('ORDER', sum(1 for kw in order_keywords if kw in all_text)))
    if has_refund_issue: intents.append(('REFUND', sum(1 for kw in refund_keywords if kw in all_text)))
    if has_return_issue: intents.append(('RETURN', sum(1 for kw in return_keywords if kw in all_text)))
    if has_account_issue: intents.append(('ACCOUNT', sum(1 for kw in account_keywords if kw in all_text)))
    if has_prime_issue: intents.append(('PRIME', sum(1 for kw in prime_keywords if kw in all_text)))
    if has_payment_issue: intents.append(('PAYMENT', sum(1 for kw in payment_keywords if kw in all_text)))
    if has_technical_issue: intents.append(('TECHNICAL', sum(1 for kw in technical_keywords if kw in all_text)))
    if has_product_issue: intents.append(('PRODUCT', sum(1 for kw in product_keywords if kw in all_text)))

    intents.sort(key=lambda x: x[1], reverse=True)

    if intents:
        primary = intents[0][0]
    else:
        primary = 'OTHER'

    return {
        'primary_intent': primary,
        'has_prime_context': is_prime,
        'has_marketplace_context': is_marketplace,
        'has_escalation_signal': has_escalation,
        'has_service_complaint': has_service_complaint,
        'all_intents': [x[0] for x in intents]
    }

# Analyze all conversations
primary_counts = Counter()
for conv in sample:
    result = identify_primary_intent(conv)
    primary_counts[result['primary_intent']] += 1

print("\n=== REFINED PRIMARY INTENT DISTRIBUTION ===\n")
for intent, count in primary_counts.most_common():
    pct = count / len(sample) * 100
    print(f"  {intent}: {count:,} ({pct:.1f}%)")

# Save
with open(r'C:\Users\DELL\Desktop\hiver\data\processed\refined_intent_analysis.json', 'w', encoding='utf-8') as f:
    json.dump({'primary_intent_distribution': dict(primary_counts), 'sample_size': len(sample)}, f, indent=2)

print("\nRefined analysis saved.")
