#!/usr/bin/env python3
"""Corrected deterministic rule-based labeling pipeline for AmazonHelp taxonomy v1.0

V2.1 fixes from V2 change-impact audit:
1. PAYMENT_ISSUE - strengthen patterns to recover 44 cases incorrectly moved to OTHER
2. DELIVERY_MISSING - strengthen patterns to recover 14 cases incorrectly moved to OTHER
3. DELIVERY_LATE - keep V2 context improvement but allow "when will I get" with order context
4. OTHER recovery - recover only clearly valid existing intents

DO NOT modify taxonomy v1.0
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
import random

# ============================================
# CONFIGURATION - Frozen Taxonomy v1.0
# ============================================

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

# ============================================
# FIXED LANGUAGE DETECTION (V2.1 - unchanged from V2)
# ============================================

def detect_language(text):
    """Fixed language detection - only marks non-English if clearly non-Latin script"""
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

# ============================================
# CONTEXT DETECTION
# ============================================

DELIVERY_CONTEXT = [
    'package', 'packages', 'parcel', 'order', 'orders', 'delivery', 'delivered',
    'shipping', 'shipped', 'shipment', 'courier', 'driver', 'carrier',
    'tracking', 'track', 'arrival', 'arrive', 'expected', 'eta',
    'delivery date', 'delivery day', 'promise', 'promised'
]

REFUND_CONTEXT = [
    'refund', 'money back', 'reimburse'
]

# V2.1: EXPANDED payment context - STRENGTHENED
PAYMENT_CONTEXT = [
    'payment', 'pay', 'billing', 'credit card', 'debit card', 'gift card',
    'charge', 'charged', 'bank', 'transaction', 'card payment', 'online payment',
    'payment method', 'payment failed', 'payment declined', 'payment issue',
    'not charged', 'didnt go through', "didn't go through", 'charge failed',
    'amount deducted', 'amount taken', 'double charge', 'extra charge',
    'unauthorized charge', 'wrong amount', 'incorrect charge'
]

ORDER_CONTEXT = [
    'order', 'orders', 'order number', 'order id'
]

def has_delivery_context(text):
    """Check if text has delivery-related context"""
    text_lower = text.lower()
    return any(ctx in text_lower for ctx in DELIVERY_CONTEXT)

def has_refund_context(text):
    """Check if text has refund-related context"""
    text_lower = text.lower()
    return any(ctx in text_lower for ctx in REFUND_CONTEXT)

def has_payment_context(text):
    """Check if text has payment-related context"""
    text_lower = text.lower()
    return any(ctx in text_lower for ctx in PAYMENT_CONTEXT)

def has_order_context(text):
    """Check if text has order-related context"""
    text_lower = text.lower()
    return any(ctx in text_lower for ctx in ORDER_CONTEXT)

# ============================================
# INTENT PATTERNS - V2.1 CORRECTIONS
# ============================================

INTENT_PATTERNS = {
    # V2.1: DELIVERY_MISSING - STRENGTHENED with more explicit missing patterns
    "DELIVERY_MISSING": [
        # Very explicit - high confidence
        "not delivered", "never received", "never got", "didnt get", "didn't get",
        "havent received", "haven't received", "never arrived", "not receive",
        "show as delivered but", "shows delivered but", "says delivered but",
        "package not received", "order not received", "nothing arrived",
        "empty box", "box was empty", "missing item", "items missing",

        # Explicit missing/lost - high confidence
        "where is my package", "where is my order", "where is my parcel",
        "still waiting for my package", "still waiting for my order",
        "lost package", "lost order", "my package is missing", "my order is missing",
        "parcel is missing", "tracking shows delivered but i don't have",
        "tracking says delivered but", "delivered but i didnt get",
        "delivered but nothing", "delivered but not received",
        "was delivered but i", "should have been delivered",

        # Generic missing - medium confidence
        "missing", "didn't get", "didnt get my"
    ],

    # V2.1: DELIVERY_LATE - KEEP V2 context improvement but add flexibility
    "DELIVERY_LATE": [
        # Explicit late - no context needed
        "late", "delayed", "delay", "eta", "expected delivery", "promise",
        "days late", "taking too long", "still not here", "hasnt arrived", "hasn't arrived",
        "supposed to arrive", "was supposed to", "promised delivery", "delivery is late",
        "package is late", "order is late", "arriving today", "delivery is delayed",

        # AMBIGUOUS PHRASES - require delivery context (V2 improvement preserved)
        # "still waiting" requires delivery context
        # "not arrived yet" requires delivery context
        # "waiting for delivery" requires delivery context

        # V2.1: "when will i get" - allow with ORDER context (not just delivery)
        "when will i get my order", "when will i get my package", "when will i get my parcel",
        "when is my order coming", "when is my package arriving"
    ],

    "DELIVERY_TRACKING": [
        "tracking", "track my package", "track my order", "tracking number",
        "track order", "where is my package", "package tracking", "can't track",
        "tracking info", "tracking status", "track it", "track package",
        "can't track my", "unable to track", "tracking not working"
    ],

    # ORDER intents
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

    # PRODUCT intents
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

    # V2.1: REFUND_REQUEST - refined to distinguish from PAYMENT_ISSUE
    "REFUND_REQUEST": [
        # Explicit refund requests
        "refund", "money back", "reimburse", "get my money back",
        "want refund", "need refund", "when will i get my refund", "refund pending",
        "refund not received", "no refund yet", "refund status", "still waiting for refund",
        "refund issued", "refund processed", "refund approved",

        # Refund + item/product context (medium confidence)
        "refund for item", "refund for order", "refund my item", "refund my order"
    ],

    # V2.1: PAYMENT_ISSUE - SIGNIFICANTLY STRENGTHENED
    "PAYMENT_ISSUE": [
        # Payment problems - core patterns
        "payment", "billing", "credit card", "debit card", "gift card",
        "charged", "charge", "transaction",

        # Payment failures
        "payment failed", "payment declined", "payment not working", "payment issue",
        "payment method", "card payment", "online payment", "payment processing",

        # Incorrect charges
        "wrong charge", "charged wrong", "incorrect charge", "overcharged",
        "duplicate charge", "double charge", "extra charge", "unexpected charge",
        "unauthorized charge", "charged unexpectedly", "wrong amount",

        # Payment method issues
        "card declined", "card rejected", "card not working", "card failed",
        "bank issues", "bank problem", "payment refused",

        # Amazon Pay issues
        "amazon pay", "pay balance", "pay account",

        # V2.1: Added patterns based on audit findings
        "not charged", "didnt go through", "amount not deducted", "payment didn't go",
        "card charged", "card processing"
    ],

    # ACCOUNT intents
    "ACCOUNT_ACCESS": [
        "login", "password", "locked", "access", "account suspended", "sign in", "log in",
        "cant login", "can't login", "cant sign in", "can't sign in", "forgot password",
        "reset password", "account locked", "locked out", "signin", "logging in"
    ],

    # TECHNICAL intents
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

# ============================================
# MODIFIER PATTERNS
# ============================================

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

# ============================================
# ESCALATION PATTERNS
# ============================================

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

# ============================================
# HELPER FUNCTIONS
# ============================================

def normalize_text(text):
    """Safely normalize text for matching"""
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
    """Get all customer message text"""
    customer_turns = [t for t in conv.get('turns', []) if t.get('speaker') == 'Customer']
    return ' '.join(t.get('text', '') for t in customer_turns)

def get_all_text(conv):
    """Get all conversation text"""
    return ' '.join(t.get('text', '') for t in conv.get('turns', []))

def match_intent(text, patterns):
    """Check if any pattern matches"""
    normalized = normalize_text(text)
    for pattern in patterns:
        if pattern in normalized:
            return True
    return False

def count_matches(text, patterns):
    """Count how many patterns match"""
    normalized = normalize_text(text)
    count = 0
    for pattern in patterns:
        if pattern in normalized:
            count += 1
    return count

# ============================================
# PRIMARY INTENT DETERMINATION - V2.1
# ============================================

def determine_primary_intent(customer_text, all_text):
    """Determine primary intent based on V2.1 corrected rules"""

    # Score each intent
    scores = {}
    for intent, patterns in INTENT_PATTERNS.items():
        scores[intent] = count_matches(customer_text, patterns)

    normalized = normalize_text(customer_text)
    has_delivery_ctx = has_delivery_context(customer_text)
    has_order_ctx = has_order_context(customer_text)
    has_refund_ctx = has_refund_context(customer_text)
    has_payment_ctx = has_payment_context(customer_text)

    # If no intent matches, return OTHER
    if all(v == 0 for v in scores.values()):
        return "OTHER"

    # ===========================================
    # V2.1: DELIVERY_MISSING - Highest priority for explicit missing
    # ===========================================
    delivery_missing_score = scores.get("DELIVERY_MISSING", 0)
    delivery_late_score = scores.get("DELIVERY_LATE", 0)

    if delivery_missing_score > 0:
        # Very explicit missing patterns - return immediately
        explicit_missing = [
            "never received", "never got", "didnt get", "didn't get",
            "havent received", "haven't received", "never arrived",
            "show as delivered but", "shows delivered but", "says delivered but",
            "package not received", "order not received", "empty box",
            "where is my package", "where is my order", "lost package", "lost order",
            "tracking shows delivered but", "tracking says delivered but",
            "delivered but i didnt get", "delivered but i don't have",
            "delivered but nothing", "delivered but not received",
            "my package is missing", "my order is missing", "parcel is missing",
            "items missing", "missing item"
        ]
        for phrase in explicit_missing:
            if phrase in normalized:
                return "DELIVERY_MISSING"

        # If both missing and late present, prefer missing
        if delivery_late_score > 0 and (has_delivery_ctx or has_order_ctx):
            return "DELIVERY_MISSING"

    # ===========================================
    # V2.1: DELIVERY_LATE - Keep V2 context improvement with flexibility
    # ===========================================

    # Check for ambiguous phrases
    ambiguous_phrases = ["still waiting", "not arrived yet", "waiting for delivery"]

    has_ambiguous = any(phrase in normalized for phrase in ambiguous_phrases)

    # V2.1: "when will i get" - allow with order OR delivery context
    when_will_get_match = "when will i get" in normalized
    has_order_or_delivery = has_delivery_ctx or has_order_ctx

    # If ambiguous phrase without context, reduce score to 0
    if has_ambiguous and not has_delivery_ctx:
        delivery_late_score = 0

    # If "when will i get" without order/delivery context, reduce score
    if when_will_get_match and not has_order_or_delivery:
        delivery_late_score = 0

    # V2.1: "when will i get my order/package" - allow with order context
    if when_will_get_match and has_order_ctx and not has_delivery_ctx:
        delivery_allow_phrases = [
            "when will i get my order", "when will i get my package",
            "when will i get my parcel", "when is my order coming"
        ]
        for phrase in delivery_allow_phrases:
            if phrase in normalized:
                delivery_late_score = max(delivery_late_score, 1)

    # Return DELIVERY_LATE if score remains positive with context
    if delivery_late_score > 0 and (has_delivery_ctx or has_order_ctx or delivery_late_score >= 2):
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
    # V2.1: PAYMENT vs REFUND disambiguation - IMPROVED
    # ===========================================
    refund_score = scores.get("REFUND_REQUEST", 0)
    payment_score = scores.get("PAYMENT_ISSUE", 0)

    # V2.1: If payment context present AND payment score > 0, prefer PAYMENT_ISSUE
    # UNLESS refund context is strong
    if payment_score > 0 and has_payment_ctx:
        # Check if it's really a refund issue
        if has_refund_ctx and refund_score > payment_score:
            return "REFUND_REQUEST"
        return "PAYMENT_ISSUE"

    # If refund context strong, prefer refund
    if refund_score > 0 and has_refund_ctx:
        return "REFUND_REQUEST"

    # If payment score exists, prefer payment
    if payment_score > 0:
        return "PAYMENT_ISSUE"

    # If only refund score exists
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

    # ===========================================
    # ACCOUNT
    # ===========================================
    if scores.get("ACCOUNT_ACCESS", 0) > 0:
        return "ACCOUNT_ACCESS"

    # ===========================================
    # Re-check DELIVERY_LATE with lower threshold
    # ===========================================
    if delivery_late_score > 0:
        return "DELIVERY_LATE"

    return "OTHER"

def determine_secondary_intents(customer_text, primary):
    """Determine secondary intents"""
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
    """Check if candidate is too related to primary"""
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
    """Determine modifiers present"""
    modifiers = []

    for modifier, patterns in MODIFIER_PATTERNS.items():
        if match_intent(all_text, patterns):
            modifiers.append(modifier)

    return list(set(modifiers))

def determine_escalation_signals(customer_text):
    """Determine escalation signals present"""
    signals = []

    for signal, patterns in ESCALATION_PATTERNS.items():
        if match_intent(customer_text, patterns):
            signals.append(signal)

    return list(set(signals))

def determine_confidence(primary, secondary, customer_text, signals):
    """Determine confidence level"""

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
    """Label a single conversation"""
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

# ============================================
# MAIN
# ============================================

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

    print("Labeling conversations with V2.1 corrected rules...")
    labeled = []
    for conv in conversations:
        labeled.append(label_conversation(conv))

    print(f"Labeled {len(labeled):,} conversations")

    # Compute statistics
    print("Computing statistics...")

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

    with open(OUTPUT_DIR / 'amazonhelp_label_statistics_v21.json', 'w', encoding='utf-8') as f:
        json.dump(statistics, f, indent=2, ensure_ascii=False)

    print(f"Saved amazonhelp_label_statistics_v21.json")

    # Save labeled conversations v2.1
    print("Saving labeled conversations V2.1...")
    with open(OUTPUT_DIR / 'amazonhelp_labeled_conversations_v21.jsonl', 'w', encoding='utf-8') as f:
        for labeled_conv in labeled:
            f.write(json.dumps(labeled_conv, ensure_ascii=False) + '\n')

    print(f"Saved amazonhelp_labeled_conversations_v21.jsonl ({len(labeled):,} records)")

    # ============================================
    # COMPARE V1 vs V2 vs V2.1
    # ============================================

    print("Comparing V1 vs V2 vs V2.1...")

    # Load V1 and V2
    v1_labeled = []
    with open(OUTPUT_DIR / 'amazonhelp_labeled_conversations.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            v1_labeled.append(json.loads(line))

    v2_labeled = []
    with open(OUTPUT_DIR / 'amazonhelp_labeled_conversations_v2.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            v2_labeled.append(json.loads(line))

    # Index by conversation_id
    v1_by_id = {l['conversation_id']: l for l in v1_labeled}
    v2_by_id = {l['conversation_id']: l for l in v2_labeled}

    # Find changes V1->V2.1 and V2->V2.1
    changes_v1_v21 = []
    changes_v2_v21 = []

    for l in labeled:
        conv_id = l['conversation_id']
        v1_intent = v1_by_id[conv_id]['primary_intent']
        v2_intent = v2_by_id[conv_id]['primary_intent']
        v21_intent = l['primary_intent']

        if v1_intent != v21_intent:
            changes_v1_v21.append({
                'conversation_id': conv_id,
                'v1_intent': v1_intent,
                'v21_intent': v21_intent,
                'customer_text': get_customer_text(v1_by_id[conv_id])[:200]
            })

        if v2_intent != v21_intent:
            changes_v2_v21.append({
                'conversation_id': conv_id,
                'v2_intent': v2_intent,
                'v21_intent': v21_intent,
                'customer_text': get_customer_text(v1_by_id[conv_id])[:200]
            })

    # Create three-way comparison
    comparison = {
        'v1_distribution': dict(Counter(l['primary_intent'] for l in v1_labeled)),
        'v2_distribution': dict(Counter(l['primary_intent'] for l in v2_labeled)),
        'v21_distribution': dict(primary_counts),
        'v1_confidence': dict(Counter(l['confidence'] for l in v1_labeled)),
        'v2_confidence': dict(Counter(l['confidence'] for l in v2_labeled)),
        'v21_confidence': dict(confidence_counts),
        'v1_language': dict(Counter(l['language'] for l in v1_labeled)),
        'v2_language': dict(Counter(l['language'] for l in v2_labeled)),
        'v21_language': dict(language_counts),
        'v1_other_count': sum(1 for l in v1_labeled if l['primary_intent'] == 'OTHER'),
        'v2_other_count': sum(1 for l in v2_labeled if l['primary_intent'] == 'OTHER'),
        'v21_other_count': other_count,
        'changes_v1_v21_count': len(changes_v1_v21),
        'changes_v2_v21_count': len(changes_v2_v21),
        'multi_intent_v1': sum(1 for l in v1_labeled if len(l['secondary_intents']) > 0),
        'multi_intent_v2': sum(1 for l in v2_labeled if len(l['secondary_intents']) > 0),
        'multi_intent_v21': multi_intent_count
    }

    with open(OUTPUT_DIR / 'labeling_v21_comparison.json', 'w', encoding='utf-8') as f:
        json.dump(comparison, f, indent=2, ensure_ascii=False)

    print(f"Saved labeling_v21_comparison.json")

    # Save changes
    with open(SAMPLES_DIR / 'labeling_v21_changes.json', 'w', encoding='utf-8') as f:
        json.dump({
            'v1_v21_changes': changes_v1_v21[:100],
            'v2_v21_changes': changes_v2_v21
        }, f, indent=2, ensure_ascii=False)

    print(f"Saved labeling_v21_changes.json")

    # ============================================
    # PRINT SUMMARY
    # ============================================

    print("\n" + "="*60)
    print("V2.1 LABELING SUMMARY")
    print("="*60)

    print(f"\nTotal conversations: {total}")
    print(f"Total OTHER: {other_count} ({100*other_count/total:.1f}%)")
    print(f"Changes from V1: {len(changes_v1_v21)}")
    print(f"Changes from V2: {len(changes_v2_v21)}")

    print("\nPrimary Intent Distribution V2.1:")
    for intent, count in primary_counts.most_common():
        pct = 100 * count / total
        v1_count = v1_labeled and Counter(v1_by_id[i['conversation_id']]['primary_intent'] for i in labeled if i['conversation_id'] in v1_by_id).get(intent, 0) or 0
        print(f"  {intent}: {count} ({pct:.1f}%)")

    print("\nConfidence Distribution V2.1:")
    for conf, count in confidence_counts.most_common():
        pct = 100 * count / total
        print(f"  {conf}: {count} ({pct:.1f}%)")

    print("\n" + "="*60)
    print("V2.1 LABELING COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()