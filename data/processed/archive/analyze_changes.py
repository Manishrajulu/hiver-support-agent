import json
from collections import Counter, defaultdict

# Load V1 and V2
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

# Get all changes
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
                'customer_text': customer_text,
                'v1_language': v1_by_id[conv_id].get('language', 'unknown'),
            })

print(f"Total changes: {len(all_changes)}")

# Save full changes
with open('data/samples/v1_v2_all_changes_full.json', 'w', encoding='utf-8') as f:
    json.dump(all_changes, f, indent=2, ensure_ascii=False)

# Transition matrix
transitions = Counter()
for c in all_changes:
    transitions[(c['v1_intent'], c['v2_intent'])] += 1

# =====================
# PAYMENT_ISSUE ANALYSIS
# =====================
pi_removed = [c for c in all_changes if c['v1_intent'] == 'PAYMENT_ISSUE']
print(f"\nPAYMENT_ISSUE removed from V1: {len(pi_removed)}")

pi_analysis = []
for c in pi_removed:
    text = c['customer_text'].lower()
    v2_new = c['v2_intent']

    has_payment_kw = any(kw in text for kw in ['payment', 'pay', 'card', 'bank', 'charge', 'billing', 'transaction', 'amazon pay', 'cashback', 'promotional', 'gift card'])
    has_refund_kw = any(kw in text for kw in ['refund', 'money back', 'reimburse', 'return money'])
    has_app_kw = any(kw in text for kw in ['app', 'website', 'not working', 'login', 'access', 'page'])
    has_device_kw = any(kw in text for kw in ['device', 'kindle', 'echo', 'alexa', 'tablet', 'speaker'])

    if has_refund_kw and not has_payment_kw:
        assessment = 'B_V1_SHOULD_BE_REFUND'
    elif has_app_kw and not has_payment_kw:
        assessment = 'B_V1_SHOULD_BE_APP_USAGE'
    elif has_device_kw and not has_payment_kw:
        assessment = 'B_V1_SHOULD_BE_DEVICE'
    elif has_payment_kw and v2_new == 'OTHER':
        assessment = 'A_V2_INCORRECTLY_MOVED_TO_OTHER'
    elif has_payment_kw:
        assessment = 'C_AMBIGUOUS_MOVED_TO_' + v2_new
    else:
        assessment = 'C_AMBIGUOUS_GENERIC'

    pi_analysis.append({
        'conversation_id': c['conversation_id'],
        'v1_intent': c['v1_intent'],
        'v2_intent': v2_new,
        'customer_text': c['customer_text'][:200],
        'has_payment_kw': has_payment_kw,
        'has_refund_kw': has_refund_kw,
        'assessment': assessment
    })

pi_counts = Counter(a['assessment'] for a in pi_analysis)
print("\nPAYMENT_ISSUE Removal Assessment:")
for k, v in pi_counts.most_common():
    print(f"  {k}: {v} ({100*v/len(pi_removed):.1f}%)")

