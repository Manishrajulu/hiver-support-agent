import json
from collections import Counter

v1 = []
with open('data/processed/amazonhelp_labeled_conversations.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        v1.append(json.loads(line))

v2 = []
with open('data/processed/amazonhelp_labeled_conversations_v2.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        v2.append(json.loads(line))

v1_by_id = {l['conversation_id']: l for l in v1}
v2_by_id = {l['conversation_id']: l for l in v2}

all_changes = []
for conv_id in v1_by_id:
    if conv_id in v2_by_id:
        v1_intent = v1_by_id[conv_id]['primary_intent']
        v2_intent = v2_by_id[conv_id]['primary_intent']
        if v1_intent != v2_intent:
            customer_text = ' '.join(t.get('text', '') for t in v1_by_id[conv_id]['turns'] if t.get('speaker') == 'Customer')
            all_changes.append({
                'conversation_id': conv_id,
                'v1_intent': v1_intent,
                'v2_intent': v2_intent,
                'v1_confidence': v1_by_id[conv_id]['confidence'],
                'v2_confidence': v2_by_id[conv_id]['confidence'],
                'customer_text': customer_text[:500],
            })

print(f"Total changes: {len(all_changes)}")

# Create examples for each transition category
trans_examples = {}
for c in all_changes:
    key = f"{c['v1_intent']} -> {c['v2_intent']}"
    if key not in trans_examples:
        trans_examples[key] = []
    trans_examples[key].append(c)

# Take top 3 examples per transition
examples_output = {}
for key, convs in sorted(trans_examples.items(), key=lambda x: -len(x[1]))[:20]:
    examples_output[key] = convs[:3]

with open('data/samples/v1_v2_change_examples.json', 'w', encoding='utf-8') as f:
    json.dump(examples_output, f, indent=2, ensure_ascii=False)

print(f"Saved {len(examples_output)} transition categories with examples")

# PAYMENT_ISSUE -> OTHER examples
pi_other = [c for c in all_changes if c['v1_intent'] == 'PAYMENT_ISSUE' and c['v2_intent'] == 'OTHER']
print(f"\nPAYMENT_ISSUE -> OTHER: {len(pi_other)} cases")
for c in pi_other[:3]:
    print(f"  {c['conversation_id']}: {c['customer_text'][:200]}...")

# DELIVERY_MISSING -> OTHER examples
dm_other = [c for c in all_changes if c['v1_intent'] == 'DELIVERY_MISSING' and c['v2_intent'] == 'OTHER']
print(f"\nDELIVERY_MISSING -> OTHER: {len(dm_other)} cases")
for c in dm_other[:3]:
    print(f"  {c['conversation_id']}: {c['customer_text'][:200]}...")

# DELIVERY_LATE -> OTHER examples
dl_other = [c for c in all_changes if c['v1_intent'] == 'DELIVERY_LATE' and c['v2_intent'] == 'OTHER']
print(f"\nDELIVERY_LATE -> OTHER: {len(dl_other)} cases")
for c in dl_other[:3]:
    print(f"  {c['conversation_id']}: {c['customer_text'][:200]}...")