import json
from collections import Counter

# Load all three versions
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

v1_by_id = {l['conversation_id']: l for l in v1}
v2_by_id = {l['conversation_id']: l for l in v2}
v21_by_id = {l['conversation_id']: l for l in v21}

print("="*70)
print("THREE-WAY COMPARISON: V1 vs V2 vs V2.1")
print("="*70)

# Primary intent comparison
v1_intents = Counter(l['primary_intent'] for l in v1)
v2_intents = Counter(l['primary_intent'] for l in v2)
v21_intents = Counter(l['primary_intent'] for l in v21)

all_intents = set(v1_intents.keys()) | set(v2_intents.keys()) | set(v21_intents.keys())

print(f"\n{'Intent':<25} {'V1':>8} {'V2':>8} {'V2.1':>8} {'V1->V2':>10} {'V2->V2.1':>10}")
print("-"*75)

for intent in sorted(all_intents, key=lambda x: -v21_intents.get(x, 0)):
    v1_c = v1_intents.get(intent, 0)
    v2_c = v2_intents.get(intent, 0)
    v21_c = v21_intents.get(intent, 0)
    v1_v2 = v2_c - v1_c
    v2_v21 = v21_c - v2_c
    v1_v2_sign = '+' if v1_v2 > 0 else ''
    v2_v21_sign = '+' if v2_v21 > 0 else ''
    print(f"{intent:<25} {v1_c:>8} {v2_c:>8} {v21_c:>8} {v1_v2_sign}{v1_v2:>9} {v2_v21_sign}{v2_v21:>9}")

print("\n" + "="*70)
print("CONFIDENCE COMPARISON")
print("="*70)

v1_conf = Counter(l['confidence'] for l in v1)
v2_conf = Counter(l['confidence'] for l in v2)
v21_conf = Counter(l['confidence'] for l in v21)

print(f"\n{'Confidence':<15} {'V1':>10} {'V2':>10} {'V2.1':>10}")
print("-"*50)
for conf in ['HIGH', 'MEDIUM', 'LOW']:
    v1_c = v1_conf.get(conf, 0)
    v2_c = v2_conf.get(conf, 0)
    v21_c = v21_conf.get(conf, 0)
    print(f"{conf:<15} {v1_c:>10} {v2_c:>10} {v21_c:>10}")

print("\n" + "="*70)
print("LANGUAGE DISTRIBUTION")
print("="*70)

v1_lang = Counter(l['language'] for l in v1)
v2_lang = Counter(l['language'] for l in v2)
v21_lang = Counter(l['language'] for l in v21)

print(f"\n{'Language':<15} {'V1':>10} {'V2':>10} {'V2.1':>10}")
print("-"*50)
for lang in ['en', 'non_en', 'unknown']:
    v1_c = v1_lang.get(lang, 0)
    v2_c = v2_lang.get(lang, 0)
    v21_c = v21_lang.get(lang, 0)
    print(f"{lang:<15} {v1_c:>10} {v2_c:>10} {v21_c:>10}")

print("\n" + "="*70)
print("MULTI-INTENT RATE")
print("="*70)

v1_multi = sum(1 for l in v1 if len(l['secondary_intents']) > 0)
v2_multi = sum(1 for l in v2 if len(l['secondary_intents']) > 0)
v21_multi = sum(1 for l in v21 if len(l['secondary_intents']) > 0)

print(f"\nMulti-intent conversations:")
print(f"  V1:  {v1_multi} ({100*v1_multi/len(v1):.1f}%)")
print(f"  V2:  {v2_multi} ({100*v2_multi/len(v2):.1f}%)")
print(f"  V2.1: {v21_multi} ({100*v21_multi/len(v21):.1f}%)")

# ============================================
# AUDIT V2.1 CHANGES
# ============================================

print("\n" + "="*70)
print("V2.1 AUDIT: V2 -> V2.1 CHANGES")
print("="*70)

