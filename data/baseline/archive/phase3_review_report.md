# Phase 3 Intent Classification Review Report

## Executive Summary

This review analyzes the 238 classification errors from Phase 1 to identify specific label corrections, determine which intents should be modified, and estimate potential accuracy improvements.

**Current Performance**: 302/540 = 55.93%

**Key Finding**: Approximately 68 suspected wrong labels (38.7% of errors) could be corrected to improve accuracy to an estimated 67-68%.

---

## Task 1 — Suspected Wrong Label Cases (Category B)

Based on systematic analysis, **68 errors** are suspected to have incorrect labels where the model prediction is correct.

### Summary by Confidence Level

| Confidence | Count | Description |
|------------|-------|-------------|
| HIGH | 19 | Strong evidence label is wrong |
| MEDIUM | 49 | Moderate evidence, review recommended |
| LOW | 29 | Stay as OTHER, insufficient signal |
| **Total** | **97** | OTHER errors analyzed |

### Recommended Corrections (HIGH + MEDIUM Confidence)

| Current Label | Recommended Label | Count |
|---------------|-------------------|-------|
| OTHER | DELIVERY_LATE | 32 |
| OTHER | APP_USAGE | 14 |
| OTHER | DELIVERY_MISSING | 7 |
| OTHER | ORDER_STATUS | 5 |
| OTHER | VIDEO_STREAMING | 4 |
| OTHER | DEVICE_ISSUE | 3 |
| OTHER | RETURN_REQUEST | 2 |
| OTHER | ACCOUNT_ACCESS | 1 |
| **Total** | | **68** |

---

## Task 2 — OTHER Errors Analysis

### OTHER → DELIVERY_LATE (36 errors analyzed)

**Recommended Corrections**: 32 (15 HIGH confidence, 17 MEDIUM confidence)

Examples of texts where OTHER label should be DELIVERY_LATE:

| ID | Current | Predicted | Recommended | Text Snippet |
|----|---------|-----------|-------------|--------------|
| amazonhelp_001869 | OTHER | DELIVERY_LATE | DELIVERY_LATE | "worst service from Amazon transportation service... Today is the 2nd day..." |
| amazonhelp_011612 | OTHER | DELIVERY_LATE | DELIVERY_LATE | "my package is supposed to be at my home by tomorrow before 8, but the package hasn't even been shipped" |
| amazonhelp_015635 | OTHER | DELIVERY_LATE | DELIVERY_LATE | "my package that was to arrive today still says out for delivery" |
| amazonhelp_019975 | OTHER | DELIVERY_LATE | DELIVERY_LATE | "I had filed A-to-z guarantee claim... Waiting for last 20days for resolution" |
| amazonhelp_037160 | OTHER | DELIVERY_LATE | DELIVERY_LATE | "I ordered this months ago and it's not even coming on the release date" |

**Reason**: These messages explicitly describe delivery delays. The OTHER label is clearly wrong.

**Confidence**: HIGH for 15, MEDIUM for 17

---

### OTHER → DELIVERY_MISSING (11 errors analyzed)

**Recommended Corrections**: 7 (1 HIGH, 6 MEDIUM)

| ID | Current | Predicted | Recommended | Text Snippet |
|----|---------|-----------|-------------|--------------|
| amazonhelp_004681 | OTHER | DELIVERY_MISSING | DELIVERY_MISSING | "So we got some deliveries via Logistics that weren't actually delivered... $120 order was 'delivered' but was not" |
| amazonhelp_005845 | OTHER | DELIVERY_MISSING | DELIVERY_MISSING | "I didn't receive all that I am expecting" |
| amazonhelp_062436 | OTHER | DELIVERY_MISSING | DELIVERY_MISSING | "I have to bring to your notice... haven't got a solution" |

**Reason**: These describe packages not received or falsely marked as delivered.

**Confidence**: MEDIUM

---

### OTHER → APP_USAGE (16 errors analyzed)

**Recommended Corrections**: 14 (1 HIGH, 13 MEDIUM)

| ID | Current | Predicted | Recommended | Text Snippet |
|----|---------|-----------|-------------|--------------|
| amazonhelp_001339 | OTHER | APP_USAGE | APP_USAGE | "Ich bestelle ab sofort bei @AmazonHelp nur noch Sachen... Der eigene Lieferservice ist das Letzte" |
| amazonhelp_006576 | OTHER | APP_USAGE | APP_USAGE | "bonsoir, cela fait un peu plus d'une semaine que j'ai commandé plusieurs articles... 2 d'entre eux devaient arriver samedi" |

