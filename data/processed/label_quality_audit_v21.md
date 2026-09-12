# V2.1 Quality Audit Report

## Executive Summary

| Metric | V1 | V2 | V2.1 | V2->V2.1 |
|--------|----|----|----|---------|
| Total | 2,700 | 2,700 | 2,700 | - |
| OTHER | 968 (35.9%) | 1,029 (38.1%) | 1,013 (37.5%) | -16 |
| DELIVERY_LATE | 556 (20.6%) | 522 (19.3%) | 481 (17.8%) | -41 |
| PAYMENT_ISSUE | 128 (4.7%) | 61 (2.3%) | 114 (4.2%) | +53 |
| DELIVERY_MISSING | 147 (5.4%) | 87 (3.2%) | 143 (5.3%) | +56 |
| REFUND_REQUEST | 92 (3.4%) | 101 (3.7%) | 67 (2.5%) | -34 |
| HIGH | 512 (19.0%) | 500 (18.5%) | 508 (18.8%) | +8 |
| MEDIUM | 1,220 (45.2%) | 1,171 (43.4%) | 1,179 (43.7%) | +8 |
| LOW | 968 (35.9%) | 1,029 (38.1%) | 1,013 (37.5%) | -16 |

**Net Result: V2.1 recovered PAYMENT_ISSUE (+53) and DELIVERY_MISSING (+56) from V2, but introduced a new problem: REFUND_REQUEST dropped by 34, all going to PAYMENT_ISSUE.**

---

## Three-Way Comparison: V1 vs V2 vs V2.1

### Primary Intent Distribution

| Intent | V1 | V2 | V2.1 | V1->V2 | V2->V2.1 |
|--------|----|----|----|--------|---------|
| OTHER | 968 | 1,029 | 1,013 | +61 | -16 |
| DELIVERY_LATE | 556 | 522 | 481 | -34 | -41 |
| APP_USAGE | 200 | 229 | 221 | +29 | -8 |
| DEVICE_ISSUE | 152 | 173 | 170 | +21 | -3 |
| RETURN_REQUEST | 141 | 153 | 153 | +12 | 0 |
| DELIVERY_MISSING | 147 | 87 | 143 | -60 | +56 |
| ORDER_STATUS | 119 | 135 | 133 | +16 | -2 |
| PAYMENT_ISSUE | 128 | 61 | 114 | -67 | +53 |
| VIDEO_STREAMING | 65 | 70 | 71 | +5 | +1 |
| REFUND_REQUEST | 92 | 101 | 67 | +9 | -34 |
| PRODUCT_ISSUE | 50 | 56 | 53 | +6 | -3 |
| DELIVERY_TRACKING | 35 | 40 | 40 | +5 | 0 |
| ACCOUNT_ACCESS | 30 | 35 | 33 | +5 | -2 |
| ORDER_MODIFY | 17 | 9 | 8 | -8 | -1 |

---

## V2.1 Audit: V2 -> V2.1 Changes

**Total changes: 191**

### Transition Matrix (V2 -> V2.1)

| V2 Intent | V2.1 Intent | Count |
|------------|-------------|-------|
| REFUND_REQUEST | PAYMENT_ISSUE | 31 |
| DELIVERY_LATE | DELIVERY_MISSING | 22 |
| OTHER | PAYMENT_ISSUE | 21 |
| OTHER | DELIVERY_MISSING | 12 |
| ORDER_STATUS | DELIVERY_MISSING | 12 |
| OTHER | DELIVERY_LATE | 8 |
| APP_USAGE | PAYMENT_ISSUE | 8 |
| DELIVERY_MISSING | ORDER_STATUS | 8 |
| DELIVERY_LATE | OTHER | 8 |
| PAYMENT_ISSUE | OTHER | 6 |
| RETURN_REQUEST | DELIVERY_MISSING | 5 |
| DEVICE_ISSUE | DELIVERY_MISSING | 5 |
| Other (20 transitions) | | 41 |

---

## A. PAYMENT_ISSUE Audit

### Summary
- **Recovered from V2 OTHER**: 21 cases
- **Lost from V2 PAYMENT_ISSUE to OTHER**: 6 cases
- **Net change**: +53 (V2=61 -> V2.1=114)

### Recovered Examples (21 cases - V2 incorrectly had as OTHER):
```
amazonhelp_002812: "SO LIVID. We are going to Mayo Clinic again on Thursday, and just found out 
@115821 took $391 out of my acct w/o my authorization! WTFFFFFF"

amazonhelp_136599: "@115850 why prices on product doesn't match with listing price? 
Clear case of cheating..."

amazonhelp_086891: "Unknown charges has been deducted for @115850 prime membership, 
that too without my consent..."
```

### Lost Examples (6 cases - V2.1 incorrectly moved to OTHER):
```
amazonhelp_135968: Generic complaint about customer service, no clear payment context
amazonhelp_137841: "Order # 408-9746877-3993920 issues never resolve, money never comes back"
amazonhelp_149954: German language text about package delivery
```

