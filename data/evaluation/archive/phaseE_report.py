#!/usr/bin/env python3
"""
Phase E: Generate Full Report
"""
import json
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 70)
print("PHASE E: TAXONOMY CLEANUP REPORT")
print("=" * 70)

# =============================================================================
# SECTION 1: CHANGES APPLIED
# =============================================================================
print("\n" + "=" * 70)
print("SECTION 1: TAXONOMY CHANGES APPLIED")
print("=" * 70)

with open("data/cleaned/phaseE_change_log.json", 'r') as f:
    change_log = json.load(f)

all_changes = change_log['all_changes']
print(f"\nTotal examples relabeled: {len(all_changes)}")

# Count by original label
original_counts = {}
for cid, old, new in all_changes:
    original_counts[old] = original_counts.get(old, 0) + 1

print("\nRelabeling by original label:")
for label, count in sorted(original_counts.items(), key=lambda x: -x[1]):
    print(f"  {label}: {count}")

print("\nAll relabelings:")
for cid, old, new in all_changes:
    print(f"  {cid}: {old} -> {new}")

# =============================================================================
# SECTION 2: PHASE E RESULTS
# =============================================================================
print("\n" + "=" * 70)
print("SECTION 2: PHASE E RESULTS (ACTUAL)")
print("=" * 70)

phaseE_accuracy = 377 / 540
phaseC_accuracy = 384 / 540
phase6_accuracy = 381 / 540

print(f"\nMEASURED ACCURACY:")
print(f"  Phase 6 (original):  {phase6_accuracy*100:.2f}% (381/540)")
print(f"  Phase C (baseline):  {phaseC_accuracy*100:.2f}% (384/540)")
print(f"  Phase E (cleaned):   {phaseE_accuracy*100:.2f}% (377/540)")
print(f"  Delta vs Phase C:    {(phaseE_accuracy - phaseC_accuracy)*100:+.2f}pp")
print(f"  Delta vs Phase 6:    {(phaseE_accuracy - phase6_accuracy)*100:+.2f}pp")

# =============================================================================
# SECTION 3: CONFUSION MATRIX COMPARISON
# =============================================================================
print("\n" + "=" * 70)
print("SECTION 3: CONFUSION MATRIX COMPARISON")
print("=" * 70)

# Phase C pairs (from Phase A report)
phaseC_pairs = [
    ('APP_USAGE', 'OTHER', 14),
    ('DELIVERY_LATE', 'OTHER', 13),
    ('DEVICE_ISSUE', 'OTHER', 9),
    ('DELIVERY_LATE', 'RETURN_REQUEST', 6),
    ('DELIVERY_MISSING', 'DELIVERY_LATE', 6),
    ('ORDER_STATUS', 'OTHER', 6),
    ('ACCOUNT_ACCESS', 'OTHER', 5),
    ('APP_USAGE', 'DELIVERY_LATE', 4),
    ('DELIVERY_LATE', 'DELIVERY_MISSING', 4),
    ('OTHER', 'APP_USAGE', 4),
    ('OTHER', 'DELIVERY_LATE', 4),
    ('VIDEO_STREAMING', 'DELIVERY_LATE', 4),
    ('VIDEO_STREAMING', 'OTHER', 4),
    ('DELIVERY_MISSING', 'OTHER', 3),
    ('ORDER_STATUS', 'PAYMENT_ISSUE', 3)
]

# Phase E pairs (from training output)
phaseE_pairs = [
    ('APP_USAGE', 'OTHER', 14),
    ('DELIVERY_LATE', 'OTHER', 13),
    ('DELIVERY_MISSING', 'DELIVERY_LATE', 8),
    ('DELIVERY_LATE', 'RETURN_REQUEST', 6),
    ('DEVICE_ISSUE', 'OTHER', 6),
    ('OTHER', 'DELIVERY_LATE', 6),
    ('APP_USAGE', 'DELIVERY_LATE', 5),
    ('DELIVERY_MISSING', 'OTHER', 5),
    ('ACCOUNT_ACCESS', 'OTHER', 4),
    ('ORDER_STATUS', 'OTHER', 4),
    ('OTHER', 'APP_USAGE', 4),
    ('VIDEO_STREAMING', 'DELIVERY_LATE', 4),
    ('VIDEO_STREAMING', 'OTHER', 4),
    ('DELIVERY_LATE', 'DELIVERY_MISSING', 3),
    ('ORDER_STATUS', 'DELIVERY_MISSING', 3)
]

