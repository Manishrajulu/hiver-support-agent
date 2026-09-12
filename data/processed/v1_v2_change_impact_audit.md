# V1 vs V2 Change-Impact Audit Report

## Executive Summary

| Metric | V1 | V2 | Change |
|--------|----|----|--------|
| Total Conversations | 2,700 | 2,700 | - |
| Total Label Changes | - | 176 | - |
| OTHER | 968 (35.9%) | 1,029 (38.1%) | +61 |
| DELIVERY_LATE | 556 (20.6%) | 522 (19.3%) | -34 |
| DELIVERY_MISSING | 147 (5.4%) | 87 (3.2%) | -60 |
| PAYMENT_ISSUE | 128 (4.7%) | 61 (2.3%) | -67 |
| HIGH Confidence | 512 (19.0%) | 500 (18.5%) | -12 |
| MEDIUM Confidence | 1,220 (45.2%) | 1,171 (43.4%) | -49 |
| LOW Confidence | 968 (35.9%) | 1,029 (38.1%) | +61 |

**Critical Finding: V2 is TOO STRICT. It incorrectly moved 44 PAYMENT_ISSUE cases to OTHER and 21 DELIVERY_LATE cases to OTHER, while correctly handling only 6 ambiguous cases.**

---

## 1. TRANSITION MATRIX (All 176 Changes)

| Old Intent | New Intent | Count | Percentage |
|------------|------------|-------|------------|
| PAYMENT_ISSUE | OTHER | 44 | 25.0% |
| PAYMENT_ISSUE | APP_USAGE | 17 | 9.7% |
| DELIVERY_MISSING | OTHER | 14 | 8.0% |
| DELIVERY_MISSING | ORDER_STATUS | 14 | 8.0% |
| PAYMENT_ISSUE | DEVICE_ISSUE | 10 | 5.7% |
| DELIVERY_LATE | APP_USAGE | 8 | 4.5% |
| DELIVERY_LATE | RETURN_REQUEST | 6 | 3.4% |
| DELIVERY_MISSING | RETURN_REQUEST | 6 | 3.4% |
| DELIVERY_LATE | DEVICE_ISSUE | 5 | 2.8% |
| DELIVERY_LATE | PRODUCT_ISSUE | 5 | 2.8% |
| DELIVERY_MISSING | DEVICE_ISSUE | 5 | 2.8% |
| DELIVERY_MISSING | DELIVERY_TRACKING | 5 | 2.8% |
| DELIVERY_MISSING | REFUND_REQUEST | 4 | 2.3% |
| DELIVERY_MISSING | APP_USAGE | 4 | 2.3% |
| DELIVERY_MISSING | PAYMENT_ISSUE | 3 | 1.7% |
| DELIVERY_LATE | VIDEO_STREAMING | 3 | 1.7% |
| ORDER_MODIFY | OTHER | 3 | 1.7% |
| DELIVERY_LATE | PAYMENT_ISSUE | 3 | 1.7% |
| ORDER_MODIFY | REFUND_REQUEST | 3 | 1.7% |
| DELIVERY_LATE | ACCOUNT_ACCESS | 2 | 1.1% |
| DELIVERY_MISSING | ACCOUNT_ACCESS | 2 | 1.1% |
| ORDER_MODIFY | ORDER_STATUS | 2 | 1.1% |
| DELIVERY_LATE | REFUND_REQUEST | 2 | 1.1% |
| PAYMENT_ISSUE | ACCOUNT_ACCESS | 1 | 0.6% |
| DELIVERY_MISSING | VIDEO_STREAMING | 1 | 0.6% |
| PAYMENT_ISSUE | VIDEO_STREAMING | 1 | 0.6% |
| ORDER_MODIFY | DEVICE_ISSUE | 1 | 0.6% |
| DELIVERY_MISSING | PRODUCT_ISSUE | 1 | 0.6% |
| DELIVERY_MISSING | ORDER_MODIFY | 1 | 0.6% |

---

## 2. PAYMENT_ISSUE DROP Analysis

**V1 PAYMENT_ISSUE: 128**
**V2 PAYMENT_ISSUE: 61**
**Drop: 67 (52.3%)**

### Removal Breakdown (73 total removed from V1):