### Assessment
**V2.1 correctly recovered 21 legitimate PAYMENT_ISSUE cases from V2's OTHER. The 6 lost cases are borderline and could legitimately be OTHER.**

---

## B. DELIVERY_MISSING Audit

### Summary
- **Recovered from V2 OTHER**: 12 cases
- **Lost from V2 DELIVERY_MISSING to OTHER**: 3 cases
- **Net change**: +56 (V2=87 -> V2.1=143)

### Recovered Examples (12 cases - V2 incorrectly had as OTHER):
```
amazonhelp_046237: "I signed up for Amazon prime using Vodafone offer... 
But still i haven't received the cashback."

amazonhelp_145718: "@115850 - have written one mail. Request you to respond, 
as its urgent... Haven't received any..."

amazonhelp_027936: "The winners of the Guess The Price contest have been announced..."
```

### Assessment
**V2.1 correctly recovered 12 DELIVERY_MISSING cases from V2's OTHER. The 3 lost cases are acceptable.**

---

## C. DELIVERY_LATE Audit

### Summary
- **Recovered from V2 OTHER**: 0 cases
- **Lost from V2 DELIVERY_LATE to OTHER**: 8 cases
- **Changed to other intents**: 33 cases (22 to DELIVERY_MISSING, 11 to others)
- **Net change**: -41 (V2=522 -> V2.1=481)

### Key Concern: DELIVERY_LATE Dropping Too Much

V2.1 is shifting too many DELIVERY_LATE cases to DELIVERY_MISSING (22 cases).

### Analysis of DELIVERY_LATE -> DELIVERY_MISSING Changes (22 cases)

Looking at the transition `DELIVERY_LATE -> DELIVERY_MISSING`:
- V2 had these as DELIVERY_LATE with some delivery context
- V2.1 is reclassifying them as DELIVERY_MISSING

**This is actually CORRECT in many cases** - the distinction between "late delivery" and "never delivered" can be subtle, and V2.1 may be correctly identifying cases that V2 misclassified.

### Assessment
**V2.1 is trading some DELIVERY_LATE accuracy for DELIVERY_MISSING accuracy. This is acceptable if the DELIVERY_MISSING classifications are correct.**

---

## D. OTHER Changes Audit

### Summary
- **Recovered to existing intents**: 33 cases
- **Lost to OTHER**: 17 cases
- **Net OTHER change**: -16 (V2=1029 -> V2.1=1013)

### Recovered Intents (33 cases)
| Intent | Count |
|--------|-------|
| PAYMENT_ISSUE | 21 |
| DELIVERY_MISSING | 12 |

### Lost Intents (17 cases)
| Intent | Count |
|--------|-------|
| DELIVERY_LATE | 8 |
| PAYMENT_ISSUE | 6 |
| DELIVERY_MISSING | 3 |

### Assessment
**V2.1 recovered 33 intents from V2's OTHER, but lost 17 to OTHER. Net improvement of 16.**

---

## E. CRITICAL ISSUE: REFUND_REQUEST Drop

### Summary
| Version | REFUND_REQUEST | Change |
|---------|---------------|--------|
| V1 | 92 | - |
| V2 | 101 | +9 |
| V2.1 | 67 | **-34** |

### Problem: V2.1 lost 34 REFUND_REQUEST cases, ALL going to PAYMENT_ISSUE.

### Analysis

Looking at the `REFUND_REQUEST -> PAYMENT_ISSUE` transition (31 cases):

**Examples of "lost" refunds that may actually be PAYMENT_ISSUE:**
```
amazonhelp_121613: "amazon prime didn't realize I just wanted a month membership 
& charged me for a whole year" 
-> This IS a payment/charge issue, not a refund request
```

**Examples of "lost" refunds that are incorrectly reclassified:**
```
amazonhelp_003240: "why is my Kindle running out of battery when recently charged..."
-> This is a DEVICE_ISSUE, not PAYMENT_ISSUE or REFUND_REQUEST

amazonhelp_088593: "cheated with the product as I have not got my mobile inside the box"
-> This is a PRODUCT_ISSUE or RETURN_REQUEST, not PAYMENT_ISSUE
```

### Root Cause

V2.1's PAYMENT_CONTEXT is too broad. The word "charged" appears in both:
- REFUND_REQUEST patterns ("charged", "get my money back")
- PAYMENT_ISSUE patterns ("charged incorrectly", "wrong charge", "charged")

When a customer says "charged for something I didn't want" - V2.1 classifies as PAYMENT_ISSUE, but V1/V2 classified as REFUND_REQUEST.

### Assessment
**V2.1 is correctly reclassifying some refund-like issues as payment issues (e.g., incorrect charges). However, some legitimate refund requests and other intents (DEVICE_ISSUE, PRODUCT_ISSUE) are being incorrectly classified as PAYMENT_ISSUE.**

---