# Get V2 -> V2.1 changes
changes_v2_v21 = []
for conv_id in v2_by_id:
    if conv_id in v21_by_id:
        v2_intent = v2_by_id[conv_id]['primary_intent']
        v21_intent = v21_by_id[conv_id]['primary_intent']
        if v2_intent != v21_intent:
            changes_v2_v21.append({
                'conversation_id': conv_id,
                'v2_intent': v2_intent,
                'v21_intent': v21_intent,
                'customer_text': ' '.join(t.get('text', '') for t in v1_by_id[conv_id]['turns'] if t.get('speaker') == 'Customer')
            })

print(f"\nTotal V2 -> V2.1 changes: {len(changes_v2_v21)}")

# Transition matrix for V2 -> V2.1
v2_v21_trans = Counter((c['v2_intent'], c['v21_intent']) for c in changes_v2_v21)

print(f"\n{'V2 Intent':<25} {'-> V2.1 Intent':<25} {'Count':>8}")
print("-"*60)
for (v2_i, v21_i), count in v2_v21_trans.most_common():
    print(f"{v2_i:<25} -> {v21_i:<25} {count:>8}")

# ============================================
# FOCUSED AUDITS
# ============================================

print("\n" + "="*70)
print("A. PAYMENT_ISSUE CHANGES (V2 -> V2.1)")
print("="*70)

pi_changes = [c for c in changes_v2_v21 if c['v2_intent'] == 'PAYMENT_ISSUE' or c['v21_intent'] == 'PAYMENT_ISSUE']
print(f"\nPAYMENT_ISSUE related changes: {len(pi_changes)}")

pi_recovered = [c for c in pi_changes if c['v2_intent'] == 'OTHER' and c['v21_intent'] == 'PAYMENT_ISSUE']
pi_lost = [c for c in pi_changes if c['v2_intent'] == 'PAYMENT_ISSUE' and c['v21_intent'] == 'OTHER']
print(f"  Recovered from V2 OTHER: {len(pi_recovered)}")
print(f"  Lost from V2 PAYMENT_ISSUE: {len(pi_lost)}")

print("\nRepresentative recovered examples:")
for c in pi_recovered[:3]:
    print(f"  {c['conversation_id']}: {c['v2_intent']} -> {c['v21_intent']}")
    print(f"    Text: {c['customer_text'][:150]}...")

print("\nRepresentative lost examples:")
for c in pi_lost[:3]:
    print(f"  {c['conversation_id']}: {c['v2_intent']} -> {c['v21_intent']}")
    print(f"    Text: {c['customer_text'][:150]}...")

print("\n" + "="*70)
print("B. DELIVERY_MISSING CHANGES (V2 -> V2.1)")
print("="*70)

dm_changes = [c for c in changes_v2_v21 if c['v2_intent'] == 'DELIVERY_MISSING' or c['v21_intent'] == 'DELIVERY_MISSING']
print(f"\nDELIVERY_MISSING related changes: {len(dm_changes)}")

dm_recovered = [c for c in dm_changes if c['v2_intent'] == 'OTHER' and c['v21_intent'] == 'DELIVERY_MISSING']
dm_lost = [c for c in dm_changes if c['v2_intent'] == 'DELIVERY_MISSING' and c['v21_intent'] == 'OTHER']
print(f"  Recovered from V2 OTHER: {len(dm_recovered)}")
print(f"  Lost from V2 DELIVERY_MISSING: {len(dm_lost)}")

print("\nRepresentative recovered examples:")
for c in dm_recovered[:3]:
    print(f"  {c['conversation_id']}: {c['v2_intent']} -> {c['v21_intent']}")
    print(f"    Text: {c['customer_text'][:150]}...")

print("\n" + "="*70)
print("C. DELIVERY_LATE CHANGES (V2 -> V2.1)")
print("="*70)

dl_changes = [c for c in changes_v2_v21 if c['v2_intent'] == 'DELIVERY_LATE' or c['v21_intent'] == 'DELIVERY_LATE']
print(f"\nDELIVERY_LATE related changes: {len(dl_changes)}")