print("\nTop Confusion Pairs Comparison:")
print(f"{'Pair':<45} {'Phase C':>8} {'Phase E':>8} {'Change':>8}")
print("-" * 70)

all_pairs = set()
for p in phaseC_pairs:
    all_pairs.add((p[0], p[1]))
for p in phaseE_pairs:
    all_pairs.add((p[0], p[1]))

for true, pred in sorted(all_pairs, key=lambda x: -1):
    c1_count = 0
    c2_count = 0
    for p in phaseC_pairs:
        if p[0] == true and p[1] == pred:
            c1_count = p[2]
            break
    for p in phaseE_pairs:
        if p[0] == true and p[1] == pred:
            c2_count = p[2]
            break
    change = c2_count - c1_count
    if change > 0:
        change_str = f"+{change}"
    elif change < 0:
        change_str = f"{change}"
    else:
        change_str = "="
    print(f"{true} -> {pred:<30} {c1_count:>8} {c2_count:>8} {change_str:>8}")

print("\nKey observations:")
print("  - DELIVERY_MISSING -> DELIVERY_LATE increased: 6 -> 8 (+2)")
print("  - DEVICE_ISSUE -> OTHER decreased: 9 -> 6 (-3)")
print("  - DELIVERY_MISSING -> OTHER decreased: 3 -> 5 (+2) [worse]")
print("  - APP_USAGE -> OTHER stayed same: 14 -> 14")
print("  - DELIVERY_LATE -> OTHER stayed same: 13 -> 13")

# =============================================================================
# SECTION 4: ERROR BREAKDOWN
# =============================================================================
print("\n" + "=" * 70)
print("SECTION 4: REMAINING ERROR BREAKDOWN (ACTUAL)")
print("=" * 70)

total_errors = 540 - 377  # 163

# From training output
ambiguous = 49
genuine_mistake = 114
low_example = 0
other = 0

print(f"\nTotal errors: {total_errors}")
print(f"\nError Categories:")
print(f"  a) Ambiguous/overlapping taxonomy: {ambiguous} ({ambiguous*100/total_errors:.1f}%)")
print(f"  b) Genuine model mistakes: {genuine_mistake} ({genuine_mistake*100/total_errors:.1f}%)")
print(f"  c) Low-example classes: {low_example} ({low_example*100/total_errors:.1f}%)")
print(f"  d) Other: {other} ({other*100/total_errors:.1f}%)")

print("\nLow-example classes in train set:")
low_classes = [
    ('CANCELLATION', 2),
    ('ORDER_MODIFY', 2),
]
for label, count in low_classes:
    print(f"  {label}: {count} train examples")

# =============================================================================
# SECTION 5: ANALYSIS
# =============================================================================
print("\n" + "=" * 70)
print("SECTION 5: ANALYSIS")
print("=" * 70)

print("""
FINDING: Phase E taxonomy cleanup DECREASED accuracy by 1.30 percentage points.

Why did accuracy decrease?

1. BOUNDARY CORRECTIONS MAY HAVE BEEN WRONG
   - Some DELIVERY_MISSING -> DELIVERY_LATE corrections may have been incorrect
   - The original labels may have been more accurate than our "refined" rules
   - e.g., "supposed to deliver today" could still mean missing, not late

2. MODEL ADAPTED TO OLD LABELS
   - The model learned patterns from Phase C labels
   - Changing labels confused the model
   - The model now sees patterns it learned as DELIVERY_MISSING labeled as DELIVERY_LATE

3. SPECIFIC CONFUSION PAIR CHANGES
   - DELIVERY_MISSING -> DELIVERY_LATE increased: 6 -> 8 (+2 errors)
   - This suggests the boundary changes made things WORSE for this pair
   - DEVICE_ISSUE -> OTHER improved: 9 -> 6 (-3 errors) - positive

CONCLUSION:
   The Phase E changes introduced more errors than they fixed.
   The original Phase C labels were more accurate than our theoretical fixes.
""")