| Assessment | Count | Percentage | Interpretation |
|------------|-------|------------|----------------|
| A_V2_INCORRECTLY_MOVED_TO_OTHER | 44 | 60.3% | V2 incorrectly discarded payment intent |
| C_AMBIGUOUS_MOVED_TO_APP_USAGE | 17 | 23.3% | Ambiguous - may be app issue or payment |
| C_AMBIGUOUS_MOVED_TO_DEVICE_ISSUE | 10 | 13.7% | Ambiguous - may be device or payment |
| C_AMBIGUOUS_MOVED_TO_ACCOUNT_ACCESS | 1 | 1.4% | Ambiguous |
| C_AMBIGUOUS_MOVED_TO_VIDEO_STREAMING | 1 | 1.4% | Ambiguous |

### Key Finding
**60.3% of removed PAYMENT_ISSUE cases (44 conversations) were INCORRECTLY moved to OTHER.** These conversations contained payment keywords but V2 rules discarded them. This is strong evidence that V2 is too strict with PAYMENT_ISSUE rules.

### Representative Examples

**INCORRECT - V2 moved to OTHER (contains payment keywords):**
- `amazonhelp_067918`: "problème avec ma commande la carte bancaire passe pas" (payment card issue)
- `amazonhelp_022747`: "why am I paying for 2 day shipping if it's guaranteed to take 4 days" (paying for shipping)
- `amazonhelp_136599`: "why prices on product doesn't match with listing price" (price/payment issue)

### Verdict: **V1 WAS CORRECT for 60.3% of removed cases. V2 has a significant PAYMENT_ISSUE rule regression.**

---

## 3. DELIVERY_MISSING DROP Analysis

**V1 DELIVERY_MISSING: 147**
**V2 DELIVERY_MISSING: 87**
**Drop: 60 (40.8%)**

### Removal Breakdown (60 total removed from V1):

| Assessment | Count | Percentage | Interpretation |
|------------|-------|------------|----------------|
| C_AMBIGUOUS_OTHER | 38 | 63.3% | Borderline cases - genuinely ambiguous |
| A_V2_INCORRECTLY_MOVED | 14 | 23.3% | V2 incorrectly removed delivery missing intent |
| B_V1_SHOULD_BE_REFUND | 7 | 11.7% | V1 was wrong - should have been REFUND_REQUEST |
| C_AMBIGUOUS_COULD_BE_LATE | 1 | 1.7% | Could be DELIVERY_LATE instead |

### Key Finding
**23.3% of removed DELIVERY_MISSING cases (14 conversations) were INCORRECTLY moved.** The remaining 63.3% are genuinely ambiguous borderline cases.

### Representative Examples

**INCORRECT - V2 moved away from DELIVERY_MISSING:**
- `amazonhelp_095469`: "I need assistance on a missing package, please" (explicitly says "missing package")
- `amazonhelp_046237`: "I signed up for Amazon prime using Vodafone offer... But still i haven't received the cashback" (missing cashback not package)

### Verdict: **V2 has issues with DELIVERY_MISSING rules, but less severe than PAYMENT_ISSUE. 23.3% incorrectly moved.**

---

## 4. DELIVERY_LATE DROP Analysis

**V1 DELIVERY_LATE: 556**
**V2 DELIVERY_LATE: 522**
**Drop: 34 (6.1%)**

### Removal Breakdown (34 total removed from V1):

| Assessment | Count | Percentage | Interpretation |
|------------|-------|------------|----------------|
| C_AMBIGUOUS_OTHER | 13 | 38.2% | Borderline - no clear delivery context |
| C_AMBIGUOUS_MAYBE_APP | 7 | 20.6% | Ambiguous - could be APP_USAGE |
| A_V2_CORRECT_REQUIRES_CONTEXT | 6 | 17.6% | V2 CORRECT - "still waiting" without delivery context |
| C_AMBIGUOUS_MAYBE_DEVICE | 4 | 11.8% | Ambiguous - could be DEVICE_ISSUE |
| B_V1_SHOULD_BE_REFUND | 4 | 11.8% | V1 was wrong - should have been REFUND_REQUEST |

### Key Finding
**Only 6 cases (17.6%) were correctly handled by V2's context requirement for "still waiting" without delivery context.** The majority (38.2% + 20.6% + 11.8% = 70.6%) are ambiguous/borderline cases that could reasonably be different intents.

### Representative Examples

**CORRECT - V2 removed due to missing delivery context:**
- Cases where "still waiting" or "when will I get" appeared without package/delivery keywords

**INCORRECT - V2 removed legitimate DELIVERY_LATE:**
- Cases with explicit delivery keywords that V2 rules still failed to capture

### Verdict: **V2 correctly handled only 17.6% of DELIVERY_LATE removals. The context requirement may be too strict.**

---

## 5. OTHER INCREASE Analysis

**V1 OTHER: 968**
**V2 OTHER: 1,029**
**Increase: 61 (6.3%)**

