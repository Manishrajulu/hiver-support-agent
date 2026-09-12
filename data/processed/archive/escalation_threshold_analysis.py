#!/usr/bin/env python3
"""
Task 3: Escalation Threshold Sensitivity Analysis

Analyze the existing evaluation data to find defensible escalation thresholds.
"""

import json
import numpy as np
from collections import Counter

# Load end-to-end results
results = []
with open('data/evaluation/sprint5_end_to_end_results.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        results.append(json.loads(line))

print(f"Loaded {len(results)} evaluation results")

# HIGH_RISK intents
HIGH_RISK = {'REFUND_REQUEST', 'PAYMENT_ISSUE', 'ACCOUNT_ACCESS', 'ORDER_MODIFY'}

def analyze_threshold(conf_thresh, sim_thresh, require_intent_match=False):
    """Analyze a threshold combination."""
    auto_handle = []
    escalate = []

    for r in results:
        # Calculate avg similarity
        avg_sim = np.mean(r['retrieval_scores']) if r['retrieval_scores'] else 0

        # Check risk flags
        risk_flags = []

        # High-risk check
        if r['predicted_intent'] in HIGH_RISK:
            risk_flags.append('HIGH_RISK')

        # Confidence check
        if r['confidence'] < conf_thresh:
            risk_flags.append('LOW_CONF')

        # Evidence check
        if not r['retrieval_scores'] or avg_sim < sim_thresh:
            risk_flags.append('WEAK_EVIDENCE')

        # Intent match check (optional)
        if require_intent_match:
            # Check if any retrieved has same intent as predicted
            # We don't have full retrieved intent info in this data
            pass

        if risk_flags:
            escalate.append(r)
        else:
            auto_handle.append(r)

    # Calculate metrics
    total = len(results)
    esc_rate = len(escalate) / total
    ah_rate = len(auto_handle) / total

    # Auto-handle correctness
    ah_correct = sum(1 for r in auto_handle if r['predicted_intent'] == r['actual_intent'])
    ah_accuracy = ah_correct / len(auto_handle) if auto_handle else 0

    # Risky auto-handles (wrong intent)
    ah_wrong_intent = sum(1 for r in auto_handle if r['predicted_intent'] != r['actual_intent'])

    # High-risk auto-handles (high-risk intent)
    ah_high_risk = sum(1 for r in auto_handle if r['predicted_intent'] in HIGH_RISK)

    return {
        'conf_thresh': conf_thresh,
        'sim_thresh': sim_thresh,
        'escalate_count': len(escalate),
        'auto_handle_count': len(auto_handle),
        'esc_rate': esc_rate,
        'ah_rate': ah_rate,
        'ah_correct': ah_correct,
        'ah_accuracy': ah_accuracy,
        'ah_wrong_intent': ah_wrong_intent,
        'ah_high_risk': ah_high_risk
    }

# Analyze multiple thresholds
print("\n" + "="*80)
print("THRESHOLD SENSITIVITY ANALYSIS")
print("="*80)

# Current policy: conf<0.3, sim<0.4
print("\n--- CURRENT POLICY (conf<0.3, sim<0.4) ---")
current = analyze_threshold(0.3, 0.4)
print(f"Escalation: {current['escalate_count']}/{len(results)} = {current['esc_rate']:.1%}")
print(f"AUTO_HANDLE: {current['auto_handle_count']}/{len(results)} = {current['ah_rate']:.1%}")
print(f"AUTO_HANDLE accuracy: {current['ah_correct']}/{current['auto_handle_count']} = {current['ah_accuracy']:.1%}")
print(f"AUTO_HANDLE wrong intent: {current['ah_wrong_intent']}")
print(f"AUTO_HANDLE high-risk: {current['ah_high_risk']}")

# Test different combinations
print("\n--- THRESHOLD GRID SEARCH ---")
print(f"{'Conf':>6} {'Sim':>6} {'Esc':>6} {'AH':>6} {'Esc%':>7} {'AH%':>7} {'AH_acc':>7} {'AH_wrong':>9} {'AH_risk':>8}")
print("-" * 80)

thresholds = [
    (0.2, 0.3),
    (0.2, 0.4),
    (0.2, 0.5),
    (0.25, 0.3),
    (0.25, 0.4),
    (0.25, 0.5),
    (0.3, 0.3),
    (0.3, 0.4),
    (0.3, 0.5),
    (0.35, 0.3),
    (0.35, 0.4),
    (0.35, 0.5),
    (0.4, 0.3),
    (0.4, 0.4),
    (0.4, 0.5),
    (0.5, 0.3),
    (0.5, 0.4),
    (0.5, 0.5),
]

best_for_safety = None
best_for_auto_handle = None

for conf, sim in thresholds:
    r = analyze_threshold(conf, sim)
    print(f"{conf:>6.2f} {sim:>6.2f} {r['escalate_count']:>6} {r['auto_handle_count']:>6} {r['esc_rate']:>7.1%} {r['ah_rate']:>7.1%} {r['ah_accuracy']:>7.1%} {r['ah_wrong_intent']:>9} {r['ah_high_risk']:>8}")

    # Track safest (no wrong intents, no high-risk)
    if r['ah_wrong_intent'] == 0 and r['ah_high_risk'] == 0:
        if best_for_safety is None or r['ah_rate'] > best_for_safety['ah_rate']:
            best_for_safety = r

    # Track best auto-handle rate with acceptable safety
    if r['ah_wrong_intent'] == 0 and r['ah_high_risk'] == 0:
        if best_for_auto_handle is None or r['auto_handle_count'] > best_for_auto_handle['auto_handle_count']:
            best_for_auto_handle = r

print("\n--- BEST OPTIONS ---")

if best_for_safety:
    print(f"\nSafest option (0 wrong intent, 0 high-risk):")
    print(f"  Thresholds: conf>={best_for_safety['conf_thresh']}, sim>={best_for_safety['sim_thresh']}")
    print(f"  AUTO_HANDLE: {best_for_safety['auto_handle_count']}/{len(results)} = {best_for_safety['ah_rate']:.1%}")
    print(f"  Accuracy when AUTO_HANDLE: {best_for_safety['ah_accuracy']:.1%}")

# Analyze why cases escalate
print("\n" + "="*80)
print("ESCALATION BREAKDOWN (Current policy: conf<0.3, sim<0.4)")
print("="*80)

# Current policy
esc_by_reason = Counter()
for r in results:
    conf = r['confidence']
    sim = np.mean(r['retrieval_scores']) if r['retrieval_scores'] else 0
    intent = r['predicted_intent']

    reasons = []
    if intent in HIGH_RISK:
        reasons.append('HIGH_RISK')
    if conf < 0.3:
        reasons.append(f'LOW_CONF({conf:.2f})')
    if not r['retrieval_scores'] or sim < 0.4:
        reasons.append('WEAK_EVIDENCE')

    for reason in reasons:
        esc_by_reason[reason] += 1

print("\nEscalation reasons:")
for reason, count in esc_by_reason.most_common():
    print(f"  {reason}: {count}")

# Analyze AUTO_HANDLE cases
print("\n--- AUTO_HANDLE CASES ANALYSIS ---")
ah_cases = [r for r in results if
    r['predicted_intent'] not in HIGH_RISK and
    r['confidence'] >= 0.3 and
    (not r['retrieval_scores'] or np.mean(r['retrieval_scores']) >= 0.4)
]

print(f"\nAUTO_HANDLE cases: {len(ah_cases)}")

for r in ah_cases:
    avg_sim = np.mean(r['retrieval_scores']) if r['retrieval_scores'] else 0
    print(f"\n  ID: {r['conversation_id']}")
    print(f"    Intent: {r['predicted_intent']} (actual: {r['actual_intent']})")
    print(f"    Confidence: {r['confidence']:.3f}")
    print(f"    Avg similarity: {avg_sim:.3f}")
    print(f"    Correct intent: {r['predicted_intent'] == r['actual_intent']}")