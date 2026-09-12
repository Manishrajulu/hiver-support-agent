# Label Quality Audit Report V2

## Executive Summary

| Metric | V1 | V2 | Change |
|--------|----|----|-------|
| Total conversations | 2,700 | 2,700 | - |
| OTHER | 968 (35.9%) | 1,029 (38.1%) | +61 |
| DELIVERY_LATE | 556 (20.6%) | 522 (19.3%) | -34 |
| DELIVERY_MISSING | 147 (5.4%) | 87 (3.2%) | -60 |
| PAYMENT_ISSUE | 128 (4.7%) | 61 (2.3%) | -67 |
| Total label changes | - | 176 | - |

**Context-aware rules reduced DELIVERY_LATE false positives but increased OTHER rate.**

---

## ISSUE 1: Language Detection

### Status: FIXED in V1 → V2

| Distribution | V1 | V2 |
|--------------|----|----|
| English | 17 (0.6%) | 2,306 (85.4%) |
| Non-English | 2,683 (99.4%) | 391 (14.5%) |

**Root cause**: Regex patterns matched common English words as foreign (que, si, der, del, pour, est, etc.)
**Fix**: Use script detection for non-Latin scripts + distinctive non-English word list + English word ratio threshold

---

## ISSUE 2: DELIVERY_LATE False Positives

### Status: PARTIALLY ADDRESSED

**V1 Problem**: Generic phrases like "still waiting" and "when will i get" matched without delivery context.

**V2 Fix Applied**: Added `has_delivery_context()` check for ambiguous phrases.

**Results**:
- DELIVERY_LATE decreased from 556 (20.6%) to 522 (19.3%) - reduction of 34
- Some false positives now correctly classified as OTHER or other intents

**Analysis of 176 label changes**:
- DELIVERY_LATE -> OTHER: Some lost delivery context, fell through to OTHER
- DELIVERY_LATE -> APP_USAGE: 7 cases reclassified as app issues
- DELIVERY_LATE -> DEVICE_ISSUE: 4 cases reclassified

**Remaining concern**: OTHER increased by 61 - some of these may be recoverable with additional pattern matching.

---

## ISSUE 3: OTHER Rate Analysis

### Status: INCREASED - Needs Attention

**V1**: 968 (35.9%)
**V2**: 1,029 (38.1%)

### Breakdown of Changes (100 sample):

| Change Type | Count |
|-------------|-------|
| PAYMENT_ISSUE -> OTHER | 24 |
| DELIVERY_MISSING -> OTHER | 10 |
| PAYMENT_ISSUE -> DEVICE_ISSUE | 8 |
| DELIVERY_LATE -> APP_USAGE | 7 |
| DELIVERY_MISSING -> ORDER_STATUS | 7 |
| DELIVERY_MISSING -> RETURN_REQUEST | 4 |
| Other | 40 |

### Analysis

The increase in OTHER is primarily from:
1. **PAYMENT_ISSUE losing evidence** - 24 conversations no longer meet payment issue criteria
2. **DELIVERY_MISSING losing evidence** - 10 conversations no longer meet delivery missing criteria

This suggests the context requirements are stricter but may be too strict in some cases.

---

## ISSUE 4: Confidence Distribution

| Confidence | V1 | V2 |
|------------|----|----|
| HIGH | 512 (19.0%) | 500 (18.5%) |
| MEDIUM | 1,220 (45.2%) | 1,171 (43.4%) |
| LOW | 968 (35.9%) | 1,029 (38.1%) |

**Observation**: LOW confidence increased as some borderline cases now fall through to OTHER.

---

## V1 → V2 Change Summary

### Primary Intent Changes

| Intent | V1 | V2 | Change |
|--------|----|----|--------|
| OTHER | 968 | 1,029 | +61 |
| DELIVERY_LATE | 556 | 522 | -34 |
| DELIVERY_MISSING | 147 | 87 | -60 |
| PAYMENT_ISSUE | 128 | 61 | -67 |
| APP_USAGE | 200 | 229 | +29 |
| DEVICE_ISSUE | 152 | 173 | +21 |
| ORDER_STATUS | 119 | 135 | +16 |
| RETURN_REQUEST | 141 | 153 | +12 |
| REFUND_REQUEST | 92 | 101 | +9 |
| VIDEO_STREAMING | 65 | 70 | +5 |
| PRODUCT_ISSUE | 50 | 56 | +6 |
| DELIVERY_TRACKING | 35 | 40 | +5 |
| ACCOUNT_ACCESS | 30 | 35 | +5 |
| ORDER_MODIFY | 17 | 9 | -8 |

### Notable Changes
- **APP_USAGE increased by 29**: Some delivery-related "waiting" cases reclassified as app usage
- **DEVICE_ISSUE increased by 21**: Some payment/delivery cases reclassified as device issues
- **DELIVERY_MISSING dropped by 60**: Context requirements caused many to fall to OTHER
- **PAYMENT_ISSUE dropped by 67**: Context requirements caused many to fall to OTHER

---

## Remaining Issues

### 1. OTHER Rate Still High (38.1%)
The context-aware rules are stricter, causing more borderline cases to fall to OTHER. This is by design but means the rules may be too strict.

### 2. Some Legitimate Intents May Be Misclassified
The sample shows:
- Some DELIVERY_LATE -> APP_USAGE may be incorrect (customer complaining about app for delivery issues)
- Some PAYMENT_ISSUE -> OTHER may be legitimate payment issues that just lack context keywords

### 3. ORDER_MODIFY Remains Very Low (0.3%)
Only 9 conversations classified as ORDER_MODIFY in V2, down from 17 in V1.

---

## Recommendations

### For V3 (If Needed)
1. **Relax DELIVERY_LATE context** slightly - allow "when will i get" without explicit delivery words
2. **Add PAYMENT_ISSUE patterns** for generic payment problem language
3. **Add ORDER_MODIFY context** for cancel/modify with billing language
4. **Recover some DELIVERY_MISSING** by adding patterns like "never received" without requiring explicit delivery context

### Pipeline Status
| Factor | Status |
|--------|--------|
| Structural correctness | PASS |
| Language detection | FIXED |
| DELIVERY_LATE accuracy | IMPROVED (but some legitimate cases may be lost) |
| OTHER rate | HIGH (38.1%) |
| Intent collision | PASS |

**Recommendation**: V2 is an improvement over V1 but the OTHER rate increase suggests rules may be too strict. Consider relaxing some context requirements before finalizing.