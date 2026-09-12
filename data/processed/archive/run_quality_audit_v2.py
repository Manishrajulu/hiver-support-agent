#!/usr/bin/env python3
"""Label Quality Audit Script for V2"""

import json
import re
from collections import Counter, defaultdict
import random

random.seed(42)

def detect_language_fixed(text):
    """Fixed language detection"""
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

print("Loading labeled conversations V2...")
labeled = []
with open(r'C:\Users\DELL\Desktop\hiver\data\processed\amazonhelp_labeled_conversations_v2.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        labeled.append(json.loads(line))

print(f"Loaded {len(labeled)} labeled conversations")

print("\n" + "="*60)
print("V2 QUALITY AUDIT - INTENT DISTRIBUTION")
print("="*60)

intent_dist = Counter(l['primary_intent'] for l in labeled)
print("\nIntent Distribution (V2):")
for intent, count in intent_dist.most_common():
    pct = 100 * count / len(labeled)
    print(f"  {intent}: {count} ({pct:.1f}%)")

confidence_dist = Counter(l['confidence'] for l in labeled)
print("\nConfidence Distribution (V2):")
for conf, count in confidence_dist.most_common():
    pct = 100 * count / len(labeled)
    print(f"  {conf}: {count} ({pct:.1f}%)")

multi_intent = sum(1 for l in labeled if len(l.get('secondary_intents', [])) > 0)
print(f"\nMulti-intent conversations: {multi_intent} ({100*multi_intent/len(labeled):.1f}%)")

print("\n" + "="*60)
print("V2 vs V1 COMPARISON")
print("="*60)

old_stats = json.load(open(r'C:\Users\DELL\Desktop\hiver\data\processed\amazonhelp_label_statistics.json', 'r', encoding='utf-8'))
new_stats = json.load(open(r'C:\Users\DELL\Desktop\hiver\data\processed\amazonhelp_label_statistics_v2.json', 'r', encoding='utf-8'))

print("\nKey Changes:")
print(f"  OTHER: {old_stats['primary_intents'].get('OTHER', 0)} -> {new_stats['primary_intents'].get('OTHER', 0)}")
print(f"  DELIVERY_LATE: {old_stats['primary_intents'].get('DELIVERY_LATE', 0)} -> {new_stats['primary_intents'].get('DELIVERY_LATE', 0)}")
print(f"  APP_USAGE: {old_stats['primary_intents'].get('APP_USAGE', 0)} -> {new_stats['primary_intents'].get('APP_USAGE', 0)}")
print(f"  DEVICE_ISSUE: {old_stats['primary_intents'].get('DEVICE_ISSUE', 0)} -> {new_stats['primary_intents'].get('DEVICE_ISSUE', 0)}")

print("\n" + "="*60)
print("AUDIT COMPLETE")
print("="*60)