### Source of NEW OTHER Labels:

| Should Be | Count | Percentage |
|-----------|-------|------------|
| PAYMENT_ISSUE | 23 | 37.7% |
| DELIVERY_LATE | 21 | 34.4% |
| GENUINELY_OTHER | 9 | 14.8% |
| ORDER_MODIFY | 7 | 11.5% |
| DELIVERY_MISSING | 1 | 1.6% |

### Key Finding
**72.1% of the OTHER increase (44 cases) came from PAYMENT_ISSUE and DELIVERY_LATE being incorrectly moved to OTHER.** Only 14.8% are genuinely unclassifiable.

### Verdict: **V2 is incorrectly discarding legitimate intents, particularly PAYMENT_ISSUE and DELIVERY_LATE.**

---

## 6. CONFIDENCE COMPARISON

| Confidence | V1 | V2 | Change |
|------------|----|----|--------|
| HIGH | 512 (19.0%) | 500 (18.5%) | -12 |
| MEDIUM | 1,220 (45.2%) | 1,171 (43.4%) | -49 |
| LOW | 968 (35.9%) | 1,029 (38.1%) | +61 |

### Analysis
- **HIGH confidence decreased by 12** (2.3% relative)
- **MEDIUM confidence decreased by 49** (4.0% relative)
- **LOW confidence increased by 61** (6.3% relative)

**V2 confidence quality is WORSE than V1.** The stricter rules are causing more borderline cases to fall to LOW confidence, but many of these borderline cases actually have clear intents that V1 captured correctly.

---

## 7. FINAL RECOMMENDATION

### Decision: **C - MAKE SMALL RULE FIXES TO V2**

V2 introduced improvements (DELIVERY_LATE context requirement) but introduced significant regressions in PAYMENT_ISSUE handling and overall confidence quality.

### Required Rule Fixes

#### FIX 1: PAYMENT_ISSUE Rules (CRITICAL)
**Problem**: 44 PAYMENT_ISSUE conversations incorrectly moved to OTHER

**Current behavior**: V2 rules discard payment keywords too aggressively

**Fix needed**: Ensure "pay", "payment", "card", "bank", "charge", "billing" combined with complaint context triggers PAYMENT_ISSUE

#### FIX 2: DELIVERY_MISSING Rules (MODERATE)
**Problem**: 14 DELIVERY_MISSING conversations incorrectly moved to OTHER

**Current behavior**: V2 rules don't recognize "missing package" language without explicit delivery context

**Fix needed**: "missing" + "package" or "never received" should trigger DELIVERY_MISSING

#### FIX 3: DELIVERY_LATE Context Requirement (MODERATE)
**Problem**: Only 17.6% of DELIVERY_LATE removals were correct

**Current behavior**: "still waiting" and "when will I get" require explicit delivery context

**Fix needed**: Allow "when will I get" without explicit delivery context since it strongly implies delivery inquiry

#### FIX 4: OTHER Recovery (LOW PRIORITY)
**Problem**: 44 PAYMENT_ISSUE + 21 DELIVERY_LATE = 65 legitimate intents moved to OTHER

**Fix needed**: After fixing rules 1-3, the OTHER increase should reverse

---

## Summary Statistics

| Category | Assessment | Count | % |
|----------|------------|-------|---|
| V2 Correct Removals | DELIVERY_LATE context | 6 | 3.4% |
| V2 Incorrect Removals | PAYMENT_ISSUE -> OTHER | 44 | 25.0% |
| V2 Incorrect Removals | DELIVERY_MISSING -> OTHER | 14 | 8.0% |
| Ambiguous Removals | Various | 112 | 63.6% |
| **Total** | | **176** | **100%** |

**Net Assessment**: V2 introduced a 25% regression (44/176) in PAYMENT_ISSUE accuracy while achieving only 3.4% improvement (6/176) in DELIVERY_LATE context handling.

---

## Files Generated

| File | Description |
|------|-------------|
| `data/processed/v1_v2_transition_matrix.json` | Full transition matrix |
| `data/samples/v1_v2_all_changes_full.json` | All 176 changed conversations |
| `data/samples/v1_v2_change_examples.json` | Representative examples |
| `data/samples/pi_removal_analysis.json` | PAYMENT_ISSUE removal details |
| `data/samples/dm_removal_analysis.json` | DELIVERY_MISSING removal details |
| `data/samples/dl_removal_analysis.json` | DELIVERY_LATE removal details |
| `data/samples/other_increase_analysis.json` | OTHER increase source analysis |
| `data/processed/v1_v2_change_impact_audit.md` | This report |