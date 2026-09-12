#!/usr/bin/env python3
"""
Run improved Groq prompt on 100-conversation subset.
"""

import json
import sys
import time
from collections import Counter
from groq import Groq

sys.stdout.reconfigure(encoding='utf-8')

# Load API key
with open('data/api_key.env', 'r') as f:
    for line in f:
        line = line.strip()
        if line.startswith('GROQ_API_KEY='):
            api_key = line.split('=', 1)[1].strip()
            break

client = Groq(api_key=api_key)

# Load improved prompt
with open('data/evaluation/groq_improved_prompt.md', 'r') as f:
    SYSTEM_PROMPT = f.read()

VALID_INTENTS = [
    "DELIVERY_MISSING", "DELIVERY_LATE", "DELIVERY_TRACKING", "ORDER_STATUS",
    "ORDER_MODIFY", "PRODUCT_ISSUE", "RETURN_REQUEST", "REFUND_REQUEST",
    "PAYMENT_ISSUE", "ACCOUNT_ACCESS", "APP_USAGE", "DEVICE_ISSUE",
    "VIDEO_STREAMING", "OTHER"
]

# Load 100 subset
with open('data/evaluation/groq_prompt_experiment_subset.json', 'r') as f:
    subset = json.load(f)
subset_ids = subset['subset_ids']

# Load conversations
conversations = {}
with open('data/processed/amazonhelp_labeled_conversations_v21.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        conv = json.loads(line)
        if conv['conversation_id'] in subset_ids:
            customer_texts = []
            for turn in conv.get('turns', []):
                if turn.get('speaker') == 'Customer':
                    customer_texts.append(turn.get('text', ''))
            conversations[conv['conversation_id']] = {
                'text': ' '.join(customer_texts),
                'actual_intent': conv['primary_intent']
            }

print(f"Loaded {len(conversations)} conversations")

# Load original Groq predictions
original_preds = {}
with open('data/evaluation/groq_test_predictions.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        rec = json.loads(line)
        if rec['conversation_id'] in subset_ids:
            original_preds[rec['conversation_id']] = rec['groq_predicted_intent']

print(f"Loaded {len(original_preds)} original predictions")

# Run improved prompt
results = []
success = 0
fail = 0

for i, cid in enumerate(subset_ids):
    if cid not in conversations:
        continue

    conv = conversations[cid]
    customer_text = conv['text']

    # Truncate if too long
    if len(customer_text) > 4000:
        customer_text = customer_text[:4000]

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="allam-2-7b",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Classify this conversation:\n\n{customer_text}"}
                ],
                temperature=0.1,
                max_tokens=100
            )

            raw_response = response.choices[0].message.content

            # Parse response
            predicted_intent = None
            for line in raw_response.split('\n'):
                line = line.strip()
                if line.startswith('primary_intent:'):
                    predicted_intent = line.split(':', 1)[1].strip()
                    break

            # Validate
            if predicted_intent not in VALID_INTENTS:
                for intent in VALID_INTENTS:
                    if intent in raw_response.upper():
                        predicted_intent = intent
                        break
                else:
                    predicted_intent = "OTHER"

            results.append({
                'conversation_id': cid,
                'actual_intent': conv['actual_intent'],
                'original_predicted_intent': original_preds.get(cid),
                'improved_predicted_intent': predicted_intent,
                'raw_response': raw_response
            })
            success += 1
            break

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 * (attempt + 1))
            else:
                results.append({
                    'conversation_id': cid,
                    'actual_intent': conv['actual_intent'],
                    'original_predicted_intent': original_preds.get(cid),
                    'improved_predicted_intent': 'ERROR',
                    'raw_response': str(e)
                })
                fail += 1

    if (i + 1) % 20 == 0:
        print(f"Processed {i + 1}/100")

    time.sleep(0.3)

print(f"\nCompleted: {success} success, {fail} failures")

# Save predictions
with open('data/evaluation/groq_prompt_experiment_predictions.jsonl', 'w', encoding='utf-8') as f:
    for r in results:
        f.write(json.dumps(r, ensure_ascii=False) + '\n')

print("Saved: data/evaluation/groq_prompt_experiment_predictions.jsonl")

# Calculate metrics
improved_correct = sum(1 for r in results if r['actual_intent'] == r['improved_predicted_intent'])
original_correct = sum(1 for r in results if r['actual_intent'] == r['original_predicted_intent'])
improved_accuracy = improved_correct / len(results)
original_accuracy = original_correct / len(results)

print(f"\n=== RESULTS ON 100-CONVERSATION SUBSET ===")
print(f"Original prompt accuracy: {original_accuracy:.4f} ({original_correct}/100)")
print(f"Improved prompt accuracy: {improved_accuracy:.4f} ({improved_correct}/100)")
print(f"Improvement: {improved_accuracy - original_accuracy:+.4f}")

# Per-intent analysis
improved_confusions = Counter()
original_confusions = Counter()

for r in results:
    if r['actual_intent'] != r['improved_predicted_intent']:
        improved_confusions[f"{r['actual_intent']} -> {r['improved_predicted_intent']}"] += 1
    if r['actual_intent'] != r['original_predicted_intent']:
        original_confusions[f"{r['actual_intent']} -> {r['original_predicted_intent']}"] += 1

# Per-intent prediction distribution
actual_dist = Counter(r['actual_intent'] for r in results)
improved_pred_dist = Counter(r['improved_predicted_intent'] for r in results)
original_pred_dist = Counter(r['original_predicted_intent'] for r in results)

print("\n=== PER-INTENT DISTRIBUTION ===")
print(f"{'Intent':<20} {'Actual':<8} {'Original':<8} {'Improved':<8}")
for intent in sorted(actual_dist.keys()):
    print(f"{intent:<20} {actual_dist[intent]:<8} {original_pred_dist.get(intent, 0):<8} {improved_pred_dist.get(intent, 0):<8}")

print("\n=== TOP ORIGINAL PROMPT CONFUSIONS ===")
for pair, count in original_confusions.most_common(5):
    print(f"  {pair}: {count}")

print("\n=== TOP IMPROVED PROMPT CONFUSIONS ===")
for pair, count in improved_confusions.most_common(5):
    print(f"  {pair}: {count}")

# Save comparison JSON
comparison = {
    'subset_size': 100,
    'original_accuracy': original_accuracy,
    'improved_accuracy': improved_accuracy,
    'improvement': improved_accuracy - original_accuracy,
    'original_correct': original_correct,
    'improved_correct': improved_correct,
    'success_count': success,
    'fail_count': fail,
    'actual_distribution': dict(actual_dist),
    'original_predicted_distribution': dict(original_pred_dist),
    'improved_predicted_distribution': dict(improved_pred_dist),
    'original_top_confusions': dict(original_confusions.most_common(10)),
    'improved_top_confusions': dict(improved_confusions.most_common(10))
}

with open('data/evaluation/groq_prompt_experiment_comparison.json', 'w') as f:
    json.dump(comparison, f, indent=2)

print("\nSaved: data/evaluation/groq_prompt_experiment_comparison.json")