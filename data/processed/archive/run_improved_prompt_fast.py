#!/usr/bin/env python3
"""
Run improved Groq prompt on 100-conversation subset - FAST version with incremental save.
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

# Load existing results if any (for resume)
results = []
try:
    with open('data/evaluation/groq_prompt_experiment_predictions.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            results.append(json.loads(line))
    print(f"Resuming from {len(results)} existing results")
except:
    results = []

processed_ids = set(r['conversation_id'] for r in results)

# Run improved prompt
for i, cid in enumerate(subset_ids):
    if cid in processed_ids:
        continue

    conv = conversations[cid]
    customer_text = conv['text']

    if len(customer_text) > 4000:
        customer_text = customer_text[:4000]

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

        predicted_intent = None
        for line in raw_response.split('\n'):
            line = line.strip()
            if line.startswith('primary_intent:'):
                predicted_intent = line.split(':', 1)[1].strip()
                break

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

    except Exception as e:
        results.append({
            'conversation_id': cid,
            'actual_intent': conv['actual_intent'],
            'original_predicted_intent': original_preds.get(cid),
            'improved_predicted_intent': 'ERROR',
            'raw_response': str(e)
        })

    processed_ids.add(cid)

    # Save after every 10
    if len(results) % 10 == 0:
        with open('data/evaluation/groq_prompt_experiment_predictions.jsonl', 'w', encoding='utf-8') as f:
            for r in results:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')
        print(f"Saved {len(results)}/100")

    time.sleep(0.2)

# Final save
with open('data/evaluation/groq_prompt_experiment_predictions.jsonl', 'w', encoding='utf-8') as f:
    for r in results:
        f.write(json.dumps(r, ensure_ascii=False) + '\n')

print(f"\nFinal: {len(results)} results saved")

# Calculate metrics
improved_correct = sum(1 for r in results if r['actual_intent'] == r['improved_predicted_intent'])
original_correct = sum(1 for r in results if r['actual_intent'] == r['original_predicted_intent'])
improved_accuracy = improved_correct / len(results)
original_accuracy = original_correct / len(results)

print(f"\n=== RESULTS ===")
print(f"Original: {original_accuracy:.4f} ({original_correct}/{len(results)})")
print(f"Improved: {improved_accuracy:.4f} ({improved_correct}/{len(results)})")
print(f"Change: {improved_accuracy - original_accuracy:+.4f}")