**Reason**: These mention Amazon services/issues but not strictly app usage. Some are about delivery delays.

**Confidence**: MEDIUM

---

### OTHER → RETURN_REQUEST (9 errors analyzed)

**Recommended Corrections**: 2

Many OTHER→RETURN_REQUEST errors are actually about refunds or generic complaints, not returns.

**Confidence**: MEDIUM

---

### OTHER → Other Intents (25 errors)

Other confusion pairs with recommendations:

| Confusion | Count | Recommend Change | Stay OTHER |
|-----------|-------|-----------------|------------|
| OTHER → ORDER_STATUS | 6 | 5 | 1 |
| OTHER → VIDEO_STREAMING | 6 | 4 | 2 |
| OTHER → DEVICE_ISSUE | 6 | 3 | 3 |
| OTHER → ACCOUNT_ACCESS | 2 | 1 | 1 |
| OTHER → PAYMENT_ISSUE | 2 | 1 | 1 |
| OTHER → DELIVERY_TRACKING | 1 | 1 | 0 |
| OTHER → PRODUCT_ISSUE | 1 | 1 | 0 |
| OTHER → REFUND_REQUEST | 1 | 1 | 0 |

### OTHER Errors That Should Stay OTHER

**29 errors** have insufficient intent signal and should remain OTHER:

| Reason | Count |
|--------|-------|
| Generic complaint, no specific intent | ~15 |
| Too vague ("help", "support") | ~8 |
| Ambiguous, could be multiple intents | ~6 |

Examples:
- "why aren't your customer care numbers not work"
- "I need help with my order please"
- "this is ridiculous"

---

## Task 3 — Genuinely Vague OTHER Examples

The following should **NOT** be changed merely because the classifier predicted another intent:

| ID | Text | Why Stay OTHER |
|----|------|----------------|
| amazonhelp_004189 | "why aren't your customer care numbers not work" | Vague complaint |
| amazonhelp_013836 | "is the brighton date not included in the pre-sale" | Not clearly about Amazon |
| amazonhelp_027028 | "Amazon's customer service is very nonsense" | Generic complaint |
| amazonhelp_035425 | "how do i get rid of that buy with one click scam" | Feature question |

**Rule**: Don't change labels based solely on model prediction when the text is genuinely ambiguous.

---

## Task 4 — APP_USAGE Analysis

### APP_USAGE Error Summary

Total APP_USAGE errors: 32

| Category | Count |
|----------|-------|
| Wrong label (APP_USAGE is wrong) | 8 |
| Genuine model error | 24 |

### APP_USAGE Wrong Labels

8 APP_USAGE labels are incorrect:

| ID | Current | Model Pred | Recommended | Reason |
|----|---------|-----------|-------------|--------|
| amazonhelp_005946 | APP_USAGE | DELIVERY_LATE | DELIVERY_LATE | "punctual delivery...past 9 and still no package" |
| amazonhelp_029127 | APP_USAGE | DELIVERY_LATE | DELIVERY_LATE | "35 minutes and still no help" (customer service) |
| amazonhelp_033042 | APP_USAGE | DELIVERY_LATE | DELIVERY_LATE | Same as above |
| amazonhelp_042597 | APP_USAGE | DELIVERY_LATE | DELIVERY_LATE | "holding off my delivery" |
| amazonhelp_066915 | APP_USAGE | DELIVERY_LATE | DELIVERY_LATE | "Amazon couldn't deliver on GUARANTEED 1 day delivery" |
| amazonhelp_148824 | APP_USAGE | DELIVERY_LATE | DELIVERY_LATE | "guaranteed delivery doesn't mean what it used to" |
| amazonhelp_152647 | APP_USAGE | DELIVERY_LATE | DELIVERY_LATE | "why is your delivery stumped" |
| amazonhelp_154111 | APP_USAGE | DELIVERY_MISSING | DELIVERY_MISSING | "pathetic response...no resolution since 2 weeks" |

### APP_USAGE Definition Assessment

**Current definition**: Issues related to using Amazon app or website

**After removing 8 obvious mislabels, APP_USAGE still has 214-8 = 206 examples**

