#!/usr/bin/env python3
"""Label Quality Audit Script"""

import json
import re
from collections import Counter, defaultdict
import random

random.seed(42)

# ============================================
# FIXED LANGUAGE DETECTION
# ============================================

def detect_language_fixed(text):
    """Fixed language detection - only marks non-English if clearly non-English script or words"""
    if not text:
        return "unknown"

    # Check for non-Latin scripts (Hindi, Arabic, Chinese, etc.)
    if re.search(r'[ऀ-ॿঀ-ৱੀ-੪઀-૪଀-ପୀ-୪த-ఇಀ-ನಒ-ಳം-ഹං-෴ก-๛]', text):
        return "non_en"

    # Check for Cyrillic (Russian)
    if re.search(r'[а-яА-ЯЁё]', text):
        return "non_en"

    # Check for Arabic script
    if re.search(r'[؀-ۿ]', text):
        return "non_en"

    # Check for Japanese/Korean
    if re.search(r'[぀-ヿ一-鿿]', text):
        return "non_en"

    # For Latin script text, check if it's clearly English
    clean_text = re.sub(r'@\w+', '', text)
    clean_text = re.sub(r'http\S+', '', clean_text)
    clean_text = re.sub(r'#\w+', '', clean_text)

    english_words = set([
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
        'may', 'might', 'must', 'shall', 'can', 'need', 'want', 'order', 'orders',
        'delivery', 'delivered', 'delivering', 'amazon', 'help', 'please', 'thanks',
        'thank', 'sorry', 'my', 'me', 'i', 'you', 'your', 'yours', 'we', 'our',
        'package', 'packages', 'item', 'items', 'product', 'price', 'account',
        'refund', 'return', 'returning', 'returned', 'payment', 'paying', 'paid',
        'shipping', 'shipped', 'ship', 'tracking', 'track', 'late', 'waiting',
        'cancel', 'cancelled', 'change', 'status', 'update', 'contact', 'service',
        'customer', 'support', 'issue', 'problem', 'resolved', 'response', 'received',
        'not', 'no', 'yes', 'but', 'if', 'or', 'when', 'what', 'where', 'how',
        'why', 'who', 'which', 'this', 'that', 'these', 'those'
    ])

    words = clean_text.lower().split()
    if len(words) == 0:
        return "unknown"

    english_word_count = sum(1 for w in words if w in english_words)
    english_ratio = english_word_count / len(words)

    if english_ratio > 0.15:
        return "en"

    # Check for common non-English single words (highly distinctive)
    very_non_english = [
        'quel', 'quelle', 'comme', 'avec', 'pour', 'sans', 'chez', 'elle', 'lui',
        'nous', 'vous', 'eux', 'cette', 'bien', 'fait', 'plus', 'sont', 'etaient',
        'hola', 'gracias', 'como', 'porque', 'puedo', 'quiero', 'tengo', 'esta',
        'muy', 'pero', 'para', 'con', 'sin', 'los', 'las', 'del', 'al', 'su', 'una',
        'hallo', 'danke', 'nicht', 'nur', 'oder', 'aber', 'auch', 'schon', 'wird',
        'sind', 'hier', 'wenn', 'haben', 'werden'
    ]

    non_english_word_count = sum(1 for w in words if w in very_non_english)
    if non_english_word_count >= 2:
        return "non_en"

    return "en"

# ============================================
# LOAD DATA
# ============================================

