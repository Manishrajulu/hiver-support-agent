#!/usr/bin/env python3
"""
Phase E: Apply Taxonomy Changes
"""
import json
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("PHASE E: APPLYING TAXONOMY CHANGES")
print("=" * 60)

# Load Phase C experimental dataset
exp_path = "data/baseline/phaseC_experimental.jsonl"
data = []
with open(exp_path, 'r', encoding='utf-8') as f:
    for line in f:
        data.append(json.loads(line.strip()))
print(f"\nLoaded {len(data)} examples from Phase C dataset")

data_lookup = {item['conversation_id']: item for item in data}

# =============================================================================
# STEP 1: Apply 3 MEDIUM-CONFIDENCE corrections from Phase B
# =============================================================================
print("\n[1] Applying 3 MEDIUM-CONFIDENCE corrections...")

medium_corrections = {
    "amazonhelp_018062": ("DELIVERY_MISSING", "DELIVERY_LATE"),
    "amazonhelp_034718": ("APP_USAGE", "PRODUCT_ISSUE"),
    "amazonhelp_148628": ("DEVICE_ISSUE", "PAYMENT_ISSUE"),
}

medium_applied = []
for cid, (old_label, new_label) in medium_corrections.items():
    if cid in data_lookup:
        item = data_lookup[cid]
        current = item.get('primary_intent')
        if current == old_label:
            item['primary_intent'] = new_label
            medium_applied.append((cid, old_label, new_label))
            print(f"  {cid}: {old_label} -> {new_label}")
        else:
            print(f"  WARNING: {cid} has {current}, expected {old_label}")
    else:
        print(f"  WARNING: {cid} not found in dataset")

print(f"\n  Applied {len(medium_applied)} MEDIUM corrections")

# =============================================================================
# STEP 2: DELIVERY_LATE vs DELIVERY_MISSING boundary
# =============================================================================
print("\n[2] Analyzing DELIVERY_LATE vs DELIVERY_MISSING boundary...")

# Find DELIVERY_LATE that should be DELIVERY_MISSING (never arrived)
late_to_missing = []
for item in data:
    cid = item['conversation_id']
    intent = item.get('primary_intent')
    text = ' '.join([t.get('text', '') for t in item.get('turns', []) if t.get('speaker') == 'Customer']).lower()

    if intent == 'DELIVERY_LATE':
        if any(kw in text for kw in ['never arrived', 'never got', 'not received', 'missing', 'disappeared']):
            late_to_missing.append((cid, intent, 'DELIVERY_MISSING', text[:100]))

# Find DELIVERY_MISSING that should be DELIVERY_LATE (supposed to deliver)
missing_to_late = []
for item in data:
    cid = item['conversation_id']
    intent = item.get('primary_intent')
    text = ' '.join([t.get('text', '') for t in item.get('turns', []) if t.get('speaker') == 'Customer']).lower()

    if intent == 'DELIVERY_MISSING':
        if any(kw in text for kw in ['supposed to deliver', 'expected', 'should have arrived', 'not yet arrived', 'hasn\'t arrived']):
            missing_to_late.append((cid, intent, 'DELIVERY_LATE', text[:100]))

print(f"\n  DELIVERY_LATE -> DELIVERY_MISSING ({len(late_to_missing)}):")
for cid, old, new, text in late_to_missing[:5]:
    print(f"    {cid}: {old} -> {new}: {text}...")

print(f"\n  DELIVERY_MISSING -> DELIVERY_LATE ({len(missing_to_late)}):")
for cid, old, new, text in missing_to_late[:5]:
    print(f"    {cid}: {old} -> {new}: {text}...")

boundary_applied = []
for cid, old, new, text in late_to_missing:
    if cid in data_lookup and data_lookup[cid].get('primary_intent') == old:
        data_lookup[cid]['primary_intent'] = new
        boundary_applied.append((cid, old, new))

for cid, old, new, text in missing_to_late:
    if cid in data_lookup and data_lookup[cid].get('primary_intent') == old:
        data_lookup[cid]['primary_intent'] = new
        boundary_applied.append((cid, old, new))

print(f"\n  Applied {len(boundary_applied)} boundary corrections")

# =============================================================================
# STEP 3: ORDER_STATUS vs DELIVERY boundary
# =============================================================================
print("\n[3] Analyzing ORDER_STATUS vs DELIVERY boundary...")