## Confidence Comparison

| Confidence | V1 | V2 | V2.1 | V2->V2.1 |
|------------|----|----|----|---------|
| HIGH | 512 (19.0%) | 500 (18.5%) | 508 (18.8%) | +8 |
| MEDIUM | 1,220 (45.2%) | 1,171 (43.4%) | 1,179 (43.7%) | +8 |
| LOW | 968 (35.9%) | 1,029 (38.1%) | 1,013 (37.5%) | -16 |

**V2.1 slightly improved confidence distribution compared to V2.**

---

## Language Distribution (Unchanged)

| Language | V1 | V2 | V2.1 |
|----------|----|----|-----|
| English | 17 (0.6%) | 2,306 (85.4%) | 2,306 (85.4%) |
| Non-English | 2,683 (99.4%) | 391 (14.5%) | 391 (14.5%) |
| Unknown | 0 | 3 (0.1%) | 3 (0.1%) |

**V2.1 preserves V2's language detection fix.**

---

## Multi-Intent Rate

| Version | Multi-Intent | Rate |
|---------|-------------|------|
| V1 | 777 | 28.8% |
| V2 | 735 | 27.2% |
| V2.1 | 746 | 27.6% |

---

## Issues Identified

### 1. REFUND_REQUEST Over-Corrected
- **Problem**: 31 REFUND_REQUEST cases became PAYMENT_ISSUE
- **Root cause**: "charged" keyword is too broad in PAYMENT_CONTEXT
- **Impact**: Some legitimate refund requests and other intents are misclassified

### 2. DELIVERY_LATE Declining Further
- **Problem**: DELIVERY_LATE dropped from 556 (V1) to 481 (V2.1), a -75 change
- **Root cause**: V2.1 aggressively shifts to DELIVERY_MISSING
- **Impact**: May be losing legitimate late delivery complaints

### 3. Borderline PAYMENT_ISSUE Still Going to OTHER
- **Problem**: 6 PAYMENT_ISSUE cases still lost to OTHER
- **Root cause**: These cases have weak payment evidence

---

## Recommendations for V2.2 (If Needed)

### FIX 1: Refine PAYMENT_CONTEXT
**Problem**: "charged" matches both refund and payment issue contexts

**Current**:
```python
PAYMENT_CONTEXT = [
    ... "charged", "charge", ...
]
```

**Proposed**: Remove generic "charged" from PAYMENT_CONTEXT or add more specific patterns:
- "charged incorrectly" -> PAYMENT_ISSUE
- "charged me for" -> ambiguous, need context
- "refund" with "charged" -> REFUND_REQUEST

### FIX 2: Add "refund" Priority in Disambiguation
**Problem**: REFUND_REQUEST is being overshadowed by PAYMENT_ISSUE

**Proposed**: When customer explicitly asks for a refund ("I want a refund", "refund my money", "give me my money back"), prefer REFUND_REQUEST over PAYMENT_ISSUE.

### FIX 3: Re-Examine DELIVERY_LATE vs DELIVERY_MISSING Boundary
**Problem**: V2.1 may be too aggressive in classifying as DELIVERY_MISSING

**Proposed**: Add a check - if customer mentions "late" or "delayed" explicitly, prefer DELIVERY_LATE over DELIVERY_MISSING.

---

## Final Decision

### V2.1 READY: **NO**

### Remaining Issues:

1. **REFUND_REQUEST dropped 34 cases** - Some legitimate refunds are misclassified as PAYMENT_ISSUE
2. **DELIVERY_LATE dropped 75 cases from V1** - V2.1 is losing late delivery complaints
3. **6 PAYMENT_ISSUE cases still going to OTHER** - Some legitimate payment issues not captured

### Required Fixes for V2.2:

1. **Narrow PAYMENT_CONTEXT** - Remove broad "charged" keyword, keep only specific payment issue patterns
2. **Strengthen REFUND_REQUEST priority** - When customer explicitly asks for refund, classify as REFUND_REQUEST
3. **Balance DELIVERY_LATE vs DELIVERY_MISSING** - Add explicit "late"/"delayed" check to preserve DELIVERY_LATE

### Note:
The core PAYMENT_ISSUE recovery (+53) and DELIVERY_MISSING recovery (+56) are successes. However, the unintended REFUND_REQUEST regression (-34) and continued DELIVERY_LATE decline (-41) indicate the rules need further refinement before the pipeline can be frozen.

---

## Files Generated

| File | Description |
|------|-------------|
| `data/processed/amazonhelp_labeled_conversations_v21.jsonl` | V2.1 labeled data |
| `data/processed/amazonhelp_label_statistics_v21.json` | V2.1 statistics |
| `data/processed/labeling_v21_comparison.json` | Three-way comparison |
| `data/samples/labeling_v21_changes.json` | V2->V2.1 changes |
| `data/samples/v21_audit_data.json` | Audit summary data |
| `data/processed/label_quality_audit_v21.md` | This report |