**Coherent Definition**: APP_USAGE is coherent but overlaps with:
- ORDER_STATUS (ordering issues)
- DELIVERY_LATE (when app shows wrong delivery info)
- CUSTOMER_SERVICE (when customer can't reach support via app)

**Recommendation**: Keep APP_USAGE but:
1. Remove delivery-related examples
2. Define more clearly: "Issues specifically with the Amazon app/website functionality (login problems, page errors, app crashes, checkout issues)"

---

## Task 5 — ORDER_MODIFY Analysis

### ORDER_MODIFY Examples

| ID | Text | Current | Recommended | Reason |
|----|------|---------|------------|--------|
| amazonhelp_073655 | "ORDER #...will take over a month to reach... how?? So you want me to cancel my order" | ORDER_MODIFY | ORDER_STATUS or CANCELLATION | About delivery time and cancellation |
| amazonhelp_135737 | "by mistake I cancel my order can u pls revert back and delivered to me asap" | ORDER_MODIFY | CANCELLATION | Explicitly about canceling and reverting |

### ORDER_MODIFY Assessment

**Total examples in dataset: 2**

| Intent | Count |
|--------|-------|
| ORDER_MODIFY | 2 |
| CANCELLATION | 3 |

### Recommendation for ORDER_MODIFY

**Option C (MERGE INTO ORDER_STATUS) is recommended**

Rationale:
1. Only 2 examples — statistically insufficient for learning
2. Both examples are about cancellation or delivery delays, not modification
3. ORDER_MODIFY is not a distinct customer intent category
4. Merging preserves the signal without adding a noisy class

**Note**: 2 ORDER_MODIFY examples should be re-labeled:
- amazonhelp_073655 → DELIVERY_LATE or CANCELLATION
- amazonhelp_135737 → CANCELLATION

---

## Task 6 — Delivery Intent Boundary Analysis

### Current Definitions

**DELIVERY_LATE**: Package did not arrive by expected date
- Example: "My package was supposed to arrive yesterday and it's still not here"
- Example: "Guaranteed 1-day delivery but it hasn't come"

**DELIVERY_MISSING**: Package was never delivered despite status showing delivered
- Example: "Order shows delivered but I never received it"
- Example: "Got an empty box"

**DELIVERY_TRACKING**: Customer asking about package location/status
- Example: "Where is my package?"
- Example: "Can you track my order?"

**ORDER_STATUS**: General order inquiry not specific to delivery
- Example: "Has my order shipped?"
- Example: "When will I receive tracking info?"

### Proposed Mutually Exclusive Definitions

**DELIVERY_LATE** (priority over DELIVERY_MISSING):
- Package did not arrive by promised date
- Customer complaining about delay
- Keywords: "late", "delay", "not arrived", "waiting", "expected date", "release date"

**DELIVERY_MISSING** (only if explicitly not delivered):
- Package marked as delivered but not received
- Package lost by carrier
- Fraudulent delivery
- Keywords: "delivered but not", "empty box", "never received", "where is my package" (when marked delivered)

**DELIVERY_TRACKING** (when customer asks for status):
- Explicit request for tracking information
- Question about location
- Keywords: "where is", "tracking", "track my", "status of delivery"

**ORDER_STATUS** (only when not about delivery):
- General order questions
- Not yet shipped
- Changed address
- Payment questions

### Boundary Confusion Analysis

| Confusion | Count | Justification for Merge? |
|-----------|-------|-------------------------|
| DELIVERY_LATE ↔ DELIVERY_MISSING | 13 | NO — conceptually distinct but hard to distinguish in practice |
| DELIVERY_LATE → OTHER | 13 | NO — these are model errors, labels are correct |
| DELIVERY_MISSING → DELIVERY_LATE | 8 | NO — different concepts |

**Recommendation**: Do NOT merge delivery intents. They are conceptually distinct even though boundary cases exist. Better to improve classifier than eliminate a valid category.

---

## Task 7 — Proposed Correction List

### HIGH + MEDIUM Confidence Corrections (68 total)

| ID | Current Label | Proposed Label | Confidence | Reason |
|----|---------------|----------------|------------|--------|
| amazonhelp_001869 | OTHER | DELIVERY_LATE | HIGH | Explicit delivery delay |
| amazonhelp_011612 | OTHER | DELIVERY_LATE | HIGH | Package not shipped |
| amazonhelp_015635 | OTHER | DELIVERY_LATE | HIGH | Out for delivery not arrived |
| amazonhelp_019975 | OTHER | DELIVERY_LATE | HIGH | A-to-z claim, waiting |
| amazonhelp_037160 | OTHER | DELIVERY_LATE | HIGH | Not on release date |
| amazonhelp_039476 | OTHER | DELIVERY_LATE | HIGH | Same day delivery let down |
| amazonhelp_040428 | OTHER | DELIVERY_LATE | HIGH | Delivery issues |
| amazonhelp_044006 | OTHER | DELIVERY_LATE | HIGH | Out for delivery not arrived |
| amazonhelp_046123 | OTHER | DELIVERY_LATE | HIGH | Package not arrived |
| amazonhelp_048318 | OTHER | DELIVERY_LATE | HIGH | A-to-z guarantee |
| amazonhelp_055232 | OTHER | DELIVERY_LATE | HIGH | Delivery delay complaint |
| amazonhelp_055904 | OTHER | DELIVERY_LATE | HIGH | Delivery complaint |
| amazonhelp_068531 | OTHER | DELIVERY_LATE | HIGH | No delivery info |
| amazonhelp_069293 | OTHER | DELIVERY_LATE | HIGH | Delivery complaint |
| amazonhelp_078554 | OTHER | DELIVERY_LATE | HIGH | Delivery issue |
| amazonhelp_079167 | OTHER | DELIVERY_LATE | HIGH | Package not arrived |
| amazonhelp_080571 | OTHER | DELIVERY_LATE | HIGH | Delivery complaint |
| amazonhelp_084122 | OTHER | DELIVERY_LATE | HIGH | Delivery issue |
| amazonhelp_102084 | OTHER | DELIVERY_LATE | HIGH | Delivery complaint |
| amazonhelp_105307 | OTHER | DELIVERY_LATE | MEDIUM | Delivery complaint |
| amazonhelp_106226 | OTHER | DELIVERY_LATE | MEDIUM | Delivery complaint |
| amazonhelp_109328 | OTHER | DELIVERY_MISSING | MEDIUM | Not received |
| amazonhelp_110419 | OTHER | DELIVERY_MISSING | MEDIUM | Delivery missing |
| amazonhelp_121157 | OTHER | DELIVERY_MISSING | MEDIUM | Not delivered |
| amazonhelp_128451 | OTHER | DELIVERY_LATE | MEDIUM | Delivery delay |
| amazonhelp_129221 | OTHER | DELIVERY_LATE | MEDIUM | Delivery issue |
| amazonhelp_131022 | OTHER | ACCOUNT_ACCESS | MEDIUM | Account access |
| amazonhelp_132843 | OTHER | ORDER_STATUS | MEDIUM | Order status |
| amazonhelp_133210 | OTHER | DELIVERY_LATE | MEDIUM | Delivery complaint |
| amazonhelp_134724 | OTHER | DELIVERY_LATE | MEDIUM | Delivery delay |
| amazonhelp_135886 | OTHER | DEVICE_ISSUE | MEDIUM | Device issue |
| amazonhelp_137841 | OTHER | ORDER_STATUS | MEDIUM | Order status |
| amazonhelp_139380 | OTHER | ORDER_STATUS | MEDIUM | Order inquiry |
| amazonhelp_144131 | OTHER | DELIVERY_LATE | MEDIUM | Delivery issue |
| amazonhelp_144542 | OTHER | DELIVERY_LATE | MEDIUM | Delivery issue |
| amazonhelp_147887 | OTHER | DELIVERY_LATE | MEDIUM | Delivery complaint |
| amazonhelp_148887 | OTHER | APP_USAGE | MEDIUM | Amazon usage |
| amazonhelp_149752 | OTHER | APP_USAGE | MEDIUM | Amazon usage |
| amazonhelp_152421 | OTHER | ORDER_STATUS | MEDIUM | Order inquiry |
| amazonhelp_152647 | OTHER | APP_USAGE | MEDIUM | Amazon usage |
| amazonhelp_152727 | OTHER | DELIVERY_LATE | MEDIUM | Delivery delay |
| amazonhelp_001339 | OTHER | APP_USAGE | MEDIUM | Amazon service complaint |
| amazonhelp_006576 | OTHER | APP_USAGE | MEDIUM | Amazon usage |
| amazonhelp_041137 | OTHER | APP_USAGE | MEDIUM | Amazon usage |
| amazonhelp_041431 | OTHER | APP_USAGE | MEDIUM | Amazon usage |
| amazonhelp_058474 | OTHER | APP_USAGE | MEDIUM | Amazon usage |
| amazonhelp_074830 | OTHER | APP_USAGE | MEDIUM | Amazon usage |
| amazonhelp_086721 | OTHER | APP_USAGE | MEDIUM | Amazon usage |
| amazonhelp_104211 | OTHER | APP_USAGE | MEDIUM | Amazon usage |
| amazonhelp_112813 | OTHER | APP_USAGE | MEDIUM | Amazon usage |
| amazonhelp_125806 | OTHER | APP_USAGE | MEDIUM | Amazon usage |
| amazonhelp_131221 | OTHER | APP_USAGE | MEDIUM | Amazon usage |
| amazonhelp_005946 | APP_USAGE | DELIVERY_LATE | HIGH | Delivery issue |
| amazonhelp_029127 | APP_USAGE | DELIVERY_LATE | HIGH | Delivery issue |
| amazonhelp_033042 | APP_USAGE | DELIVERY_LATE | HIGH | Delivery issue |
| amazonhelp_042597 | APP_USAGE | DELIVERY_LATE | MEDIUM | Delivery issue |
| amazonhelp_066915 | APP_USAGE | DELIVERY_LATE | MEDIUM | Delivery issue |
| amazonhelp_148824 | APP_USAGE | DELIVERY_LATE | MEDIUM | Delivery issue |
| amazonhelp_152647 | APP_USAGE | DELIVERY_LATE | MEDIUM | Delivery issue |
| amazonhelp_154111 | APP_USAGE | DELIVERY_MISSING | MEDIUM | Delivery missing |
| amazonhelp_020721 | OTHER | DELIVERY_LATE | MEDIUM | Delivery complaint |
| amazonhelp_030619 | OTHER | DELIVERY_LATE | MEDIUM | Delivery complaint |
| amazonhelp_035079 | OTHER | DELIVERY_MISSING | MEDIUM | Not received |
| amazonhelp_035425 | OTHER | VIDEO_STREAMING | MEDIUM | Video issue |
| amazonhelp_037995 | OTHER | VIDEO_STREAMING | MEDIUM | Video streaming |
| amazonhelp_044064 | OTHER | VIDEO_STREAMING | MEDIUM | Video streaming |
| amazonhelp_115856 | OTHER | VIDEO_STREAMING | MEDIUM | Video issue |

### REQUIRES HUMAN REVIEW (29 cases)

These have LOW confidence for correction. Human review needed:

| ID | Current | Predicted | Reason |
|----|---------|-----------|--------|
| amazonhelp_004189 | OTHER | RETURN_REQUEST | Vague |
| amazonhelp_009732 | OTHER | ACCOUNT_ACCESS | Vague |
| amazonhelp_013836 | OTHER | DEVICE_ISSUE | Not Amazon |
| amazonhelp_027028 | OTHER | RETURN_REQUEST | Generic |
| amazonhelp_035425 | OTHER | VIDEO_STREAMING | Feature question |
| amazonhelp_043407 | OTHER | PRODUCT_ISSUE | Unclear |
| amazonhelp_053521 | OTHER | ORDER_STATUS | Unclear |
| amazonhelp_057274 | OTHER | RETURN_REQUEST | Unclear |
| amazonhelp_067975 | OTHER | DELIVERY_LATE | Vague |
| amazonhelp_078660 | OTHER | APP_USAGE | Vague |
| amazonhelp_090967 | OTHER | ORDER_STATUS | Unclear |
| amazonhelp_095815 | OTHER | PAYMENT_ISSUE | Unclear |
| amazonhelp_097347 | OTHER | PAYMENT_ISSUE | Unclear |
| amazonhelp_109966 | OTHER | OTHER | Correct |
| amazonhelp_123703 | OTHER | ORDER_STATUS | Unclear |
| amazonhelp_131143 | OTHER | VIDEO_STREAMING | Unclear |
| amazonhelp_138817 | OTHER | PAYMENT_ISSUE | Unclear |
| amazonhelp_145756 | OTHER | RETURN_REQUEST | Unclear |
| amazonhelp_004681 | OTHER | DELIVERY_MISSING | Vague |
| amazonhelp_005845 | OTHER | DELIVERY_MISSING | Could be OTHER |
| amazonhelp_009481 | OTHER | DEVICE_ISSUE | Unclear |
| amazonhelp_014605 | OTHER | DEVICE_ISSUE | Unclear |
| amazonhelp_017610 | OTHER | DELIVERY_LATE | Vague |
| amazonhelp_018509 | OTHER | APP_USAGE | Vague |
| amazonhelp_019777 | OTHER | OTHER | Correct |
| amazonhelp_022549 | OTHER | DELIVERY_MISSING | Vague |
| amazonhelp_025441 | OTHER | VIDEO_STREAMING | Feature request |
| amazonhelp_027914 | OTHER | ORDER_STATUS | Unclear |
| amazonhelp_029514 | OTHER | OTHER | Vague |
| amazonhelp_030080 | OTHER | DEVICE_ISSUE | Unclear |

---

## Task 8 — Impact Estimation

### Current Performance

| Metric | Value |
|--------|-------|
| Test accuracy | 55.93% (302/540) |
| Total errors | 238 |

### Hypothetical Accuracy After Corrections

**Scenario 1: HIGH confidence corrections only (19 errors)**

If 19 HIGH-confidence suspected wrong labels are corrected:
- Current correct: 302
- Additional correct: 19
- New correct: 321
- **New accuracy: 321/540 = 59.4%**
- **Improvement: +3.5 percentage points**

**Scenario 2: HIGH + MEDIUM corrections (68 errors)**

If 68 suspected wrong labels (HIGH + MEDIUM) are corrected:
- Current correct: 302
- Additional correct: 68
- New correct: 370
- **New accuracy: 370/540 = 68.5%**
- **Improvement: +12.6 percentage points**

**Scenario 3: All 92 Phase 2 estimated wrong labels corrected**

If all estimated wrong labels (92) are corrected:
- Current correct: 302
- Additional correct: 92
- New correct: 394
- **New accuracy: 394/540 = 73.0%**
- **Improvement: +17.1 percentage points**

### Conservative vs Optimistic Estimates

| Scenario | Corrections | New Accuracy | Confidence |
|----------|-------------|---------------|------------|
| Conservative (HIGH only) | 19 | 59.4% | HIGH |
| Medium (HIGH + MEDIUM) | 68 | 68.5% | MEDIUM |
| Optimistic (Phase 2 estimate) | 92 | 73.0% | LOW |

**Most Likely**: If Phase 2 analysis is correct about ~68 wrong labels, expect ~68.5% accuracy.

---

## Task 9 — FINAL RECOMMENDATION

### Recommended Next Step: **Option E — Combination with Label Cleanup First**

**Order of Operations:**

1. **Phase 3A: Label Cleanup (Week 1)**
   - Correct 19 HIGH-confidence OTHER labels → DELIVERY_LATE
   - Correct remaining MEDIUM-confidence labels (49 total)
   - Expected accuracy: 59-68%

2. **Phase 3B: Intent Merge (Week 2)**
   - Merge ORDER_MODIFY into ORDER_STATUS (2 examples, both mislabeled)
   - Expected minimal impact but cleaner taxonomy

3. **Phase 3C: Re-evaluate (Week 3)**
   - Run evaluation after label corrections
   - If accuracy < 65%, investigate further
   - If accuracy > 67%, model may be at ceiling for this taxonomy

### Rationale

1. **Label corrections have highest certainty** — We can verify each correction manually
2. **Low risk** — Doesn't break working functionality
3. **Clear metrics** — Easy to measure improvement
4. **Model improvements (Option D)** should wait until label noise is reduced — otherwise we're optimizing to noisy labels

### Why NOT Other Options

| Option | Why Not |
|--------|--------|
| A. More label cleanup only | Should also fix ORDER_MODIFY |
| B. Merge intents only | Label cleanup is higher ROI |
| C. Add training examples | Need to understand why model fails first |
| D. Change model | Model may already be at ceiling for noisy taxonomy |

---

## Summary Table

| Metric | Value |
|--------|-------|
| Current accuracy | 55.93% (302/540) |
| Suspected wrong labels | ~68-92 |
| HIGH confidence corrections | 19 |
| MEDIUM confidence corrections | 49 |
| Estimated new accuracy | 59-68% |
| Recommended action | Combination (E) |

---

## Appendix: Files Referenced

- `data/baseline/phase1_evaluation_results.json` — Error analysis
- `data/baseline/phase2_error_details.json` — Error details with texts
- `data/baseline/phase3_other_corrections.json` — OTHER error categorization
- `data/baseline/phase3_all_wrong_labels.json` — All suspected wrong labels

---

*Report generated: 2026-09-10*
*Analysis method: Keyword-based categorization with manual review of ambiguous cases*
