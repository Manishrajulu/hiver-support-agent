import json
import random
from collections import Counter

# Load V2.1 labeled conversations
v21 = []
with open('data/processed/amazonhelp_labeled_conversations_v21.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        v21.append(json.loads(line))

print(f"Loaded {len(v21)} conversations")

# Fixed seed for reproducibility
random.seed(42)

# Group by primary intent
by_intent = {}
for l in v21:
    intent = l['primary_intent']
    if intent not in by_intent:
        by_intent[intent] = []
    by_intent[intent].append(l)

print("\nV2.1 Distribution:")
for intent, convs in sorted(by_intent.items(), key=lambda x: -len(x[1])):
    print(f"  {intent}: {len(convs)}")

# Target sample sizes
TARGET_SIZES = {
    'PAYMENT_ISSUE': 30,
    'REFUND_REQUEST': 30,
    'DELIVERY_LATE': 30,
    'DELIVERY_MISSING': 30,
    'ORDER_STATUS': 20,
    'APP_USAGE': 20,
    'DEVICE_ISSUE': 20,
    'OTHER': 20
}

# Identify borderline cases for each intent pair
def has_borderline_pattern(text, patterns):
    """Check if text has patterns near decision boundaries"""
    text_lower = text.lower()
    return any(p in text_lower for p in patterns)

def get_customer_text(conv):
    return ' '.join(t.get('text', '') for t in conv['turns'] if t.get('speaker') == 'Customer')

# Define borderline pattern pairs
BORDERLINE_PAIRS = {
    'PAYMENT_ISSUE': {
        'REFUND_REQUEST': [
            'refund', 'money back', 'charged', 'charge',
            'want my money', 'where is my refund'
        ],
        'OTHER': ['payment', 'charged', 'card', 'bank']
    },
    'REFUND_REQUEST': {
        'PAYMENT_ISSUE': ['charged', 'charge', 'payment'],
        'OTHER': ['refund', 'money back']
    },
    'DELIVERY_LATE': {
        'DELIVERY_MISSING': [
            'late', 'delayed', 'never arrived', 'never received',
            'not arrived', 'still waiting', 'when will i get'
        ],
        'OTHER': ['delivery', 'package', 'order']
    },
    'DELIVERY_MISSING': {
        'DELIVERY_LATE': ['late', 'delayed', 'when will', 'expected'],
        'OTHER': ['missing', 'never received', 'never got']
    },
    'OTHER': {
        'DELIVERY_LATE': ['delivery', 'package', 'late', 'waiting'],
        'PAYMENT_ISSUE': ['payment', 'charged', 'card'],
        'REFUND_REQUEST': ['refund', 'money back'],
        'APP_USAGE': ['app', 'website', 'not working']
    }
}

# Select stratified sample
selected = []
selected_ids = set()

def select_sample(intents_list, target_size, intent_name, other_intents_to_check=None):
    """Select a stratified sample with focus on borderline cases"""
    if len(intents_list) <= target_size:
        return intents_list

    # First, collect borderline cases
    borderline_cases = []
    normal_cases = []

    for conv in intents_list:
        customer_text = get_customer_text(conv)

        # Check if borderline with any related intent
        is_borderline = False
        if intent_name in BORDERLINE_PAIRS:
            for other_intent, patterns in BORDERLINE_PAIRS[intent_name].items():
                if has_borderline_pattern(customer_text, patterns):
                    is_borderline = True
                    break

        if is_borderline:
            borderline_cases.append(conv)
        else:
            normal_cases.append(conv)

    print(f"\n  {intent_name}: {len(intents_list)} total, {len(borderline_cases)} borderline, {len(normal_cases)} normal")

    # Ensure we include all borderline cases up to target
    result = []
    selected_ids_local = set()

    # Add all borderline cases first (up to target_size)
    random.shuffle(borderline_cases)
    for conv in borderline_cases:
        if len(result) >= target_size:
            break
        if conv['conversation_id'] not in selected_ids:
            result.append(conv)
            selected_ids_local.add(conv['conversation_id'])

    # Fill remaining with random normal cases
    if len(result) < target_size:
        random.shuffle(normal_cases)
        for conv in normal_cases:
            if len(result) >= target_size:
                break
            if conv['conversation_id'] not in selected_ids:
                result.append(conv)
                selected_ids_local.add(conv['conversation_id'])

    return result

# Select samples for each intent
print("\nSelecting stratified sample...")
sample_by_intent = {}

for intent, target_size in TARGET_SIZES.items():
    if intent in by_intent:
        sample_by_intent[intent] = select_sample(
            by_intent[intent],
            target_size,
            intent
        )
        print(f"  Selected {len(sample_by_intent[intent])} for {intent}")
    else:
        print(f"  WARNING: {intent} not found in V2.1")
        sample_by_intent[intent] = []

# Flatten and add to selected
for intent, convs in sample_by_intent.items():
    for conv in convs:
        if conv['conversation_id'] not in selected_ids:
            selected.append(conv)
            selected_ids.add(conv['conversation_id'])

print(f"\nTotal selected: {len(selected)}")

# Create the sample with review_reason
sample = []

for conv in selected:
    customer_text = get_customer_text(conv)
    primary = conv['primary_intent']

    # Determine review_reason
    review_reason = "random_stratified"

    # Check for borderline cases
    if primary in BORDERLINE_PAIRS:
        for other_intent, patterns in BORDERLINE_PAIRS[primary].items():
            if has_borderline_pattern(customer_text, patterns):
                if other_intent == 'REFUND_REQUEST' or other_intent == 'PAYMENT_ISSUE':
                    review_reason = "payment_refund_boundary"
                    break
                elif other_intent == 'DELIVERY_LATE' or other_intent == 'DELIVERY_MISSING':
                    review_reason = "delivery_late_missing_boundary"
                    break
                else:
                    review_reason = "other_possible_missed_intent"
                    break

    # Check for OTHER borderline
    if primary == 'OTHER':
        has_likely_intent = False
        for other_intent, patterns in BORDERLINE_PAIRS['OTHER'].items():
            if has_borderline_pattern(customer_text, patterns):
                review_reason = "other_possible_missed_intent"
                has_likely_intent = True
                break

    # Build turns list
    turns_list = []
    for i, turn in enumerate(conv['turns']):
        turns_list.append({
            'turn_number': i + 1,
            'speaker': turn.get('speaker', 'Unknown'),
            'text': turn.get('text', '')
        })

    sample.append({
        'conversation_id': conv['conversation_id'],
        'assigned_primary_intent': primary,
        'assigned_secondary_intents': conv.get('secondary_intents', []),
        'confidence': conv.get('confidence', 'UNKNOWN'),
        'num_turns': len(conv['turns']),
        'turns': turns_list,
        'review_reason': review_reason
    })

# Shuffle the final sample
random.shuffle(sample)

# Save the sample
with open('data/samples/v21_manual_validation_sample.json', 'w', encoding='utf-8') as f:
    json.dump(sample, f, indent=2, ensure_ascii=False)

print(f"\nSaved manual validation sample with {len(sample)} conversations")

# Print summary by review_reason
reason_counts = Counter(s['review_reason'] for s in sample)
print("\nSample by review_reason:")
for reason, count in reason_counts.most_common():
    print(f"  {reason}: {count}")

# Print summary by intent
intent_counts = Counter(s['assigned_primary_intent'] for s in sample)
print("\nSample by assigned_intent:")
for intent, count in intent_counts.most_common():
    print(f"  {intent}: {count}")