#!/usr/bin/env python3
"""Deterministic rule-based labeling pipeline for AmazonHelp taxonomy v1.0"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
import random

# ============================================
# CONFIGURATION - Frozen Taxonomy v1.0
# ============================================

PRIMARY_INTENTS = [
    "DELIVERY_MISSING",
    "DELIVERY_LATE",
    "DELIVERY_TRACKING",
    "ORDER_STATUS",
    "ORDER_MODIFY",
    "PRODUCT_ISSUE",
    "RETURN_REQUEST",
    "REFUND_REQUEST",
    "PAYMENT_ISSUE",
    "ACCOUNT_ACCESS",
    "APP_USAGE",
    "DEVICE_ISSUE",
    "VIDEO_STREAMING",
    "OTHER"
]

MODIFIERS = ["PRIME_CUSTOMER", "MARKETPLACE", "DELIVERY_CARRIER", "SUBSCRIPTION"]

ESCALATION_SIGNALS = ["FRUSTRATION_HIGH", "PREVIOUS_CONTACT", "SERVICE_COMPLAINT", "ESCALATION_REQUEST"]

LANGUAGES = ["en", "non_en", "unknown"]

DATA_QUALITIES = ["GOOD", "SHORT", "EMPTY", "NON_ENGLISH", "BROKEN_CHAIN", "OTHER"]

# ============================================
# INTENT KEYWORD PATTERNS
# ============================================

# Higher priority = checked first for disambiguation
INTENT_PATTERNS = {
    # DELIVERY intents - more specific patterns first
    "DELIVERY_MISSING": [
        "not delivered", "never received", "never got", "didnt get", "didn't get",
        "havent received", "haven't received", "never arrived", "show as delivered but",
        "shows delivered but", "says delivered but", "package not received", "order not received",
        "missing", "lost package", "lost order", "where is my package", "where is my order",
        "still waiting for my package", "still waiting for my order", "nothing arrived",
        "empty box", "box was empty"
    ],
    "DELIVERY_LATE": [
        "late", "delayed", "delay", "eta", "expected delivery", "not arrived yet",
        "still waiting", "arriving today", "promise", "when will i get", "days late",
        "taking too long", "still not here", "hasnt arrived", "hasn't arrived",
        "waiting for delivery", "delivery is late", "package is late", "order is late",
        "supposed to arrive", "was supposed to", "promised delivery"
    ],
    "DELIVERY_TRACKING": [
        "tracking", "track my package", "track my order", "tracking number",
        "track order", "where is my package", "package tracking", "can't track",
        "tracking info", "tracking status", "track it", "track package"
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

    # PAYMENT intents
    "REFUND_REQUEST": [
        "refund", "money back", "reimburse", "charged", "refunded", "get my money back",
        "want refund", "need refund", "when will i get my refund", "refund pending",
        "refund not received", "no refund yet", "refund status", "still waiting for refund"
    ],
    "PAYMENT_ISSUE": [
        "payment", "billing", "credit card", "gift card", "debit card", "charged incorrectly",
        "wrong charge", "overcharged", "duplicate charge", "payment method",
        "payment failed", "transaction", "pay", "bank", " Payment "
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
# ESCALATION SIGNAL PATTERNS
# ============================================

ESCALATION_PATTERNS = {
    "FRUSTRATION_HIGH": [
        "angry", "furious", "frustrated", "awful", "terrible", "worst", "pathetic",
        "disgusting", "ridiculous", "unacceptable", "outraged", "fuming", "livid",
        "horrible", "appalling", "disgraceful, extremely", "extremely disappointed"
    ],
    "PREVIOUS_CONTACT": [
        "already contacted", "already called", "spoken to", "tried calling",
        "multiple times", "several times", "days ago", "weeks ago", "last week",
        "last month", "contacted you before", "no response from", "still waiting",
        "been waiting", "been trying", "still not resolved", "not resolved yet"
    ],
    "SERVICE_COMPLAINT": [
        "worst service", "bad service", "poor service", "rude", "no response",
        "bad experience", "terrible experience", "horrible experience", "no help",
        "unhelpful", "incompetent", "lazy", "no one helped", "transferring", "transferred"
    ],
    "ESCALATION_REQUEST": [
        "manager", "supervisor", "escalate", "call me back", "callback",
        "speak to someone", "someone higher", "higher authority", "boss",
        "executive", "lead", "senior", "urgent", "immediately", "ASAP"
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
    # Remove URLs
    text = re.sub(r'http\S+|www\.\S+', '', text)
    # Remove mentions at the start
    text = re.sub(r'^@\w+\s+', '', text)
    # Remove @mentions
    text = re.sub(r'@\w+', '', text)
    # Remove hashtag content
    text = re.sub(r'#\w+', '', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def detect_language(text):
    """Simple language detection"""
    if not text:
        return "unknown"

    # Common non-English indicators
    non_en_patterns = [
        # French
        r'\b(je|tu|il|elle|nous|vous|ils|elles|que|qui|quoi|donc|oui|non|pas|une|un|des|le|la|les|mon|ma|mes|son|sa|ses|notre|votre|leur|cette|ce|cet|cette|avec|pour|dans|sur|sous|entre|chez|mais|ou|et|donc|ni|car|si)\b',
        # Spanish
        r'\b(yo|tu|el|ella|nosotros|vosotros|ellos|ellas|que|quien|como|donde|cuando|porque|si|no|si|una|uno|un|las|los|su|su|este|esta|esto|ese|esa|eso|con|para|por|en|su|la|el|de|del|al|mas|pero|o|u|y|porque|cuando|donde|quien|cual)\b',
        # German
        r'\b(ich|du|er|sie|es|wir|ihr|mich|dich|sich|uns|euch|was|wer|wo|wie|warum|weil|wenn|oder|aber|und|so|nicht|ein|eine|einer|einem|einen|der|die|das|den|dem|des|auf|zu|vom|mit|fur|ist|sind|war|waren|haben|hatt|werden|wurde|diese|dieser|dieses)\b',
        # Hindi
        r'[ऀ-ॿ]+',
        # Non-Latin scripts
        r'[^\x00-\x7F]+'
    ]

    for pattern in non_en_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return "non_en"

    # Check for English common words
    en_words = ['the', 'a', 'an', 'is', 'are', 'was', 'were', 'have', 'has', 'had',
                'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
                'must', 'shall', 'can', 'need', 'want', 'order', 'delivery', 'amazon',
                'help', 'please', 'thank', 'thanks', 'sorry', 'my', 'me', 'i', 'you', 'your']
    words = text.split()
    en_count = sum(1 for w in words if w in en_words)
    if en_count > len(words) * 0.3:
        return "en"

    return "non_en"

def detect_data_quality(conv):
    """Detect data quality issues"""
    if not conv.get('turns'):
        return "EMPTY"

    # Check for broken chain
    turns = conv['turns']
    if len(turns) == 1:
        return "SHORT"

    # Check for empty customer messages
    customer_turns = [t for t in turns if t.get('speaker') == 'Customer']
    if not customer_turns:
        return "EMPTY"

    # Check total text length
    total_text = ' '.join(t.get('text', '') for t in customer_turns)
    if len(total_text) < 20:
        return "SHORT"

    # Check for non-English
    lang = detect_language(total_text)
    if lang == "non_en":
        return "NON_ENGLISH"

    # Check if conversation chain is broken (AmazonHelp responses without customer follow-up)
    # A broken chain might have only AmazonHelp messages
    if len(customer_turns) == 0:
        return "EMPTY"

    return "GOOD"

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

def determine_primary_intent(customer_text, all_text):
    """Determine primary intent based on rules"""

    # Score each intent
    scores = {}
    for intent, patterns in INTENT_PATTERNS.items():
        scores[intent] = count_matches(customer_text, patterns)

    # If no intent matches, return OTHER
    if all(v == 0 for v in scores.values()):
        return "OTHER"

    # Handle intent disambiguation
    # DELIVERY disambiguation
    delivery_missing_score = scores.get("DELIVERY_MISSING", 0)
    delivery_late_score = scores.get("DELIVERY_LATE", 0)
    delivery_tracking_score = scores.get("DELIVERY_TRACKING", 0)
    order_status_score = scores.get("ORDER_STATUS", 0)

    # If tracking keywords present but not explicit delivery issue
    if delivery_tracking_score > 0 and delivery_late_score == 0 and delivery_missing_score == 0:
        return "DELIVERY_TRACKING"

    # If "where is my package/order" without explicit late/missing
    if "where is my" in normalize_text(customer_text) and "package" in normalize_text(customer_text):
        if delivery_late_score == 0 and delivery_missing_score == 0:
            # Could be tracking or order status
            if delivery_tracking_score > 0:
                return "DELIVERY_TRACKING"
            return "ORDER_STATUS"

    # Explicit missing vs late
    if delivery_missing_score > 0:
        # Check if customer is explicitly saying NOT delivered
        missing_phrases = ["not delivered", "never received", "never got", "didnt get", "shows delivered but", "empty box"]
        for phrase in missing_phrases:
            if phrase in normalize_text(customer_text):
                return "DELIVERY_MISSING"
        # If both missing and late, prefer missing
        if delivery_late_score > 0:
            return "DELIVERY_MISSING"
        return "DELIVERY_MISSING"

    if delivery_late_score > 0:
        return "DELIVERY_LATE"

    # ORDER disambiguation
    order_modify_score = scores.get("ORDER_MODIFY", 0)
    if order_modify_score > 0:
        # Cancel/modify is more specific than status
        if "cancel" in normalize_text(customer_text) or "change" in normalize_text(customer_text):
            return "ORDER_MODIFY"
        return "ORDER_MODIFY"

    if order_status_score > 0:
        return "ORDER_STATUS"

    # PRODUCT/RETURN disambiguation
    product_score = scores.get("PRODUCT_ISSUE", 0)
    return_score = scores.get("RETURN_REQUEST", 0)

    if product_score > 0 and return_score > 0:
        # If product issue and return both present, prefer return (customer wants action)
        return "RETURN_REQUEST"
    if return_score > 0:
        return "RETURN_REQUEST"
    if product_score > 0:
        return "PRODUCT_ISSUE"

    # PAYMENT disambiguation
    refund_score = scores.get("REFUND_REQUEST", 0)
    payment_score = scores.get("PAYMENT_ISSUE", 0)

    if refund_score > 0 and payment_score > 0:
        # Prefer refund if customer explicitly wants money back
        if "money back" in normalize_text(customer_text) or "refund" in normalize_text(customer_text):
            return "REFUND_REQUEST"
        return "REFUND_REQUEST"
    if refund_score > 0:
        return "REFUND_REQUEST"
    if payment_score > 0:
        return "PAYMENT_ISSUE"

    # TECHNICAL disambiguation
    app_score = scores.get("APP_USAGE", 0)
    device_score = scores.get("DEVICE_ISSUE", 0)
    video_score = scores.get("VIDEO_STREAMING", 0)

    # Device is more specific
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
    """Determine secondary intents"""

    secondary = []
    normalized = normalize_text(customer_text)

    # Check all intents except primary
    for intent, patterns in INTENT_PATTERNS.items():
        if intent == primary or intent == "OTHER":
            continue
        if match_intent(customer_text, patterns):
            # Don't add if it's closely related to primary
            if is_related_intent(primary, intent):
                continue
            secondary.append(intent)

    return secondary[:3]  # Max 3 secondary intents

def is_related_intent(primary, candidate):
    """Check if candidate is too related to primary (shouldn't be secondary)"""

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
    normalized = normalize_text(customer_text)
    all_normalized = normalize_text(all_text)

    for modifier, patterns in MODIFIER_PATTERNS.items():
        if match_intent(all_text, patterns):
            modifiers.append(modifier)

    return list(set(modifiers))

def determine_escalation_signals(customer_text):
    """Determine escalation signals present"""
    signals = []
    normalized = normalize_text(customer_text)

    for signal, patterns in ESCALATION_PATTERNS.items():
        if match_intent(customer_text, patterns):
            signals.append(signal)

    return list(set(signals))

def determine_confidence(primary, secondary, customer_text, signals):
    """Determine confidence level"""

    if primary == "OTHER":
        return "LOW"

    # Check signal intensity
    if len(signals) >= 2:
        return "MEDIUM"

    # Check for explicit keywords
    normalized = normalize_text(customer_text)
    explicit_indicators = [
        "i want", "i need", "i'm trying", "please help",
        "can you", "could you", "need to", "have to"
    ]

    explicit_count = sum(1 for ind in explicit_indicators if ind in normalized)

    if explicit_count >= 1 and primary != "OTHER":
        return "HIGH"

    # Check for vague language
    vague_indicators = ["something", "stuff", "things", "it", "this"]
    vague_count = sum(1 for ind in vague_indicators if ind in normalized)

    if vague_count > explicit_count:
        return "MEDIUM"

    # If secondary intents exist, might be ambiguous
    if len(secondary) >= 2:
        return "MEDIUM"

    return "HIGH"

# ============================================
# MAIN LABELING FUNCTION
# ============================================

def label_conversation(conv):
    """Label a single conversation"""

    conversation_id = conv.get('conversation_id', '')
    turns = conv.get('turns', [])

    customer_text = get_customer_text(conv)
    all_text = get_all_text(conv)

    # Detect language
    language = detect_language(customer_text)

    # Detect data quality
    data_quality = detect_data_quality(conv)

    # Determine primary intent
    primary_intent = determine_primary_intent(customer_text, all_text)

    # Determine secondary intents
    secondary_intents = determine_secondary_intents(customer_text, primary_intent)

    # Determine modifiers
    modifiers = determine_modifiers(customer_text, all_text)

    # Determine escalation signals
    escalation_signals = determine_escalation_signals(customer_text)

    # Determine confidence
    confidence = determine_confidence(primary_intent, secondary_intents, customer_text, escalation_signals)

    return {
        "conversation_id": conversation_id,
        "primary_intent": primary_intent,
        "secondary_intents": secondary_intents,
        "modifiers": modifiers,
        "escalation_signals": escalation_signals,
        "language": language,
        "data_quality": data_quality,
        "confidence": confidence,
        "turns": turns
    }

# ============================================
# MAIN PIPELINE
# ============================================

def main():
    DATA_DIR = Path(r'C:\Users\DELL\Desktop\hiver\data')
    OUTPUT_DIR = DATA_DIR / 'processed'
    SAMPLES_DIR = DATA_DIR / 'samples'

    # Load conversations
    print("Loading conversations...")
    conversations = []
    with open(DATA_DIR / 'processed' / 'amazonhelp_intent_discovery_sample.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            conversations.append(json.loads(line))

    print(f"Loaded {len(conversations):,} conversations")

    # Label all conversations
    print("Labeling conversations...")
    labeled = []
    for conv in conversations:
        labeled.append(label_conversation(conv))

    print(f"Labeled {len(labeled):,} conversations")

    # ============================================
    # COMPUTE STATISTICS
    # ============================================

    print("Computing statistics...")

    total = len(labeled)
    other_count = sum(1 for l in labeled if l['primary_intent'] == 'OTHER')

    # Primary intent distribution
    primary_counts = Counter(l['primary_intent'] for l in labeled)

    # Secondary intent distribution
    secondary_counts = Counter()
    for l in labeled:
        for s in l['secondary_intents']:
            secondary_counts[s] += 1

    # Modifier distribution
    modifier_counts = Counter()
    for l in labeled:
        for m in l['modifiers']:
            modifier_counts[m] += 1

    # Escalation signal distribution
    signal_counts = Counter()
    for l in labeled:
        for s in l['escalation_signals']:
            signal_counts[s] += 1

    # Language distribution
    language_counts = Counter(l['language'] for l in labeled)

    # Data quality distribution
    quality_counts = Counter(l['data_quality'] for l in labeled)

    # Confidence distribution
    confidence_counts = Counter(l['confidence'] for l in labeled)

    # Multi-intent count (secondary intents > 0)
    multi_intent_count = sum(1 for l in labeled if len(l['secondary_intents']) > 0)

    # ============================================
    # BUILD STATISTICS REPORT
    # ============================================

    statistics = {
        "total_conversations_processed": total,
        "total_successfully_labeled": total,
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
        "data_quality_distribution": dict(quality_counts),
        "confidence_distribution": dict(confidence_counts),
        "multi_intent_count": multi_intent_count,
        "multi_intent_percentage": round(100 * multi_intent_count / total, 1)
    }

    # Save statistics
    with open(OUTPUT_DIR / 'amazonhelp_label_statistics.json', 'w', encoding='utf-8') as f:
        json.dump(statistics, f, indent=2, ensure_ascii=False)

    print(f"Saved amazonhelp_label_statistics.json")

    # ============================================
    # SAVE FULL LABELED DATA
    # ============================================

    print("Saving labeled conversations...")
    with open(OUTPUT_DIR / 'amazonhelp_labeled_conversations.jsonl', 'w', encoding='utf-8') as f:
        for labeled_conv in labeled:
            f.write(json.dumps(labeled_conv, ensure_ascii=False) + '\n')

    print(f"Saved amazonhelp_labeled_conversations.jsonl ({len(labeled):,} records)")

    # ============================================
    # CREATE SAMPLES
    # ============================================

    print("Creating samples...")

    # Random 20 labeled examples
    random.seed(42)
    random_labeled = random.sample(labeled, min(20, len(labeled)))

    # 20 LOW confidence examples
    low_confidence = [l for l in labeled if l['confidence'] == 'LOW']
    low_confidence_sample = random.sample(low_confidence, min(20, len(low_confidence)))

    # 20 OTHER examples
    other_examples = [l for l in labeled if l['primary_intent'] == 'OTHER']
    other_sample = random.sample(other_examples, min(20, len(other_examples)))

    # Format examples for display
    def format_example(l):
        customer_msgs = [t['text'] for t in l['turns'] if t.get('speaker') == 'Customer']
        customer_text = ' '.join(customer_msgs)[:300]
        return {
            "conversation_id": l['conversation_id'],
            "primary_intent": l['primary_intent'],
            "secondary_intents": l['secondary_intents'],
            "modifiers": l['modifiers'],
            "escalation_signals": l['escalation_signals'],
            "confidence": l['confidence'],
            "customer_text_preview": customer_text + ('...' if len(' '.join(customer_msgs)) > 300 else '')
        }

    samples = {
        "random_20_labeled": [format_example(l) for l in random_labeled],
        "low_confidence_20": [format_example(l) for l in low_confidence_sample],
        "other_20": [format_example(l) for l in other_sample]
    }

    with open(SAMPLES_DIR / 'amazonhelp_labeling_sample.json', 'w', encoding='utf-8') as f:
        json.dump(samples, f, indent=2, ensure_ascii=False)

    print(f"Saved amazonhelp_labeling_sample.json")

    # ============================================
    # PRINT SUMMARY
    # ============================================

    print("\n" + "="*60)
    print("LABELING SUMMARY")
    print("="*60)

    print(f"\nTotal conversations: {total}")
    print(f"Total OTHER: {other_count} ({100*other_count/total:.1f}%)")
    print(f"Multi-intent: {multi_intent_count} ({100*multi_intent_count/total:.1f}%)")

    print("\nPrimary Intent Distribution:")
    for intent, count in primary_counts.most_common():
        pct = 100 * count / total
        print(f"  {intent}: {count} ({pct:.1f}%)")

    print("\nTop Secondary Intents:")
    for intent, count in secondary_counts.most_common(5):
        print(f"  {intent}: {count}")

    print("\nModifier Distribution:")
    for modifier, count in modifier_counts.most_common():
        print(f"  {modifier}: {count}")

    print("\nEscalation Signal Distribution:")
    for signal, count in signal_counts.most_common():
        print(f"  {signal}: {count}")

    print("\nLanguage Distribution:")
    for lang, count in language_counts.most_common():
        print(f"  {lang}: {count}")

    print("\nData Quality Distribution:")
    for quality, count in quality_counts.most_common():
        print(f"  {quality}: {count}")

    print("\nConfidence Distribution:")
    for conf, count in confidence_counts.most_common():
        print(f"  {conf}: {count}")

    print("\n" + "="*60)
    print("LABELING COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()