#!/usr/bin/env python3
"""Corrected deterministic rule-based labeling pipeline for AmazonHelp taxonomy v1.0

V2.2 (final) - balanced approach:
1. Keep PAYMENT_CONTEXT with "charged" for legitimate payment issues
2. Prioritize explicit REFUND_REQUEST only when refund is clearly requested
3. Balance DELIVERY_LATE vs DELIVERY_MISSING using explicit language

DO NOT modify taxonomy v1.0
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
import random

PRIMARY_INTENTS = [
    "DELIVERY_MISSING", "DELIVERY_LATE", "DELIVERY_TRACKING",
    "ORDER_STATUS", "ORDER_MODIFY",
    "PRODUCT_ISSUE", "RETURN_REQUEST",
    "REFUND_REQUEST", "PAYMENT_ISSUE",
    "ACCOUNT_ACCESS",
    "APP_USAGE", "DEVICE_ISSUE", "VIDEO_STREAMING",
    "OTHER"
]

MODIFIERS = ["PRIME_CUSTOMER", "MARKETPLACE", "DELIVERY_CARRIER", "SUBSCRIPTION"]
ESCALATION_SIGNALS = ["FRUSTRATION_HIGH", "PREVIOUS_CONTACT", "SERVICE_COMPLAINT", "ESCALATION_REQUEST"]

def detect_language(text):
    if not text:
        return "unknown"
    if re.search(r'[ऀ-ॿঀ-ৱੀ-੪઀-૪଀-ପୀ-୪த-ఇಀ-ನಒ-ಳം-ഹං-෴ก-๛]', text):
        return "non_en"
    if re.search(r'[а-яА-ЯЁё]', text):
        return "non_en"
    if re.search(r'[؀-ۿ]', text):
        return "non_en"
    if re.search(r'[぀-ヿ一-鿿]', text):
        return "non_en"
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

DELIVERY_CONTEXT = [
    'package', 'packages', 'parcel', 'order', 'orders', 'delivery', 'delivered',
    'shipping', 'shipped', 'shipment', 'courier', 'driver', 'carrier',
    'tracking', 'track', 'arrival', 'arrive', 'expected', 'eta'
]

PAYMENT_CONTEXT = [
    'payment', 'pay', 'billing', 'credit card', 'debit card', 'gift card',
    'bank', 'transaction', 'card payment', 'online payment',
    'payment method', 'payment failed', 'payment declined', 'payment issue',
    'payment not working', 'payment refused', 'card declined', 'card rejected',
    'card not working', 'bank issues', 'bank problem',
    'amazon pay', 'pay balance', 'pay account',
    'charged', 'charged incorrectly', 'wrong charge', 'overcharged',
    'charged twice', 'duplicate charge', 'extra charge', 'unauthorized charge',
    'wrong amount', 'unexpected charge'
]

REFUND_CONTEXT = ['refund', 'money back', 'reimburse']
ORDER_CONTEXT = ['order', 'orders', 'order number', 'order id']

def has_delivery_context(text):
    text_lower = text.lower()
    return any(ctx in text_lower for ctx in DELIVERY_CONTEXT)

def has_refund_context(text):
    text_lower = text.lower()
    return any(ctx in text_lower for ctx in REFUND_CONTEXT)

def has_payment_context(text):
    text_lower = text.lower()
    return any(ctx in text_lower for ctx in PAYMENT_CONTEXT)

def has_order_context(text):
    text_lower = text.lower()
    return any(ctx in text_lower for ctx in ORDER_CONTEXT)

INTENT_PATTERNS = {
    "DELIVERY_MISSING": [
        "not delivered", "never received", "never got", "didnt get", "didn't get",
        "havent received", "haven't received", "never arrived", "not receive",
        "show as delivered but", "shows delivered but", "says delivered but",
        "package not received", "order not received", "nothing arrived",
        "empty box", "box was empty",
        "where is my package", "where is my order", "where is my parcel",
        "lost package", "lost order", "my package is missing", "my order is missing",
        "parcel is missing", "tracking shows delivered but i don't have",
        "tracking says delivered but", "delivered but i didnt get",
        "delivered but nothing", "delivered but not received",
        "was delivered but i", "should have been delivered",
        "missing item", "items missing"
    ],

    "DELIVERY_LATE": [
        "late", "delayed", "delay", "eta", "expected delivery", "promise",
        "days late", "taking too long", "still not here", "hasnt arrived", "hasn't arrived",
        "supposed to arrive", "was supposed to", "promised delivery", "delivery is late",
        "package is late", "order is late", "arriving today", "delivery is delayed",
        "is delayed", "running late", "behind schedule",
        "when will i get my order", "when will i get my package", "when will i get my parcel",
        "when is my order coming", "when will my order arrive", "when will my package arrive"
    ],

    "DELIVERY_TRACKING": [
        "tracking", "track my package", "track my order", "tracking number",
        "track order", "where is my package", "package tracking", "can't track",
        "tracking info", "tracking status", "track it", "track package"
    ],

    "ORDER_MODIFY": [
        "cancel order", "change order", "modify order", "edit order", "cancel my order",
        "want to cancel", "need to cancel", "please cancel", "cancellation",
        "change my order", "modify my order", "stop order", "delete order"
    ],

    "ORDER_STATUS": [
        "order status", "where is my order", "when will my order", "order number",
        "order id", "check my order", "order details", "status of my order",
        "any update on my order", "update on order", "order update", "my order",
        "order shipped yet", "has my order shipped"
    ],

    "PRODUCT_ISSUE": [
        "wrong item", "damaged", "defective", "not as described", "broken",
        "quality issue", "product damaged", "received damaged", "item damaged",
        "poor quality", "faulty", "not what i ordered", "different item",
        "counterfeit", "fake", "looks like", "looks used", "used condition"
    ],

    "RETURN_REQUEST": [
        "return", "exchange", "replacement", "pick up", "return label", "return item",
        "want to return", "need to return", "return it", "send back", "get a replacement",
        "get it exchanged", "return this", "return my", "returning", "return order",
        "return policy", "return process"
    ],

    "REFUND_REQUEST": [
        "want a refund", "need a refund", "please refund", "refund me",
        "refund my money", "get my money back", "give me my money back",
        "where is my refund", "when will i get my refund", "refund pending",
        "refund not received", "no refund yet", "still waiting for refund",
        "haven't received my refund", "haven't got my refund",
        "i want refund", "i need refund", "please give me refund",
        "request a refund", "requested a refund"
    ],

    "PAYMENT_ISSUE": [
        "payment failed", "payment declined", "payment not working", "payment issue",
        "payment method", "card payment", "online payment", "payment processing",
        "payment refused",
        "card declined", "card rejected", "card not working", "card failed",
        "credit card", "debit card",
        "billing", "wrong charge", "overcharged", "charged incorrectly",
        "duplicate charge", "extra charge", "unauthorized charge", "unexpected charge",
        "charged twice", "wrong amount",
        "bank issues", "bank problem", "payment transaction",
        "amazon pay", "pay balance", "pay account",
        "charged", "took money", "money taken"
    ],

    "ACCOUNT_ACCESS": [
        "login", "password", "locked", "access", "account suspended", "sign in", "log in",
        "cant login", "can't login", "cant sign in", "can't sign in", "forgot password",
        "reset password", "account locked", "locked out", "signin", "logging in"
    ],

    "APP_USAGE": [
        "app", "website", "not working", "error", "page not", "load", "loading",
        "app not working", "website not working", "site not working", "can't use",
        "cant use", "application", "mobile app", "amazon app", "the app"
    ],

    "DEVICE_ISSUE": [
        "kindle", "fire tv", "firetv", "echo", "alexa", "tablet", "device",
        "amazon device", "e-reader", "fire tablet", "show", "dot", "tap"
    ],

    "VIDEO_STREAMING": [
        "video", "streaming", "prime video", "subtitle", "playback", "watch",
        "movie", "netflix", "stream", "videos not playing", "video playback",
        "prime video not working", "can't watch", "cant watch"
    ]
}

MODIFIER_PATTERNS = {
    "PRIME_CUSTOMER": [
        "prime member", "prime customer", "prime benefits", "prime subscription",
        "prime order", "prime delivery", "prime shipping", "as a prime",
        "im prime", "i'm prime", "prime account", "amazon prime"
    ],
    "MARKETPLACE": [
        "marketplace", "third party", "3rd party", "seller", "fulfilled by",
        "sold by", "vendor", "not amazon", "external seller"
    ],
    "DELIVERY_CARRIER": [
        "gati", "dtdc", "fedex", "ups", "usps", "bluedart", "delhivery",
        "courier", "carrier", "delivery partner", "shipping partner", "ontrac",
        "lasership", "amazon logistics", "amzl"
    ],
    "SUBSCRIPTION": [
        "subscription", "subscribe", "audible", "kindle unlimited", "amazon fresh",
        "prime video subscription", "prime membership", "prime now"
    ]
}

ESCALATION_PATTERNS = {
    "FRUSTRATION_HIGH": [
        "angry", "furious", "frustrated", "awful", "terrible", "worst", "pathetic",
        "disgusting", "ridiculous", "unacceptable", "outraged", "fuming", "livid"
    ],
    "PREVIOUS_CONTACT": [
        "already contacted", "already called", "spoken to", "tried calling",
        "multiple times", "several times", "days ago", "weeks ago", "last week",
        "contacted you before", "no response from", "still waiting", "been waiting"
    ],
    "SERVICE_COMPLAINT": [
        "worst service", "bad service", "poor service", "rude", "no response",
        "bad experience", "terrible experience", "horrible experience", "no help",
        "unhelpful", "incompetent", "lazy", "no one helped", "transferring", "transferred"
    ],
    "ESCALATION_REQUEST": [
        "manager", "supervisor", "escalate", "call me back", "callback",
        "speak to someone", "someone higher", "higher authority", "boss",
        "executive", "lead", "senior", "urgent", "immediately"
    ]
}

def normalize_text(text):
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'http\S+|www\.\S+', '', text)
    text = re.sub(r'^@\w+\s+', '', text)
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'#\w+', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def get_customer_text(conv):
    customer_turns = [t for t in conv.get('turns', []) if t.get('speaker') == 'Customer']
    return ' '.join(t.get('text', '') for t in customer_turns)

def get_all_text(conv):
    return ' '.join(t.get('text', '') for t in conv.get('turns', []))

def match_intent(text, patterns):
    normalized = normalize_text(text)
    for pattern in patterns:
        if pattern in normalized:
            return True
    return False

def count_matches(text, patterns):
    normalized = normalize_text(text)
    count = 0
    for pattern in patterns:
        if pattern in normalized:
            count += 1
    return count

def determine_primary_intent(customer_text, all_text):
    """Determine primary intent - balanced approach"""

    normalized = normalize_text(customer_text)
    has_delivery_ctx = has_delivery_context(customer_text)
    has_order_ctx = has_order_context(customer_text)
    has_refund_ctx = has_refund_context(customer_text)
    has_payment_ctx = has_payment_context(customer_text)

    scores = {}
    for intent, patterns in INTENT_PATTERNS.items():
        scores[intent] = count_matches(customer_text, patterns)

    if all(v == 0 for v in scores.values()):
        return "OTHER"

    # ===========================================
    # REFUND_REQUEST - priority for explicit requests
    # ===========================================
    refund_score = scores.get("REFUND_REQUEST", 0)
    payment_score = scores.get("PAYMENT_ISSUE", 0)

    # If customer explicitly asks for refund, prefer REFUND_REQUEST
    explicit_refund_phrases = [
        "want a refund", "need a refund", "please refund", "refund me",
        "refund my money", "get my money back", "give me my money back",
        "i want refund", "i need refund", "please give me refund"
    ]
    has_explicit_refund = any(phrase in normalized for phrase in explicit_refund_phrases)

    if has_explicit_refund and refund_score > 0:
        return "REFUND_REQUEST"

    # ===========================================
    # DELIVERY_LATE vs DELIVERY_MISSING
    # ===========================================
    delivery_late_score = scores.get("DELIVERY_LATE", 0)
    delivery_missing_score = scores.get("DELIVERY_MISSING", 0)

    # Explicit missing language
    explicit_missing = [
        "never received", "never got", "didnt get", "didn't get",
        "never arrived", "not received", "package is missing", "order is missing",
        "parcel is missing", "lost package", "empty box"
    ]
    has_explicit_missing = any(phrase in normalized for phrase in explicit_missing)

    # Explicit late language
    explicit_late = [
        "late", "delayed", "delay", "is delayed", "days late",
        "supposed to arrive", "was supposed to", "should have arrived"
    ]
    has_explicit_late = any(phrase in normalized for phrase in explicit_late)

    if has_explicit_missing and not has_explicit_late:
        return "DELIVERY_MISSING"

    if has_explicit_late and not has_explicit_missing:
        return "DELIVERY_LATE"

    # Score-based with priority for MISSING when both present
    if delivery_missing_score > 0 and delivery_late_score > 0:
        never_received = ["never received", "never got", "didnt get", "didn't get"]
        if any(p in normalized for p in never_received):
            return "DELIVERY_MISSING"
        return "DELIVERY_LATE"

    if delivery_missing_score > 0:
        return "DELIVERY_MISSING"

    if delivery_late_score > 0 and (has_delivery_ctx or has_order_ctx):
        return "DELIVERY_LATE"

    # ===========================================
    # DELIVERY_TRACKING
    # ===========================================
    if scores.get("DELIVERY_TRACKING", 0) > 0:
        return "DELIVERY_TRACKING"

    # ===========================================
    # ORDER intents
    # ===========================================
    order_modify_score = scores.get("ORDER_MODIFY", 0)
    order_status_score = scores.get("ORDER_STATUS", 0)

    if order_modify_score > 0:
        cancel_phrases = ["cancel order", "change order", "modify order", "edit order",
                         "cancel my order", "stop order", "delete order"]
        for phrase in cancel_phrases:
            if phrase in normalized:
                return "ORDER_MODIFY"

    if order_status_score > 0:
        return "ORDER_STATUS"

    # ===========================================
    # PRODUCT/RETURN disambiguation
    # ===========================================
    product_score = scores.get("PRODUCT_ISSUE", 0)
    return_score = scores.get("RETURN_REQUEST", 0)

    if product_score > 0 and return_score > 0:
        return "RETURN_REQUEST"
    if return_score > 0:
        return "RETURN_REQUEST"
    if product_score > 0:
        return "PRODUCT_ISSUE"

    # ===========================================
    # PAYMENT_ISSUE vs REFUND_REQUEST - balanced
    # ===========================================

    # If refund context and refund score, prefer refund
    if refund_score > 0 and has_refund_ctx:
        return "REFUND_REQUEST"

    # If payment context and payment score, prefer payment
    if payment_score > 0 and has_payment_ctx:
        return "PAYMENT_ISSUE"

    # Score-based
    if payment_score > 0:
        return "PAYMENT_ISSUE"
    if refund_score > 0:
        return "REFUND_REQUEST"

    # ===========================================
    # TECHNICAL disambiguation
    # ===========================================
    app_score = scores.get("APP_USAGE", 0)
    device_score = scores.get("DEVICE_ISSUE", 0)
    video_score = scores.get("VIDEO_STREAMING", 0)

    if device_score > 0:
        return "DEVICE_ISSUE"
    if video_score > 0:
        return "VIDEO_STREAMING"
    if app_score > 0:
        return "APP_USAGE"

    # ACCOUNT
    if scores.get("ACCOUNT_ACCESS", 0) > 0:
        return "ACCOUNT_ACCESS"

    return "OTHER"

def determine_secondary_intents(customer_text, primary):
    secondary = []
    for intent, patterns in INTENT_PATTERNS.items():
        if intent == primary or intent == "OTHER":
            continue
        if match_intent(customer_text, patterns):
            if is_related_intent(primary, intent):
                continue
            secondary.append(intent)
    return secondary[:3]

def is_related_intent(primary, candidate):
    related_groups = [
        ["DELIVERY_MISSING", "DELIVERY_LATE", "DELIVERY_TRACKING"],
        ["REFUND_REQUEST", "PAYMENT_ISSUE"],
        ["PRODUCT_ISSUE", "RETURN_REQUEST"],
        ["APP_USAGE", "DEVICE_ISSUE", "VIDEO_STREAMING"],
        ["ORDER_STATUS", "ORDER_MODIFY"]
    ]
    for group in related_groups:
        if primary in group and candidate in group:
            return True
    return False

def determine_modifiers(customer_text, all_text):
    modifiers = []
    for modifier, patterns in MODIFIER_PATTERNS.items():
        if match_intent(all_text, patterns):
            modifiers.append(modifier)
    return list(set(modifiers))

def determine_escalation_signals(customer_text):
    signals = []
    for signal, patterns in ESCALATION_PATTERNS.items():
        if match_intent(customer_text, patterns):
            signals.append(signal)
    return list(set(signals))

def determine_confidence(primary, secondary, customer_text, signals):
    if primary == "OTHER":
        return "LOW"
    if len(signals) >= 2:
        return "MEDIUM"
    normalized = normalize_text(customer_text)
    explicit_indicators = [
        "i want", "i need", "i'm trying", "please help",
        "can you", "could you", "need to", "have to"
    ]
    explicit_count = sum(1 for ind in explicit_indicators if ind in normalized)
    if explicit_count >= 1 and primary != "OTHER":
        return "HIGH"
    vague_indicators = ["something", "stuff", "things", "it", "this"]
    vague_count = sum(1 for ind in vague_indicators if ind in normalized)
    if vague_count > explicit_count:
        return "MEDIUM"
    if len(secondary) >= 2:
        return "MEDIUM"
    return "HIGH"

def label_conversation(conv):
    conversation_id = conv.get('conversation_id', '')
    turns = conv.get('turns', [])
    customer_text = get_customer_text(conv)
    all_text = get_all_text(conv)
    language = detect_language(customer_text)
    primary_intent = determine_primary_intent(customer_text, all_text)
    secondary_intents = determine_secondary_intents(customer_text, primary_intent)
    modifiers = determine_modifiers(customer_text, all_text)
    escalation_signals = determine_escalation_signals(customer_text)
    confidence = determine_confidence(primary_intent, secondary_intents, customer_text, escalation_signals)
    return {
        "conversation_id": conversation_id,
        "primary_intent": primary_intent,
        "secondary_intents": secondary_intents,
        "modifiers": modifiers,
        "escalation_signals": escalation_signals,
        "language": language,
        "data_quality": "GOOD",
        "confidence": confidence,
        "turns": turns
    }

def main():
    DATA_DIR = Path(r'C:\Users\DELL\Desktop\hiver\data')
    OUTPUT_DIR = DATA_DIR / 'processed'
    SAMPLES_DIR = DATA_DIR / 'samples'

    print("Loading conversations...")
    conversations = []
    with open(DATA_DIR / 'processed' / 'amazonhelp_intent_discovery_sample.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            conversations.append(json.loads(line))

    print(f"Loaded {len(conversations):,} conversations")

    print("Labeling conversations with V2.2 rules...")
    labeled = []
    for conv in conversations:
        labeled.append(label_conversation(conv))

    print(f"Labeled {len(labeled):,} conversations")

    total = len(labeled)
    other_count = sum(1 for l in labeled if l['primary_intent'] == 'OTHER')

    primary_counts = Counter(l['primary_intent'] for l in labeled)
    secondary_counts = Counter()
    for l in labeled:
        for s in l['secondary_intents']:
            secondary_counts[s] += 1

    modifier_counts = Counter()
    for l in labeled:
        for m in l['modifiers']:
            modifier_counts[m] += 1

    signal_counts = Counter()
    for l in labeled:
        for s in l['escalation_signals']:
            signal_counts[s] += 1

    language_counts = Counter(l['language'] for l in labeled)
    confidence_counts = Counter(l['confidence'] for l in labeled)
    multi_intent_count = sum(1 for l in labeled if len(l['secondary_intents']) > 0)

    statistics = {
        "total_conversations_processed": total,
        "total_other": other_count,
        "other_percentage": round(100 * other_count / total, 1),
        "primary_intent_distribution": dict(primary_counts.most_common()),
        "primary_intent_percentages": {
            intent: round(100 * count / total, 1)
            for intent, count in primary_counts.most_common()
        },
        "secondary_intent_frequencies": dict(secondary_counts.most_common()),
        "modifier_frequencies": dict(modifier_counts.most_common()),
        "escalation_signal_frequencies": dict(signal_counts.most_common()),
        "language_distribution": dict(language_counts),
        "confidence_distribution": dict(confidence_counts),
        "multi_intent_count": multi_intent_count,
        "multi_intent_percentage": round(100 * multi_intent_count / total, 1)
    }

    with open(OUTPUT_DIR / 'amazonhelp_label_statistics_v22.json', 'w', encoding='utf-8') as f:
        json.dump(statistics, f, indent=2, ensure_ascii=False)

    print(f"Saved amazonhelp_label_statistics_v22.json")

    print("Saving labeled conversations V2.2...")
    with open(OUTPUT_DIR / 'amazonhelp_labeled_conversations_v22.jsonl', 'w', encoding='utf-8') as f:
        for labeled_conv in labeled:
            f.write(json.dumps(labeled_conv, ensure_ascii=False) + '\n')

    print(f"Saved amazonhelp_labeled_conversations_v22.jsonl ({len(labeled):,} records)")

    # Compare versions
    print("Comparing versions...")

    v1_labeled = []
    with open(OUTPUT_DIR / 'amazonhelp_labeled_conversations.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            v1_labeled.append(json.loads(line))

    v2_labeled = []
    with open(OUTPUT_DIR / 'amazonhelp_labeled_conversations_v2.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            v2_labeled.append(json.loads(line))

    v21_labeled = []
    with open(OUTPUT_DIR / 'amazonhelp_labeled_conversations_v21.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            v21_labeled.append(json.loads(line))

    v1_by_id = {l['conversation_id']: l for l in v1_labeled}
    v21_by_id = {l['conversation_id']: l for l in v21_labeled}

    changes_v21_v22 = []
    for l in labeled:
        conv_id = l['conversation_id']
        v21_intent = v21_by_id[conv_id]['primary_intent']
        v22_intent = l['primary_intent']
        if v21_intent != v22_intent:
            changes_v21_v22.append({
                'conversation_id': conv_id,
                'v21_intent': v21_intent,
                'v22_intent': v22_intent,
                'customer_text': get_customer_text(v1_by_id[conv_id])[:200]
            })

    comparison = {
        'v1_distribution': dict(Counter(l['primary_intent'] for l in v1_labeled)),
        'v2_distribution': dict(Counter(l['primary_intent'] for l in v2_labeled)),
        'v21_distribution': dict(Counter(l['primary_intent'] for l in v21_labeled)),
        'v22_distribution': dict(primary_counts),
        'v1_confidence': dict(Counter(l['confidence'] for l in v1_labeled)),
        'v2_confidence': dict(Counter(l['confidence'] for l in v2_labeled)),
        'v21_confidence': dict(Counter(l['confidence'] for l in v21_labeled)),
        'v22_confidence': dict(confidence_counts),
        'v1_language': dict(Counter(l['language'] for l in v1_labeled)),
        'v22_language': dict(language_counts),
        'v1_other_count': sum(1 for l in v1_labeled if l['primary_intent'] == 'OTHER'),
        'v2_other_count': sum(1 for l in v2_labeled if l['primary_intent'] == 'OTHER'),
        'v21_other_count': sum(1 for l in v21_labeled if l['primary_intent'] == 'OTHER'),
        'v22_other_count': other_count,
        'changes_v21_v22_count': len(changes_v21_v22),
        'multi_intent_v1': sum(1 for l in v1_labeled if len(l['secondary_intents']) > 0),
        'multi_intent_v2': sum(1 for l in v2_labeled if len(l['secondary_intents']) > 0),
        'multi_intent_v21': sum(1 for l in v21_labeled if len(l['secondary_intents']) > 0),
        'multi_intent_v22': multi_intent_count
    }

    with open(OUTPUT_DIR / 'labeling_v22_comparison.json', 'w', encoding='utf-8') as f:
        json.dump(comparison, f, indent=2, ensure_ascii=False)

    with open(SAMPLES_DIR / 'labeling_v22_changes.json', 'w', encoding='utf-8') as f:
        json.dump({'v21_v22_changes': changes_v21_v22}, f, indent=2, ensure_ascii=False)

    print(f"Changes from V2.1: {len(changes_v21_v22)}")

    print("\n" + "="*60)
    print("V2.2 LABELING SUMMARY")
    print("="*60)

    print(f"\nTotal conversations: {total}")
    print(f"Total OTHER: {other_count} ({100*other_count/total:.1f}%)")

    print("\nPrimary Intent Distribution V2.2:")
    for intent, count in primary_counts.most_common():
        pct = 100 * count / total
        print(f"  {intent}: {count} ({pct:.1f}%)")

    print("\nConfidence Distribution V2.2:")
    for conf, count in confidence_counts.most_common():
        pct = 100 * count / total
        print(f"  {conf}: {count} ({pct:.1f}%)")

    print("\n" + "="*60)
    print("V2.2 LABELING COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()