with open('data/samples/pi_removal_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(pi_analysis, f, indent=2, ensure_ascii=False)

# =====================
# DELIVERY_MISSING ANALYSIS
# =====================
dm_removed = [c for c in all_changes if c['v1_intent'] == 'DELIVERY_MISSING']
print(f"\nDELIVERY_MISSING removed from V1: {len(dm_removed)}")

dm_analysis = []
for c in dm_removed:
    text = c['customer_text'].lower()
    v2_new = c['v2_intent']

    has_missing_kw = any(kw in text for kw in ['missing', 'never received', 'never came', 'not received', 'did not arrive', 'lost', 'where is my', 'disappeared'])
    has_delivery_kw = any(kw in text for kw in ['delivery', 'delivery guy', 'courier', 'driver', 'package', 'parcel', 'shipment'])
    has_late_kw = any(kw in text for kw in ['late', 'delayed', 'delay', 'eta', 'waiting'])
    has_refund_kw = any(kw in text for kw in ['refund', 'money back'])

    if has_missing_kw and not has_late_kw:
        assessment = 'A_V2_INCORRECTLY_MOVED_FROM_DELIVERY_MISSING'
    elif has_missing_kw and has_late_kw:
        assessment = 'C_AMBIGUOUS_COULD_BE_LATE'
    elif has_refund_kw:
        assessment = 'B_V1_SHOULD_BE_REFUND'
    else:
        assessment = 'C_AMBIGUOUS_OTHER'

    dm_analysis.append({
        'conversation_id': c['conversation_id'],
        'v1_intent': c['v1_intent'],
        'v2_intent': v2_new,
        'customer_text': c['customer_text'][:200],
        'assessment': assessment
    })

dm_counts = Counter(a['assessment'] for a in dm_analysis)
print("\nDELIVERY_MISSING Removal Assessment:")
for k, v in dm_counts.most_common():
    print(f"  {k}: {v} ({100*v/len(dm_removed):.1f}%)")

with open('data/samples/dm_removal_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(dm_analysis, f, indent=2, ensure_ascii=False)

# =====================
# DELIVERY_LATE ANALYSIS
# =====================
dl_removed = [c for c in all_changes if c['v1_intent'] == 'DELIVERY_LATE']
print(f"\nDELIVERY_LATE removed from V1: {len(dl_removed)}")

dl_analysis = []
for c in dl_removed:
    text = c['customer_text'].lower()
    v2_new = c['v2_intent']

    has_waiting_generic = 'still waiting' in text or 'when will i get' in text or "haven't received" in text
    has_delivery_context = any(kw in text for kw in ['delivery', 'package', 'parcel', 'courier', 'driver', 'shipment', 'amazon logistics', 'amazon delivery'])
    has_refund_kw = any(kw in text for kw in ['refund', 'money back'])
    has_app_kw = any(kw in text for kw in ['app', 'website', 'not working'])
    has_device_kw = any(kw in text for kw in ['device', 'kindle', 'echo'])

    if has_waiting_generic and not has_delivery_context:
        assessment = 'A_V2_CORRECT_REQUIRES_DELIVERY_CONTEXT'
    elif v2_new == 'OTHER' and has_delivery_context:
        assessment = 'A_V2_INCORRECT_MOVED_TO_OTHER'
    elif v2_new == 'APP_USAGE' and has_app_kw:
        assessment = 'C_AMBIGUOUS_MAYBE_APP'
    elif v2_new == 'DEVICE_ISSUE' and has_device_kw:
        assessment = 'C_AMBIGUOUS_MAYBE_DEVICE'
    elif has_refund_kw:
        assessment = 'B_V1_SHOULD_BE_REFUND'
    else:
        assessment = 'C_AMBIGUOUS_OTHER'

    dl_analysis.append({
        'conversation_id': c['conversation_id'],
        'v1_intent': c['v1_intent'],
        'v2_intent': v2_new,
        'customer_text': c['customer_text'][:200],
        'assessment': assessment
    })

dl_counts = Counter(a['assessment'] for a in dl_analysis)
print("\nDELIVERY_LATE Removal Assessment:")
for k, v in dl_counts.most_common():
    print(f"  {k}: {v} ({100*v/len(dl_removed):.1f}%)")

with open('data/samples/dl_removal_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(dl_analysis, f, indent=2, ensure_ascii=False)

# =====================
# OTHER INCREASE ANALYSIS
# =====================
other_increased = [c for c in all_changes if c['v2_intent'] == 'OTHER']
print(f"\nOTHER increased by V2: {len(other_increased)}")

oi_analysis = []
for c in other_increased:
    text = c['customer_text'].lower()
    v1_old = c['v1_intent']

    if 'refund' in text or 'money back' in text:
        missed = 'REFUND_REQUEST'
    elif 'return' in text and ('item' in text or 'product' in text):
        missed = 'RETURN_REQUEST'
    elif 'deliver' in text or 'late' in text or 'package' in text:
        missed = 'DELIVERY_LATE'
    elif 'missing' in text or 'never received' in text:
        missed = 'DELIVERY_MISSING'
    elif 'track' in text:
        missed = 'DELIVERY_TRACKING'
    elif 'cancel' in text or 'change' in text:
        missed = 'ORDER_MODIFY'
    elif 'order status' in text or 'where is my order' in text:
        missed = 'ORDER_STATUS'
    elif 'payment' in text or 'pay' in text or 'charge' in text:
        missed = 'PAYMENT_ISSUE'
    elif 'login' in text or 'password' in text or 'locked' in text:
        missed = 'ACCOUNT_ACCESS'
    elif 'app' in text or 'website' in text:
        missed = 'APP_USAGE'
    elif 'video' in text or 'stream' in text:
        missed = 'VIDEO_STREAMING'
    elif 'kindle' in text or 'echo' in text or 'device' in text:
        missed = 'DEVICE_ISSUE'
    else:
        missed = 'GENUINELY_OTHER'

    oi_analysis.append({
        'conversation_id': c['conversation_id'],
        'v1_intent': v1_old,
        'v2_intent': 'OTHER',
        'customer_text': c['customer_text'][:200],
        'should_be': missed
    })

oi_counts = Counter(a['should_be'] for a in oi_analysis)
print("\nOTHER Increase - What V2 Missed:")
for k, v in oi_counts.most_common():
    print(f"  {k}: {v} ({100*v/len(other_increased):.1f}%)")

with open('data/samples/other_increase_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(oi_analysis, f, indent=2, ensure_ascii=False)

# =====================
# CONFIDENCE COMPARISON
# =====================
print("\n" + "="*60)
print("CONFIDENCE COMPARISON")
print("="*60)

v1_conf = Counter(l['confidence'] for l in v1)
v2_conf = Counter(l['confidence'] for l in v2)

print("\nV1 Confidence Distribution:")
for conf, count in v1_conf.most_common():
    print(f"  {conf}: {count} ({100*count/len(v1):.1f}%)")

print("\nV2 Confidence Distribution:")
for conf, count in v2_conf.most_common():
    print(f"  {conf}: {count} ({100*count/len(v2):.1f}%)")

print("\nConfidence changes:")
for conf in ['HIGH', 'MEDIUM', 'LOW']:
    v1_c = v1_conf.get(conf, 0)
    v2_c = v2_conf.get(conf, 0)
    print(f"  {conf}: {v1_c} -> {v2_c} ({v2_c - v1_c:+/d})")

# Save all analysis
analysis_summary = {
    'total_changes': len(all_changes),
    'pi_removed_count': len(pi_removed),
    'pi_removed_assessment': dict(pi_counts),
    'dm_removed_count': len(dm_removed),
    'dm_removed_assessment': dict(dm_counts),
    'dl_removed_count': len(dl_removed),
    'dl_removed_assessment': dict(dl_counts),
    'other_increase_count': len(other_increased),
    'other_increase_should_be': dict(oi_counts),
    'v1_confidence': dict(v1_conf),
    'v2_confidence': dict(v2_conf)
}

with open('data/samples/v1_v2_analysis_summary.json', 'w', encoding='utf-8') as f:
    json.dump(analysis_summary, f, indent=2, ensure_ascii=False)

print("\nAnalysis complete. Files saved.")