# =============================================================================
# SECTION 6: COMPARISON TO KEY CONFUSIONS
# =============================================================================
print("\n" + "=" * 70)
print("SECTION 6: KEY CONFUSION PAIRS COMPARISON")
print("=" * 70)

print("\nPhase B identified these key confusions:")
print("  1. OTHER vs DELIVERY_LATE/DELIVERY_MISSING")
print("  2. APP_USAGE vs DEVICE_ISSUE")
print("  3. DELIVERY_LATE vs DELIVERY_MISSING vs DELIVERY_TRACKING")

print("\nDid these improve?")
print("\n  1. OTHER vs DELIVERY_LATE:")
print("     Phase C: OTHER->DELIVERY_LATE=4, DELIVERY_LATE->OTHER=13")
print("     Phase E: OTHER->DELIVERY_LATE=6, DELIVERY_LATE->OTHER=13")
print("     Status: NO IMPROVEMENT (worse)")

print("\n  2. APP_USAGE vs DEVICE_ISSUE:")
print("     Phase C: APP_USAGE->DEVICE_ISSUE not in top 15")
print("     Phase E: Similar - no significant change")
print("     Status: NO CHANGE")

print("\n  3. DELIVERY_LATE vs DELIVERY_MISSING:")
print("     Phase C: DELIVERY_LATE->DELIVERY_MISSING=4, DELIVERY_MISSING->DELIVERY_LATE=6")
print("     Phase E: DELIVERY_LATE->DELIVERY_MISSING=3, DELIVERY_MISSING->DELIVERY_LATE=8")
print("     Status: WORSE - more confusion between these classes")

print("\n  4. DEVICE_ISSUE -> OTHER:")
print("     Phase C: 9 errors")
print("     Phase E: 6 errors")
print("     Status: IMPROVED (-3 errors)")

# =============================================================================
# FINAL SUMMARY
# =============================================================================
print("\n" + "=" * 70)
print("FINAL SUMMARY")
print("=" * 70)

print("""
MODEL COMPARISON:
================

Model                         Accuracy    Delta
-------------------------------------------------
Original baseline             54.44%      -
Phase 6 TF-IDF+LinearSVC     70.56%      +16.12pp
Phase C TF-IDF+LinearSVC     71.11%      +16.67pp
Phase E (cleaned taxonomy)    69.81%      +15.37pp

PHASE E VERDICT: WORSE THAN PHASE C

The taxonomy cleanup decreased accuracy by 1.30 percentage points.
This suggests that:
1. The Phase B theoretical corrections were incorrect
2. The original labels were more accurate than our refined rules
3. Retraining on "corrected" labels hurt rather than helped

RECOMMENDATION: RETAIN PHASE C AS BEST MODEL

""")

# Save report
report = {
    'phase': 'E',
    'accuracy': phaseE_accuracy,
    'correct': 377,
    'total': 540,
    'delta_vs_phaseC': -0.0130,
    'delta_vs_phase6': -0.0067,
    'changes_applied': len(all_changes),
    'errors_total': total_errors,
    'errors_ambiguous': ambiguous,
    'errors_genuine_mistake': genuine_mistake,
    'errors_low_example': low_example,
    'conclusion': 'Taxonomy cleanup hurt accuracy - retain Phase C'
}

with open("data/cleaned/phaseE_final_report.json", 'w') as f:
    json.dump(report, f, indent=2)

print("Report saved to data/cleaned/phaseE_final_report.json")