print("Loading labeled conversations...")
labeled = []
with open(r'C:\Users\DELL\Desktop\hiver\data\processed\amazonhelp_labeled_conversations.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        labeled.append(json.loads(line))

print(f"Loaded {len(labeled)} labeled conversations")

# ============================================
# ISSUE 1: LANGUAGE DETECTION AUDIT
# ============================================

print("\n" + "="*60)
print("ISSUE 1: LANGUAGE DETECTION AUDIT")
print("="*60)

for l in labeled:
    customer_text = ' '.join(t.get('text', '') for t in l['turns'] if t.get('speaker') == 'Customer')
    l['language_fixed'] = detect_language_fixed(customer_text)

old_lang_dist = Counter(l['language'] for l in labeled)
new_lang_dist = Counter(l['language_fixed'] for l in labeled)

print("\nOLD language distribution:")
for lang, count in old_lang_dist.most_common():
    print(f"  {lang}: {count} ({100*count/len(labeled):.1f}%)")

print("\nNEW language distribution:")
for lang, count in new_lang_dist.most_common():
    print(f"  {lang}: {count} ({100*count/len(labeled):.1f}%)")

language_audit = {
    "old_distribution": dict(old_lang_dist),
    "new_distribution": dict(new_lang_dist),
    "problem_identified": "Non-English regex patterns matched common English words: que, si, der, del, pour, est, etc.",
    "fix_applied": "Use non-Latin script detection + distinctive non-English word list instead of common word patterns",
    "new_en_count": new_lang_dist.get('en', 0),
    "new_non_en_count": new_lang_dist.get('non_en', 0),
    "new_unknown_count": new_lang_dist.get('unknown', 0)
}

with open(r'C:\Users\DELL\Desktop\hiver\data\processed\language_detection_audit.json', 'w', encoding='utf-8') as f:
    json.dump(language_audit, f, indent=2)

print("\nSaved language_detection_audit.json")

# ============================================
# ISSUE 2: DELIVERY_LATE AUDIT
# ============================================

print("\n" + "="*60)
print("ISSUE 2: DELIVERY_LATE AUDIT")
print("="*60)

delivery_late_convs = [l for l in labeled if l['primary_intent'] == 'DELIVERY_LATE']
print(f"\nTotal DELIVERY_LATE: {len(delivery_late_convs)}")

random.seed(42)
delivery_late_random = random.sample(delivery_late_convs, min(30, len(delivery_late_convs)))

delivery_late_low = [l for l in delivery_late_convs if l['confidence'] == 'LOW']
delivery_late_low_sample = random.sample(delivery_late_low, min(30, len(delivery_late_low)))

delivery_late_ambiguous = []
for l in delivery_late_convs:
    customer_text = ' '.join(t.get('text', '') for t in l['turns'] if t.get('speaker') == 'Customer').lower()
    has_waiting = 'waiting' in customer_text or 'wait' in customer_text
    has_delivery = 'delivery' in customer_text or 'package' in customer_text or 'order' in customer_text
    if has_waiting and not has_delivery:
        delivery_late_ambiguous.append(l)
delivery_late_ambiguous_sample = random.sample(delivery_late_ambiguous, min(30, len(delivery_late_ambiguous)))

def format_delivery_late_example(l):
    customer_texts = [t.get('text', '')[:150] for t in l['turns'] if t.get('speaker') == 'Customer']
    return {
        'conversation_id': l['conversation_id'],
        'primary_intent': l['primary_intent'],
        'secondary_intents': l['secondary_intents'],
        'confidence': l['confidence'],
        'customer_messages': customer_texts
    }

delivery_late_audit = {
    'total_delivery_late': len(delivery_late_convs),
    'random_30': [format_delivery_late_example(l) for l in delivery_late_random],
    'low_confidence_30': [format_delivery_late_example(l) for l in delivery_late_low_sample],
    'ambiguous_30': [format_delivery_late_example(l) for l in delivery_late_ambiguous_sample]
}

with open(r'C:\Users\DELL\Desktop\hiver\data\processed\delivery_late_audit.json', 'w', encoding='utf-8') as f:
    json.dump(delivery_late_audit, f, indent=2, ensure_ascii=False)

print("Saved delivery_late_audit.json")
print(f"Ambiguous (waiting without delivery/package): {len(delivery_late_ambiguous)}")

# ============================================
# ISSUE 3: OTHER AUDIT
# ============================================

print("\n" + "="*60)
print("ISSUE 3: OTHER AUDIT")
print("="*60)

other_convs = [l for l in labeled if l['primary_intent'] == 'OTHER']
print(f"\nTotal OTHER: {len(other_convs)}")

other_sample = random.sample(other_convs, min(100, len(other_convs)))

other_categories = {
    'genuinely_unclassifiable': [],
    'obvious_existing_intent_missed': [],
    'noise': [],
    'non_english': [],
    'insufficient_context': [],
    'rule_failure': []
}

obvious_missed_examples = []

for l in other_sample:
    customer_texts = [t.get('text', '') for t in l['turns'] if t.get('speaker') == 'Customer']
    customer_text = ' '.join(customer_texts).lower()
    lang = l.get('language_fixed', detect_language_fixed(customer_text))

    if lang == 'non_en':
        other_categories['non_english'].append(l['conversation_id'])
        continue

    if len(customer_text) < 30:
        other_categories['insufficient_context'].append(l['conversation_id'])
        continue

    noise_patterns = ['thank', 'thanks', 'please help', 'please', 'sorry']
    if any(p in customer_text for p in noise_patterns) and len(customer_text) < 50:
        other_categories['noise'].append(l['conversation_id'])
        continue

    missed_intent = None
    if 'refund' in customer_text or 'money back' in customer_text or 'reimburse' in customer_text:
        missed_intent = 'REFUND_REQUEST'
    elif 'return' in customer_text and ('item' in customer_text or 'product' in customer_text or 'order' in customer_text):
        missed_intent = 'RETURN_REQUEST'
    elif 'deliver' in customer_text or 'late' in customer_text or 'package' in customer_text or 'shipping' in customer_text:
        missed_intent = 'DELIVERY_LATE'
    elif 'track' in customer_text or 'tracking' in customer_text:
        missed_intent = 'DELIVERY_TRACKING'
    elif 'cancel' in customer_text or 'change' in customer_text or 'modify' in customer_text:
        missed_intent = 'ORDER_MODIFY'
    elif 'order status' in customer_text or 'where is my order' in customer_text:
        missed_intent = 'ORDER_STATUS'
    elif 'login' in customer_text or 'password' in customer_text or 'locked' in customer_text:
        missed_intent = 'ACCOUNT_ACCESS'
    elif 'app' in customer_text or 'website' in customer_text or 'not working' in customer_text:
        missed_intent = 'APP_USAGE'
    elif 'video' in customer_text or 'stream' in customer_text or 'watch' in customer_text:
        missed_intent = 'VIDEO_STREAMING'
    elif 'kindle' in customer_text or 'echo' in customer_text or 'alexa' in customer_text or 'device' in customer_text:
        missed_intent = 'DEVICE_ISSUE'

    if missed_intent:
        other_categories['obvious_existing_intent_missed'].append({
            'conversation_id': l['conversation_id'],
            'missed_intent': missed_intent,
            'customer_text': customer_text[:200]
        })
        obvious_missed_examples.append({
            'conversation_id': l['conversation_id'],
            'primary_intent': l['primary_intent'],
            'should_be': missed_intent,
            'customer_text': customer_text[:200]
        })
    else:
        other_categories['genuinely_unclassifiable'].append(l['conversation_id'])

other_audit = {
    'total_other': len(other_convs),
    'sample_size': len(other_sample),
    'categories': {k: len(v) for k, v in other_categories.items()},
    'percentages': {k: round(100*len(v)/len(other_sample), 1) for k, v in other_categories.items()},
    'obvious_missed_top_20': obvious_missed_examples[:20]
}

with open(r'C:\Users\DELL\Desktop\hiver\data\processed\other_audit.json', 'w', encoding='utf-8') as f:
    json.dump(other_audit, f, indent=2, ensure_ascii=False)

print("Saved other_audit.json")

print(f"\nOTHER Breakdown (from {len(other_sample)} sample):")
for cat, convs in other_categories.items():
    print(f"  {cat}: {len(convs)} ({100*len(convs)/len(other_sample):.1f}%)")

# ============================================
# ISSUE 4: LOW CONFIDENCE AUDIT
# ============================================

print("\n" + "="*60)
print("ISSUE 4: LOW CONFIDENCE AUDIT")
print("="*60)

low_conf = [l for l in labeled if l['confidence'] == 'LOW']
print(f"\nTotal LOW confidence: {len(low_conf)}")

low_conf_sample = random.sample(low_conf, min(100, len(low_conf)))

low_conf_categories = {
    'genuinely_ambiguous': [],
    'insufficient_text': [],
    'conflicting_intents': [],
    'weak_evidence': [],
    'noise': [],
    'rule_issue': []
}

for l in low_conf_sample:
    customer_texts = [t.get('text', '') for t in l['turns'] if t.get('speaker') == 'Customer']
    customer_text = ' '.join(customer_texts)
    secondary = l.get('secondary_intents', [])

    if len(customer_text) < 40:
        low_conf_categories['insufficient_text'].append(l['conversation_id'])
    elif len(secondary) >= 2:
        low_conf_categories['conflicting_intents'].append(l['conversation_id'])
    elif l['primary_intent'] == 'OTHER':
        low_conf_categories['weak_evidence'].append(l['conversation_id'])
    else:
        low_conf_categories['genuinely_ambiguous'].append(l['conversation_id'])

low_conf_audit = {
    'total_low_confidence': len(low_conf),
    'sample_size': len(low_conf_sample),
    'categories': {k: len(v) for k, v in low_conf_categories.items()},
    'percentages': {k: round(100*len(v)/len(low_conf_sample), 1) for k, v in low_conf_categories.items()}
}

with open(r'C:\Users\DELL\Desktop\hiver\data\processed\low_confidence_audit.json', 'w', encoding='utf-8') as f:
    json.dump(low_conf_audit, f, indent=2)

print("Saved low_confidence_audit.json")

print(f"\nLOW Confidence Breakdown (from {len(low_conf_sample)} sample):")
for cat, convs in low_conf_categories.items():
    print(f"  {cat}: {len(convs)} ({100*len(convs)/len(low_conf_sample):.1f}%)")

# ============================================
# ISSUE 5: INTENT DISTRIBUTION CHECK
# ============================================

print("\n" + "="*60)
print("ISSUE 5: INTENT DISTRIBUTION SANITY CHECK")
print("="*60)

intent_dist = Counter(l['primary_intent'] for l in labeled)
print("\nIntent Distribution:")
for intent, count in intent_dist.most_common():
    pct = 100 * count / len(labeled)
    flag = ""
    if intent == 'OTHER' and pct > 30:
        flag = " [HIGH - check rules]"
    elif intent == 'DELIVERY_LATE' and pct > 20:
        flag = " [HIGH - check false positives]"
    elif count < 20:
        flag = " [LOW - may need attention]"
    print(f"  {intent}: {count} ({pct:.1f}%){flag}")

print("\nIntent Collision Analysis:")
late_with_missing_secondary = sum(1 for l in labeled if l['primary_intent'] == 'DELIVERY_LATE' and 'DELIVERY_MISSING' in l.get('secondary_intents', []))
print(f"  DELIVERY_LATE with DELIVERY_MISSING secondary: {late_with_missing_secondary}")

refund_with_payment_secondary = sum(1 for l in labeled if l['primary_intent'] == 'REFUND_REQUEST' and 'PAYMENT_ISSUE' in l.get('secondary_intents', []))
print(f"  REFUND_REQUEST with PAYMENT_ISSUE secondary: {refund_with_payment_secondary}")

return_with_product_secondary = sum(1 for l in labeled if l['primary_intent'] == 'RETURN_REQUEST' and 'PRODUCT_ISSUE' in l.get('secondary_intents', []))
print(f"  RETURN_REQUEST with PRODUCT_ISSUE secondary: {return_with_product_secondary}")

# ============================================
# CREATE SAMPLES FILE
# ============================================

print("\n" + "="*60)
print("CREATING QUALITY AUDIT SAMPLES")
print("="*60)

all_examples = {
    'delivery_late_random_10': [format_delivery_late_example(l) for l in delivery_late_random[:10]],
    'delivery_late_low_10': [format_delivery_late_example(l) for l in delivery_late_low_sample[:10]],
    'delivery_late_ambiguous_10': [format_delivery_late_example(l) for l in delivery_late_ambiguous_sample[:10]],
    'other_20_missed': obvious_missed_examples[:20],
    'low_confidence_20': [
        {
            'conversation_id': l['conversation_id'],
            'primary_intent': l['primary_intent'],
            'secondary_intents': l['secondary_intents'],
            'confidence': l['confidence'],
            'customer_text': ' '.join(t.get('text', '')[:100] for t in l['turns'] if t.get('speaker') == 'Customer')
        }
        for l in low_conf_sample[:20]
    ]
}

with open(r'C:\Users\DELL\Desktop\hiver\data\samples\label_quality_audit_examples.json', 'w', encoding='utf-8') as f:
    json.dump(all_examples, f, indent=2, ensure_ascii=False)

print("Saved label_quality_audit_examples.json")

print("\n" + "="*60)
print("AUDIT COMPLETE")
print("="*60)