order_delivery_issues = []
for item in data:
    cid = item['conversation_id']
    intent = item.get('primary_intent')
    text = ' '.join([t.get('text', '') for t in item.get('turns', []) if t.get('speaker') == 'Customer']).lower()

    if intent == 'ORDER_STATUS':
        if any(kw in text for kw in ['not deliver', 'late deliver', 'never deliver', 'didn\'t deliver', 'hasn\'t delivered']):
            if 'deliver' in text or 'delivery' in text:
                order_delivery_issues.append((cid, intent, text[:100]))

print(f"\n  Found {len(order_delivery_issues)} ORDER_STATUS with delivery issues:")
for cid, intent, text in order_delivery_issues[:5]:
    print(f"    {cid}: {intent}: {text}...")

order_delivery_applied = []
for cid, intent, text in order_delivery_issues:
    if cid in data_lookup and data_lookup[cid].get('primary_intent') == 'ORDER_STATUS':
        if 'never' in text or 'not received' in text or 'missing' in text:
            new_intent = 'DELIVERY_MISSING'
        else:
            new_intent = 'DELIVERY_LATE'
        data_lookup[cid]['primary_intent'] = new_intent
        order_delivery_applied.append((cid, intent, new_intent))

print(f"\n  Applied {len(order_delivery_applied)} ORDER_STATUS -> DELIVERY corrections")

# =============================================================================
# STEP 4: APP_USAGE vs DEVICE_ISSUE boundary
# =============================================================================
print("\n[4] Analyzing APP_USAGE vs DEVICE_ISSUE boundary...")

app_device_issues = []
for item in data:
    cid = item['conversation_id']
    intent = item.get('primary_intent')
    text = ' '.join([t.get('text', '') for t in item.get('turns', []) if t.get('speaker') == 'Customer']).lower()

    if intent == 'DEVICE_ISSUE':
        if 'spotify' in text or ('echo' in text and 'account' in text):
            if 'kindle' not in text and 'tablet' not in text and 'fire' not in text and 'device' not in text:
                app_device_issues.append((cid, intent, 'APP_USAGE', text[:100]))

print(f"\n  Found {len(app_device_issues)} DEVICE_ISSUE that may be APP_USAGE:")
for cid, old, new, text in app_device_issues[:5]:
    print(f"    {cid}: {old} -> {new}: {text}...")

app_device_applied = []
for cid, old, new, text in app_device_issues:
    if cid in data_lookup and data_lookup[cid].get('primary_intent') == old:
        data_lookup[cid]['primary_intent'] = new
        app_device_applied.append((cid, old, new))

print(f"\n  Applied {len(app_device_applied)} APP_USAGE/DEVICE_ISSUE corrections")

# =============================================================================
# SUMMARY
# =============================================================================
print("\n" + "=" * 60)
print("SUMMARY OF PHASE E TAXONOMY CHANGES")
print("=" * 60)

all_changes = []
all_changes.extend(medium_applied)
all_changes.extend(boundary_applied)
all_changes.extend(order_delivery_applied)
all_changes.extend(app_device_applied)

changes_by_cid = {}
for cid, old, new in all_changes:
    changes_by_cid[cid] = (old, new)

print(f"\nTotal unique examples changed: {len(changes_by_cid)}")

original_counts = {}
for cid, (old, new) in changes_by_cid.items():
    original_counts[old] = original_counts.get(old, 0) + 1

print("\nChanges by original label:")
for label, count in sorted(original_counts.items(), key=lambda x: -x[1]):
    print(f"  {label}: {count}")

print("\nAll changes applied:")
for cid, (old, new) in changes_by_cid.items():
    print(f"  {cid}: {old} -> {new}")

# =============================================================================
# SAVE PHASE E DATASET
# =============================================================================
print("\n" + "=" * 60)
print("SAVING PHASE E DATASET")
print("=" * 60)

os.makedirs("data/cleaned", exist_ok=True)

phaseE_path = "data/cleaned/phaseE_taxonomy_cleaned.jsonl"
with open(phaseE_path, 'w', encoding='utf-8') as f:
    for item in data:
        f.write(json.dumps(item, ensure_ascii=False) + '\n')

print(f"\nSaved Phase E dataset to: {phaseE_path}")

with open(phaseE_path, 'r', encoding='utf-8') as f:
    verify_count = sum(1 for _ in f)
print(f"Verified: {verify_count} examples saved")

change_log = {
    'medium_confidence_corrections': medium_applied,
    'boundary_corrections': boundary_applied,
    'order_delivery_corrections': order_delivery_applied,
    'app_device_corrections': app_device_applied,
    'all_changes': [(cid, old, new) for cid, (old, new) in changes_by_cid.items()]
}
with open("data/cleaned/phaseE_change_log.json", 'w') as f:
    json.dump(change_log, f, indent=2)
print(f"Saved change log to: data/cleaned/phaseE_change_log.json")