dl_recovered = [c for c in dl_changes if c['v2_intent'] == 'OTHER' and c['v21_intent'] == 'DELIVERY_LATE']
dl_lost = [c for c in dl_changes if c['v2_intent'] == 'DELIVERY_LATE' and c['v21_intent'] == 'OTHER']
dl_other = [c for c in dl_changes if c['v2_intent'] == 'DELIVERY_LATE' and c['v21_intent'] not in ['OTHER', 'DELIVERY_LATE']]
print(f"  Recovered from V2 OTHER: {len(dl_recovered)}")
print(f"  Lost from V2 DELIVERY_LATE to OTHER: {len(dl_lost)}")
print(f"  Changed to other intent: {len(dl_other)}")

print("\n" + "="*70)
print("D. OTHER CHANGES (V2 -> V2.1)")
print("="*70)

other_changes = [c for c in changes_v2_v21 if c['v21_intent'] == 'OTHER' or c['v2_intent'] == 'OTHER']
print(f"\nOTHER-related changes: {len(other_changes)}")

other_to_intent = [c for c in other_changes if c['v2_intent'] == 'OTHER' and c['v21_intent'] != 'OTHER']
intent_to_other = [c for c in other_changes if c['v21_intent'] == 'OTHER' and c['v2_intent'] != 'OTHER']
print(f"  OTHER -> existing intent: {len(other_to_intent)}")
print(f"  existing intent -> OTHER: {len(intent_to_other)}")

# What intents recovered from OTHER?
recovered_from = Counter(c['v21_intent'] for c in other_to_intent)
print("\n  Intents recovered from V2 OTHER:")
for intent, count in recovered_from.most_common():
    print(f"    {intent}: {count}")

# What intents moved to OTHER?
lost_to_other = Counter(c['v2_intent'] for c in intent_to_other)
print("\n  Intents that moved to V2.1 OTHER:")
for intent, count in lost_to_other.most_common():
    print(f"    {intent}: {count}")

# ============================================
# SUMMARY
# ============================================

print("\n" + "="*70)
print("SUMMARY")
print("="*70)

print(f"""
V1  -> V2  : {len([c for c in changes_v2_v21 if True])} changes (V1->V2 was 176)
V2  -> V2.1: {len(changes_v2_v21)} changes

Key Metrics:
  OTHER:      V1={v1_intents.get('OTHER',0)} -> V2={v2_intents.get('OTHER',0)} -> V2.1={v21_intents.get('OTHER',0)}
  PAYMENT_ISSUE: V1={v1_intents.get('PAYMENT_ISSUE',0)} -> V2={v2_intents.get('PAYMENT_ISSUE',0)} -> V2.1={v21_intents.get('PAYMENT_ISSUE',0)}
  DELIVERY_MISSING: V1={v1_intents.get('DELIVERY_MISSING',0)} -> V2={v2_intents.get('DELIVERY_MISSING',0)} -> V2.1={v21_intents.get('DELIVERY_MISSING',0)}
  DELIVERY_LATE: V1={v1_intents.get('DELIVERY_LATE',0)} -> V2={v2_intents.get('DELIVERY_LATE',0)} -> V2.1={v21_intents.get('DELIVERY_LATE',0)}

PAYMENT_ISSUE recovery from V2's OTHER: {len(pi_recovered)}
DELIVERY_MISSING recovery from V2's OTHER: {len(dm_recovered)}
OTHER recovered to existing intents: {len(other_to_intent)}
""")

# Save audit data
audit_data = {
    'v2_v21_total_changes': len(changes_v2_v21),
    'pi_recovered_from_v2_other': len(pi_recovered),
    'pi_lost_to_v2_other': len(pi_lost),
    'dm_recovered_from_v2_other': len(dm_recovered),
    'dm_lost_to_v2_other': len(dm_lost),
    'dl_recovered_from_v2_other': len(dl_recovered),
    'dl_lost_to_v2_other': len(dl_lost),
    'other_recovered_count': len(other_to_intent),
    'other_lost_count': len(intent_to_other),
    'recovered_intents': dict(recovered_from),
    'lost_intents': dict(lost_to_other)
}

with open('data/samples/v21_audit_data.json', 'w', encoding='utf-8') as f:
    json.dump(audit_data, f, indent=2, ensure_ascii=False)

print("Audit data saved to data/samples/v21_audit_data.json")