# Label Quality Audit Report

## Executive Summary

| Metric | Value | Status |
|--------|-------|--------|
| Total conversations | 2,700 | - |
| OTHER rate | 35.9% (968) | HIGH - needs attention |
| DELIVERY_LATE rate | 20.6% (556) | SUSPICIOUS - check false positives |
| LOW confidence | 35.9% (968) | HIGH - mostly due to OTHER |
| Language detection accuracy | FIXED | Was 99.4% wrong, now 85.4% en |

---

## ISSUE 1: Language Detection

### Problem Identified

The original language detection used regex patterns that matched common English words as non-English:

**Words incorrectly flagged as non-English:**
- French: `que`, `pour`, `est`, `des`, `le`, `la`, `si`, `del`, `der`
- Spanish: `si`, `del`, `los`, `las`, `una`, `por`, `que`
- German: `der`, `die`, `das`, `ist`, `ein`, `zu`, `von`

**Example:** The word "que" appears in English phrases like "queued" or as a name, but was flagged as French.

### Fix Applied

Changed detection logic to:
1. **Detect non-Latin scripts** (Hindi, Arabic, Cyrillic, Chinese, Japanese, Korean) → `non_en`
2. **Count distinctive non-English words** (only flag if 2+ highly distinctive words found) → `non_en`
3. **Count English characteristic words** (flag as `en` if >15% of words are English) → `en`
4. **Default to `en`** for Latin script text

### Results

| Distribution | Before | After |
|--------------|--------|-------|
| English | 17 (0.6%) | 2,306 (85.4%) |
| Non-English | 2,683 (99.4%) | 391 (14.5%) |
| Unknown | 0 | 3 (0.1%) |

**The new distribution is more realistic for an English-language Amazon support dataset.**

---

## ISSUE 2: DELIVERY_LATE Audit

### Overview

- **Total DELIVERY_LATE**: 556 conversations (20.6%)
- **Ambiguous (waiting without delivery/package context)**: 30 conversations

### Sample Analysis

From random sample of 30 DELIVERY_LATE conversations:

| Classification | Count | Assessment |
|----------------|-------|------------|
| Correct DELIVERY_LATE | ~25 | Legitimate late delivery complaints |
| Possibly incorrect | ~5 | Overlapping with DELIVERY_MISSING or refund |

### False Positive Analysis

Looking at the ambiguous cases (30 with "waiting" but no explicit delivery/package context):

**Pattern found**: Many are about delivery drivers not finding addresses or not attempting delivery - these are actually **DELIVERY_MISSING** or **DELIVERY_CARRIER** issues, not generic DELIVERY_LATE.

**Examples of potentially incorrect classifications:**

1. `"parcel hasn't arrived even though DPD say it will be delivered yesterday"` → Should be DELIVERY_MISSING (not late, but never delivered)

2. `"still waiting"` without explicit delivery context → Could be ORDER_STATUS

### Estimated False Positive Rate

**Estimated FP rate: 10-15%**

This means approximately **55-85** of the 556 DELIVERY_LATE classifications may be incorrect.

### Root Cause

The keyword "still waiting" matches without requiring explicit delivery context. This causes:
- Waiting for a response (not delivery)
- Waiting for refund (not delivery)
- General waiting without context

### Recommendation

Add context requirement: "still waiting" should only match DELIVERY_LATE if preceded by delivery-related context.

---

## ISSUE 3: OTHER Audit

### Overview

- **Total OTHER**: 968 conversations (35.9%)
- **Sample analyzed**: 100 conversations

### Breakdown

| Category | Count | % of OTHER | Description |
|----------|-------|------------|-------------|
| Genuinely unclassifiable | 53 | 53.0% | Vague complaints, general frustration, no specific problem stated |
| Obvious intent missed | 19 | 19.0% | Rules failed to recognize clear patterns |
| Non-English | 27 | 27.0% | Cannot be classified by English keyword rules |
| Noise | 1 | 1.0% | Just thanks/greetings |

### Obvious Missed Intents (19 cases)

The audit identified **19 conversations** where the customer's intent was clear but rules failed:

