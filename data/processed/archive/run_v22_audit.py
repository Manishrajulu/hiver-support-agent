import json
from collections import Counter

# Load all versions
v1 = []
with open('data/processed/amazonhelp_labeled_conversations.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        v1.append(json.loads(line))

v2 = []
with open('data/processed/amazonhelp_labeled_conversations_v2.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        v2.append(json.loads(line))

v21 = []
with open('data/processed/amazonhelp_labeled_conversations_v21.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        v21.append(json.loads(line))

v22 = []
with open('data/processed/amazonhelp_labeled_conversations_v22.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        v22.append(json.loads(line))

v1_by_id = {l['conversation_id']: l for l in v1}
v2_by_id = {l['conversation_id']: l for l in v2}
v21_by_id = {l['conversation_id']: l for l in v21}
v22_by_id = {l['conversation_id']: l for l in v22}

print("="*70)
print("FOUR-WAY COMPARISON: V1 vs V2 vs V2.1 vs V2.2")
print("="*70)

# Primary intent comparison
v1_intents = Counter(l['primary_intent'] for l in v1)
v2_intents = Counter(l['primary_intent'] for l in v2)
v21_intents = Counter(l['primary_intent'] for l in v21)
v22_intents = Counter(l['primary_intent'] for l in v22)

all_intents = set(v1_intents.keys()) | set(v2_intents.keys()) | set(v21_intents.keys()) | set(v22_intents.keys())

print(f"\n{'Intent':<22} {'V1':>8} {'V2':>8} {'V2.1':>8} {'V2.2':>8}")
print("-"*60)

for intent in sorted(all_intents, key=lambda x: -v22_intents.get(x, 0)):
    v1_c = v1_intents.get(intent, 0)
    v2_c = v2_intents.get(intent, 0)
    v21_c = v21_intents.get(intent, 0)
    v22_c = v22_intents.get(intent, 0)
    print(f"{intent:<22} {v1_c:>8} {v2_c:>8} {v21_c:>8} {v22_c:>8}")

print("\n" + "="*70)
print("V2.1 -> V2.2 TRANSITION ANALYSIS")
print("="*70)

# Get V2.1 -> V2.2 changes
changes = []
for conv_id in v21_by_id:
    if conv_id in v22_by_id:
        v21_intent = v21_by_id[conv_id]['primary_intent']
        v22_intent = v22_by_id[conv_id]['primary_intent']
        if v21_intent != v22_intent:
            customer_text = ' '.join(t.get('text', '') for t in v1_by_id[conv_id]['turns'] if t.get('speaker') == 'Customer')
            changes.append({
                'conversation_id': conv_id,
                'v21_intent': v21_intent,
                'v22_intent': v22_intent,
                'customer_text': customer_text
            })

print(f"\nTotal V2.1 -> V2.2 changes: {len(changes)}")

# Transition matrix
trans = Counter((c['v21_intent'], c['v22_intent']) for c in changes)

print(f"\n{'V2.1 Intent':<22} {'-> V2.2 Intent':<22} {'Count':>8}")
print("-"*55)
for (v21_i, v22_i), count in trans.most_common():
    print(f"{v21_i:<22} -> {v22_i:<22} {count:>8}")

# ============================================
# FOCUSED AUDITS
# ============================================

print("\n" + "="*70)
print("A. PAYMENT_ISSUE CHANGES (V2.1 -> V2.2)")
print("="*70)

pi_changes = [c for c in changes if 'PAYMENT_ISSUE' in [c['v21_intent'], c['v22_intent']]]
print(f"\nPAYMENT_ISSUE related changes: {len(pi_changes)}")

pi_lost = [c for c in pi_changes if c['v21_intent'] == 'PAYMENT_ISSUE' and c['v22_intent'] != 'PAYMENT_ISSUE']
pi_gained = [c for c in pi_changes if c['v22_intent'] == 'PAYMENT_ISSUE' and c['v21_intent'] != 'PAYMENT_ISSUE']
print(f"  Lost from V2.1: {len(pi_lost)}")
print(f"  Gained to V2.2: {len(pi_gained)}")

# Where did lost PI go?
lost_to = Counter(c['v22_intent'] for c in pi_lost)
print(f"\n  Lost PAYMENT_ISSUE went to:")
for intent, count in lost_to.most_common():
    print(f"    {intent}: {count}")

print("\n  Examples of lost PAYMENT_ISSUE:")
for c in pi_lost[:3]:
    print(f"\n    {c['conversation_id']}: {c['v21_intent']} -> {c['v22_intent']}")
    print(f"    Text: {c['customer_text'][:200]}")

print("\n" + "="*70)
print("B. REFUND_REQUEST CHANGES (V2.1 -> V2.2)")
print("="*70)

ref_changes = [c for c in changes if 'REFUND_REQUEST' in [c['v21_intent'], c['v22_intent']]]
print(f"\nREFUND_REQUEST related changes: {len(ref_changes)}")

ref_lost = [c for c in ref_changes if c['v21_intent'] == 'REFUND_REQUEST' and c['v22_intent'] != 'REFUND_REQUEST']
ref_gained = [c for c in ref_changes if c['v22_intent'] == 'REFUND_REQUEST' and c['v21_intent'] != 'REFUND_REQUEST']
print(f"  Lost from V2.1: {len(ref_lost)}")
print(f"  Gained to V2.2: {len(ref_gained)}")

# Where did lost ref go?
ref_lost_to = Counter(c['v22_intent'] for c in ref_lost)
print(f"\n  Lost REFUND_REQUEST went to:")
for intent, count in ref_lost_to.most_common():
    print(f"    {intent}: {count}")

print("\n" + "="*70)
print("C. DELIVERY_LATE CHANGES (V2.1 -> V2.2)")
print("="*70)

dl_changes = [c for c in changes if 'DELIVERY_LATE' in [c['v21_intent'], c['v22_intent']]]
print(f"\nDELIVERY_LATE related changes: {len(dl_changes)}")

dl_lost = [c for c in dl_changes if c['v21_intent'] == 'DELIVERY_LATE' and c['v22_intent'] != 'DELIVERY_LATE']
dl_gained = [c for c in dl_changes if c['v22_intent'] == 'DELIVERY_LATE' and c['v21_intent'] != 'DELIVERY_LATE']
print(f"  Lost from V2.1: {len(dl_lost)}")
print(f"  Gained to V2.2: {len(dl_gained)}")

# Where did lost dl go?
dl_lost_to = Counter(c['v22_intent'] for c in dl_lost)
print(f"\n  Lost DELIVERY_LATE went to:")
for intent, count in dl_lost_to.most_common():
    print(f"    {intent}: {count}")

print("\n" + "="*70)
print("D. OTHER CHANGES (V2.1 -> V2.2)")
print("="*70)

other_changes = [c for c in changes if 'OTHER' in [c['v21_intent'], c['v22_intent']]]
print(f"\nOTHER-related changes: {len(other_changes)}")

other_to_intent = [c for c in other_changes if c['v21_intent'] == 'OTHER' and c['v22_intent'] != 'OTHER']
intent_to_other = [c for c in other_changes if c['v22_intent'] == 'OTHER' and c['v21_intent'] != 'OTHER']
print(f"  OTHER -> existing intent: {len(other_to_intent)}")
print(f"  existing intent -> OTHER: {len(intent_to_other)}")

# What intents recovered from OTHER?
recovered = Counter(c['v22_intent'] for c in other_to_intent)
print(f"\n  Recovered from V2.1 OTHER:")
for intent, count in recovered.most_common():
    print(f"    {intent}: {count}")

# What intents moved to OTHER?
lost = Counter(c['v21_intent'] for c in intent_to_other)
print(f"\n  Moved to V2.2 OTHER:")
for intent, count in lost.most_common():
    print(f"    {intent}: {count}")

print("\n" + "="*70)
print("E. DELIVERY_MISSING CHANGES (V2.1 -> V2.2)")
print("="*70)

dm_changes = [c for c in changes if 'DELIVERY_MISSING' in [c['v21_intent'], c['v22_intent']]]
print(f"\nDELIVERY_MISSING related changes: {len(dm_changes)}")

dm_lost = [c for c in dm_changes if c['v21_intent'] == 'DELIVERY_MISSING' and c['v22_intent'] != 'DELIVERY_MISSING']
dm_gained = [c for c in dm_changes if c['v22_intent'] == 'DELIVERY_MISSING' and c['v21_intent'] != 'DELIVERY_MISSING']
print(f"  Lost from V2.1: {len(dm_lost)}")
print(f"  Gained to V2.2: {len(dm_gained)}")

# Where did lost dm go?
dm_lost_to = Counter(c['v22_intent'] for c in dm_lost)
print(f"\n  Lost DELIVERY_MISSING went to:")
for intent, count in dm_lost_to.most_common():
    print(f"    {intent}: {count}")

# ============================================
# SUMMARY
# ============================================

print("\n" + "="*70)
print("SUMMARY")
print("="*70)

v22_conf = Counter(l['confidence'] for l in v22)
v21_conf = Counter(l['confidence'] for l in v21)

print(f"""
Four-way comparison key metrics:

Intent             V1      V2     V2.1    V2.2
-------------------------------------------------
OTHER             {v1_intents.get('OTHER',0):>4}    {v2_intents.get('OTHER',0):>4}   {v21_intents.get('OTHER',0):>5}   {v22_intents.get('OTHER',0):>5}
PAYMENT_ISSUE     {v1_intents.get('PAYMENT_ISSUE',0):>4}    {v2_intents.get('PAYMENT_ISSUE',0):>4}   {v21_intents.get('PAYMENT_ISSUE',0):>5}   {v22_intents.get('PAYMENT_ISSUE',0):>5}
REFUND_REQUEST    {v1_intents.get('REFUND_REQUEST',0):>4}    {v2_intents.get('REFUND_REQUEST',0):>4}   {v21_intents.get('REFUND_REQUEST',0):>5}   {v22_intents.get('REFUND_REQUEST',0):>5}
DELIVERY_LATE     {v1_intents.get('DELIVERY_LATE',0):>4}    {v2_intents.get('DELIVERY_LATE',0):>4}   {v21_intents.get('DELIVERY_LATE',0):>5}   {v22_intents.get('DELIVERY_LATE',0):>5}
DELIVERY_MISSING  {v1_intents.get('DELIVERY_MISSING',0):>4}    {v2_intents.get('DELIVERY_MISSING',0):>4}   {v21_intents.get('DELIVERY_MISSING',0):>5}   {v22_intents.get('DELIVERY_MISSING',0):>5}

V2.1 -> V2.2 changes: {len(changes)}

PROBLEM: V2.2 PAYMENT_ISSUE dropped to {v22_intents.get('PAYMENT_ISSUE',0)} from V2.1's {v21_intents.get('PAYMENT_ISSUE',0)}
         OTHER increased to {v22_intents.get('OTHER',0)} from V2.1's {v21_intents.get('OTHER',0)}
""")

# Save audit data
audit_data = {
    'total_v21_v22_changes': len(changes),
    'pi_lost': len(pi_lost),
    'pi_gained': len(pi_gained),
    'pi_lost_to': dict(lost_to),
    'ref_lost': len(ref_lost),
    'ref_gained': len(ref_gained),
    'ref_lost_to': dict(ref_lost_to),
    'dl_lost': len(dl_lost),
    'dl_gained': len(dl_gained),
    'dl_lost_to': dict(dl_lost_to),
    'dm_lost': len(dm_lost),
    'dm_gained': len(dm_gained),
    'dm_lost_to': dict(dm_lost_to),
    'other_recovered': len(other_to_intent),
    'other_lost': len(intent_to_other),
    'recovered_from_other': dict(recovered),
    'lost_to_other': dict(lost)
}

with open('data/samples/v22_audit_data.json', 'w', encoding='utf-8') as f:
    json.dump(audit_data, f, indent=2, ensure_ascii=False)

print("Audit data saved")