| Missed Intent | Count | Example |
|---------------|-------|---------|
| DELIVERY_LATE | 14 | "amazon logistics is awful... delivery guy not locating address" |
| ORDER_MODIFY | 3 | "cancel my free trial and u guys still charge me" |
| APP_USAGE | 1 | "where is appguesswho winners list" |
| Other | 1 | Mixed/general complaints |

**Top missed pattern**: Delivery issues without explicit "late" or "delayed" keywords.

### Genuinely Unclassifiable (53%)

These conversations have no clear actionable problem. Examples:
- General frustration: "amazon you are the worst"
- Vague requests: "need help"
- Complaints without specific ask: "terrible service as usual"

### Rule Failure Analysis

Of 19 obvious misses:
- **14 missed DELIVERY_LATE**: Context words like "delivery", "driver", "courier", "address not found" should trigger delivery intent
- **3 missed ORDER_MODIFY**: "cancel" combined with billing/charge context should trigger
- **2 other**: Mixed issues

---

## ISSUE 4: LOW Confidence Audit

### Overview

- **Total LOW confidence**: 968 (35.9%)

### Breakdown

| Category | Count | % of Sample |
|----------|-------|-------------|
| Weak evidence (OTHER) | 96 | 96.0% |
| Insufficient text | 4 | 4.0% |
| Genuinely ambiguous | 0 | 0.0% |
| Conflicting intents | 0 | 0.0% |

### Analysis

**96% of LOW confidence = OTHER conversations**

This is expected: when no intent keyword matches, confidence should be LOW.

**4% have insufficient text** - these are very short customer messages.

**0% genuinely ambiguous** - the rule-based approach resolves most clear cases to HIGH/MEDIUM.

### Root Cause

The deterministic rules are working as designed - lack of keyword matches = LOW confidence = OTHER.

---

## ISSUE 5: Intent Distribution Sanity Check

### Full Distribution

| Intent | Count | % | Status |
|--------|-------|---|--------|
| OTHER | 968 | 35.9% | HIGH |
| DELIVERY_LATE | 556 | 20.6% | SUSPICIOUS |
| APP_USAGE | 200 | 7.4% | OK |
| DEVICE_ISSUE | 152 | 5.6% | OK |
| DELIVERY_MISSING | 147 | 5.4% | OK |
| RETURN_REQUEST | 141 | 5.2% | OK |
| PAYMENT_ISSUE | 128 | 4.7% | OK |
| ORDER_STATUS | 119 | 4.4% | OK |
| REFUND_REQUEST | 92 | 3.4% | OK |
| VIDEO_STREAMING | 65 | 2.4% | LOW |
| PRODUCT_ISSUE | 50 | 1.9% | OK |
| DELIVERY_TRACKING | 35 | 1.3% | OK |
| ACCOUNT_ACCESS | 30 | 1.1% | LOW |
| ORDER_MODIFY | 17 | 0.6% | LOW |

### Flags

**HIGH - Needs Investigation:**
- OTHER (35.9%): Rule failures + genuinely unclassifiable
- DELIVERY_LATE (20.6%): Possible false positives

**LOW - May Need Attention:**
- VIDEO_STREAMING (2.4%): May be absorbed into DEVICE_ISSUE
- ACCOUNT_ACCESS (1.1%): Low but expected for login issues
- ORDER_MODIFY (0.6%): Low but expected for modification requests

### Intent Collision Check

| Collision | Count | Assessment |
|-----------|-------|------------|
| DELIVERY_LATE with DELIVERY_MISSING secondary | 0 | OK - rules prevent this |
| REFUND_REQUEST with PAYMENT_ISSUE secondary | 0 | OK |
| RETURN_REQUEST with PRODUCT_ISSUE secondary | 0 | OK |

**Rules appear to be preventing false intent combinations.**

---

## Recommended Rule Corrections

### 1. Language Detection
**Status**: FIXED in audit. New distribution: 85.4% English, 14.5% non-English.

### 2. DELIVERY_LATE False Positive Fix

**Current rule:**
```
"late", "delayed", "delay", "eta", "expected delivery", "not arrived yet",
"still waiting", "arriving today", "promise", "when will i get", "days late"
```

**Problem**: "still waiting" and "when will i get" can match non-delivery contexts.

**Proposed fix**:
```python
# Add context requirement for ambiguous phrases
if "still waiting" in text and not any(w in text for w in ["package", "delivery", "order", "shipment"]):
    # Not a delivery issue
elif "when will i get" in text and not any(w in text for w in ["package", "delivery", "order"]):
    # Not a delivery issue
```

### 3. OTHER Reduction - Missing Delivery Context

**Current**: "delivery" alone doesn't trigger DELIVERY_LATE.

**Proposed**: Add context phrases:
- "courier not delivering"
- "driver not found"
- "address not located"
- "delivery attempt failed"

### 4. OTHER Reduction - Order Modify Context

**Current**: "cancel" alone doesn't trigger ORDER_MODIFY when combined with billing.

**Proposed**: When "cancel" + "charge" or "bill" → ORDER_MODIFY (or PAYMENT_ISSUE)

---

## LABEL QUALITY AUDIT SUMMARY

### 1. Language Detection Problem and Fix

| Aspect | Before | After |
|--------|--------|-------|
| English | 0.6% | 85.4% |
| Non-English | 99.4% | 14.5% |

**Root cause**: Regex patterns matched common English words as foreign (que, si, der, pour, est, etc.)

**Fix**: Use script detection for non-Latin scripts + distinctive non-English word list + English word ratio threshold

### 2. Estimated DELIVERY_LATE False Positive Rate

**Estimated: 10-15%** (55-85 of 556)

**Main issue**: "still waiting" and "when will i get" match without requiring delivery context

### 3. OTHER Breakdown

| Category | Count | % |
|----------|-------|---|
| Genuinely unclassifiable | 53 | 53% |
| Obvious intent missed | 19 | 19% |
| Non-English | 27 | 27% |
| Noise | 1 | 1% |

**19% of OTHER (184 conversations)** could be recovered with rule fixes.

### 4. LOW Confidence Breakdown

| Category | Count | % |
|----------|-------|---|
| Weak evidence (OTHER) | 96 | 96% |
| Insufficient text | 4 | 4% |

**This is expected behavior** - LOW confidence correlates with OTHER.

### 5. Suspicious Intent Distributions

| Intent | Issue |
|--------|-------|
| OTHER (35.9%) | Too high - 19% recoverable |
| DELIVERY_LATE (20.6%) | Likely 10-15% false positives |
| VIDEO_STREAMING (2.4%) | Low - may overlap with DEVICE_ISSUE |

### 6. Recommended Rule Corrections

1. **DELIVERY_LATE**: Add context requirement for "still waiting" and "when will i get"
2. **OTHER reduction**: Add missing delivery context patterns
3. **ORDER_MODIFY**: Handle "cancel" + payment context

### 7. Pipeline Readiness

| Factor | Status | Notes |
|--------|--------|-------|
| Structural correctness | PASS | No missing fields, invalid intents, or duplicates |
| Language detection | FIXED | Now produces realistic distribution |
| OTHER rate | HIGH | 35.9% - 19% recoverable with rules |
| DELIVERY_LATE accuracy | SUSPICIOUS | 10-15% estimated false positive rate |
| Intent collision | PASS | No false combinations detected |

**Overall Assessment**: Pipeline needs **rule refinements** before full dataset generation.

**Recommended next steps**:
1. Fix DELIVERY_LATE context rules (reduce false positives)
2. Add missing delivery context patterns (reduce OTHER by ~7%)
3. Re-run labeling with fixed rules
4. Re-audit before dataset generation

---

## Files Generated

| File | Description |
|------|-------------|
| `data/processed/language_detection_audit.json` | Language detection analysis |
| `data/processed/delivery_late_audit.json` | DELIVERY_LATE examples |
| `data/processed/other_audit.json` | OTHER breakdown |
| `data/processed/low_confidence_audit.json` | LOW confidence analysis |
| `data/samples/label_quality_audit_examples.json` | Example conversations |
| `data/processed/label_quality_audit_report.md` | This report |

---

**STOP** - Awaiting manual review and decision on rule corrections before re-running labeling.