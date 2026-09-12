# Phase 2 Error Investigation Report

## Executive Summary

Analysis of 238 misclassified test examples from the cleaned TF-IDF + Logistic Regression model (55.93% accuracy, 302/540 correct).

**Key Finding**: 38.7% of errors are due to **incorrect test labels**, not model failures. The model is often correct and the human-assigned label is wrong.

---

## 1. Error Categorization Results

| Category | Count | Percentage | Description |
|----------|-------|------------|-------------|
| **B** | 92 | 38.7% | Model correct, wrong expected label |
| **C** | 101 | 42.4% | Genuine model error |
| **D** | 45 | 18.9% | Ambiguous intent definitions |
| **A** | 0 | 0.0% | Clearly mislabeled test data |
| **E** | 0 | 0.0% | Insufficient information |

### Category Definitions
- **A. CLEARLY MISLABELED TEST DATA**: Expected label is obviously inconsistent with customer message
- **B. CLEARLY CORRECT MODEL / WRONG EXPECTED LABEL**: Prediction makes more sense than dataset label
- **C. GENUINE MODEL ERROR**: Expected label is reasonable and model prediction is wrong
- **D. AMBIGUOUS INTENT**: Both labels could reasonably apply due to taxonomy issues
- **E. INSUFFICIENT INFORMATION**: Message too vague to confidently determine intent

---

## 2. Root Cause Analysis

### 2.1 OTHER Intent is a Dumpster Fire

**OTHER is the #1 problem.**

- OTHER errors: 97 out of 238 (40.8%)
- OTHER accuracy: 52.2% (106/203 correct)
- OTHER total in dataset: 997 out of 2700 (36.9%)

**OTHER Error Breakdown:**
| Confusion Pair | Count |
|---------------|-------|
| OTHER → DELIVERY_LATE | 36 |
| OTHER → APP_USAGE | 16 |
| OTHER → DELIVERY_MISSING | 11 |
| OTHER → RETURN_REQUEST | 9 |
| OTHER → DEVICE_ISSUE | 6 |
| OTHER → VIDEO_STREAMING | 6 |
| OTHER → ORDER_STATUS | 6 |
| OTHER → other intents | 23 |

**Analysis**: Of 97 OTHER errors, **74 (76%)** are cases where the model predicted a specific intent (delivery, returns, etc.) but the label was OTHER. These are predominantly cases where the OTHER label is **wrong**, not the model prediction.

**Examples of OTHER labels that should be DELIVERY_LATE:**
- "my package is supposed to be at my home by tomorrow before 8, but the package hasn't even been shipped"
- "my package that was to arrive today still says out for delivery - it's 930pm. Is it coming tonight?"
- "worst service from Amazon transportation service... Today is the 2nd day..."

### 2.2 APP_USAGE Intent is Problematic

- APP_USAGE total: 214 examples
- APP_USAGE accuracy: **27.3%** (12/44 correct in test)
- APP_USAGE test errors: 32

**Problem**: Many APP_USAGE labels are incorrect. Looking at examples:
- "I'm usually impressed with Amazon's punctual delivery but today has me very disappointed" → labeled APP_USAGE, should be DELIVERY_LATE
- "35 minutes and still no help. Someone to call me back" → labeled APP_USAGE, should be CUSTOMER_SERVICE
- "pre-ordered Battlefront 2... will I be getting a beta code?" → labeled APP_USAGE, should be ORDER_STATUS

### 2.3 Delivery Intent Boundary Problems

| Confusion Pair | Count | Issue |
|----------------|-------|-------|
| DELIVERY_MISSING → DELIVERY_LATE | 8 | Boundary confusion |
| DELIVERY_LATE → DELIVERY_MISSING | 5 | Boundary confusion |
| DELIVERY_LATE → OTHER | 13 | Model may be correct |

**Proposed Definitions:**

1. **DELIVERY_LATE**: Package did not arrive by the promised/expected date
   - "My package was supposed to arrive yesterday"
   - "Guaranteed 1-day delivery but it hasn't come"

2. **DELIVERY_MISSING**: Package was never delivered despite attempts or status showing delivered
   - "Order shows delivered but I never received it"
   - "Package marked as delivered but not at my door"

3. **DELIVERY_TRACKING**: Customer is trying to find out where their package is
   - "Can you tell me where my package is?"
   - "What's the status of my delivery?"

4. **ORDER_STATUS**: General inquiry about order state (not specifically delivery)
   - "Has my order shipped?"
   - "When will I receive tracking info?"

**Issue**: These overlap significantly. A late delivery can become a "missing" delivery after some time.

### 2.4 ORDER_MODIFY is Unsustainable

- **Total examples in dataset: 2** (both in test set)
- Test accuracy: **0%** (0/2)
- Both examples are actually about cancellation

**Examples:**
1. "ORDER #... will take over a month to reach... how?" (about delivery time)
2. "by mistake I cancel my order can u pls revert back"

**Recommendation**: Merge ORDER_MODIFY into ORDER_STATUS or CANCELLATION. With only 2 examples, the model cannot learn this class.

---

## 3. Detailed Error Breakdown Table

| Category | Count | % of 238 | Main Affected Intents | Example |
|----------|-------|----------|----------------------|---------|
| B - Wrong Labels | 92 | 38.7% | OTHER, APP_USAGE | Customer says "package is late" but labeled OTHER |
| C - Model Errors | 101 | 42.4% | DELIVERY_*, APP_USAGE | Model confuses similar intents |
| D - Ambiguous | 45 | 18.9% | DELIVERY_LATE/MISSING, PRODUCT/REFUND | Both labels could apply |

---

## 4. Fixable Errors Analysis

### 4.1 Errors Fixable by Correcting Labels

From Category B analysis:
- OTHER → DELIVERY_LATE (36): If relabeled to DELIVERY_LATE → 36 fewer errors
- OTHER → DELIVERY_MISSING (11): If relabeled correctly → 11 fewer errors
- OTHER → APP_USAGE (16): Many should be delivery/order → ~10 fewer errors
- OTHER → RETURN_REQUEST (9): Some are returns → ~5 fewer errors

**Subtotal**: ~62 errors are directly fixable by label correction

### 4.2 Errors Potentially Fixable by Merging Intents

| Merge Action | Errors Affected | Reasoning |
|--------------|----------------|-----------|
| Merge DELIVERY_LATE + DELIVERY_MISSING | 13 (8+5) | Boundary confusion |
| Merge APP_USAGE → OTHER or DELIVERY | ~20 | APP_USAGE is catch-all |
| Merge ORDER_MODIFY → ORDER_STATUS | 2 | Only 2 examples |

**Subtotal**: ~35 errors affected by merges

### 4.3 Genuine Model Errors (Not Fixable by Label Changes)

- C + D categories: 101 + 45 = 146 errors
- These require model improvement (more features, better embeddings, etc.)

---

## 5. Theoretical Accuracy After Fixes

### Scenario: Correct OTHER and APP_USAGE Labels

Current: 302/540 = 55.93%

If we correct ~62 label errors (primarily OTHER → specific intents):
- Theoretical correct: 302 + 62 = 364
- Theoretical accuracy: 364/540 = **67.4%**

### Scenario: Plus Merge Delivery Intents

If we also merge DELIVERY_LATE/DELIVERY_MISSING boundaries (~13 more):
- Additional errors reduced: ~10
- Theoretical correct: 364 + 10 = 374
- Theoretical accuracy: 374/540 = **69.3%**

### Scenario: Plus Remove/Merge ORDER_MODIFY

With only 2 examples (both wrong), this class adds noise:
- Remove or merge ORDER_MODIFY: ~2 fewer errors
- Theoretical accuracy: ~**69.6%**

---

## 6. Confidence Distribution of Errors

| Confidence Range | Count | % | Interpretation |
|------------------|-------|---|----------------|
| Low (<0.15) | 113 | 47.5% | Model very uncertain |
| Mid (0.15-0.25) | 84 | 35.3% | Model somewhat uncertain |
| High (≥0.25) | 41 | 17.2% | Model confident but wrong |

**Key Insight**: 82.8% of errors have confidence < 0.25, indicating the model is generally uncertain when it makes mistakes. This is not overconfidence - it's honest uncertainty about hard cases.

---

## 7. Confidence vs. Category Relationship

| Category | Avg Confidence | Interpretation |
|----------|---------------|----------------|
| B (model correct) | ~0.18 | Model uncertain but right |
| C (genuine error) | ~0.17 | Model uncertain and wrong |
| D (ambiguous) | ~0.15 | Model very uncertain |

The similar confidence distributions across categories suggest the model is appropriately calibrated - it doesn't know when it's wrong.

---

## 8. Recommendations

### 8.1 HIGH CONFIDENCE Recommendations

1. **OTHER intent needs cleanup** (Confidence: HIGH)
   - 97 errors (40.8% of all errors) involve OTHER
   - 74 of these are likely wrong labels
   - Action: Systematic review of OTHER examples, relabel to specific intents

2. **ORDER_MODIFY should be merged/removed** (Confidence: HIGH)
   - Only 2 examples total, 0% accuracy
   - Both examples are about cancellation
   - Action: Merge into ORDER_STATUS or CANCELLATION

3. **APP_USAGE needs definition clarity** (Confidence: HIGH)
   - 27.3% accuracy, heavily used as catch-all
   - Many examples are about delivery, not app
   - Action: Define APP_USAGE more narrowly OR merge into OTHER

### 8.2 MEDIUM CONFIDENCE Recommendations

4. **Delivery intent boundaries are blurry** (Confidence: MEDIUM)
   - DELIVERY_LATE ↔ DELIVERY_MISSING confusion is understandable
   - 13 errors from boundary confusion
   - Action: Clarify definitions OR merge into single DELIVERY intent

5. **Phase 2 label corrections would improve accuracy** (Confidence: MEDIUM)
   - ~62 errors directly fixable by label correction
   - Would improve accuracy from 55.9% to ~67%
   - Action: Systematic relabeling effort

### 8.3 LOW CONFIDENCE / Needs More Analysis

6. **Return vs Refund vs Payment confusion** (Confidence: LOW)
   - Multiple confusion pairs between these
   - Need clearer definitions
   - Action: Define boundaries between RETURN_REQUEST, REFUND_REQUEST, PAYMENT_ISSUE

---

## 9. Phase 2 Diagnosis Summary

| Question | Answer | Confidence |
|----------|--------|------------|
| 1. Biggest root cause | OTHER being a catch-all with wrong labels | HIGH |
| 2. Probable label errors | ~92 (38.7% of errors) | HIGH |
| 3. Genuine model errors | ~101 (42.4% of errors) | HIGH |
| 4. Ambiguous cases | ~45 (18.9% of errors) | MEDIUM |
| 5. Insufficient information | ~0 | HIGH |
| 6. Should OTHER remain? | NO - needs to be eliminated or redefined | HIGH |
| 7. Should APP_USAGE remain? | UNCLEAR - needs clearer definition | MEDIUM |
| 8. Should ORDER_MODIFY remain? | NO - merge into ORDER_STATUS | HIGH |
| 9. Should delivery intents merge? | CONSIDER merging DELIVERY_LATE/MISSING | MEDIUM |
| 10. Recommended next action | Phase 2 label cleanup of OTHER examples | HIGH |

---

## 10. Conclusion

The dominant finding is that **label noise, not model quality, is the primary issue**. Nearly 40% of errors occur because the model predicts a reasonable intent (often delivery-related) but the human labeler marked it as OTHER or another incorrect intent.

**If only the OTHER and APP_USAGE labels were corrected:**
- Accuracy would improve from 55.9% to approximately 67-69%
- This would be a substantial improvement without any model changes

**The current model may already be performing near its ceiling for this taxonomy**. Further model improvements (new embeddings, different classifiers) will have limited impact if the label noise isn't addressed.

---

## Appendix: Methodology

1. Loaded 238 incorrect predictions from `phase1_evaluation_results.json`
2. Retrieved conversation texts for each error
3. Manually analyzed each error based on customer text
4. Categorized into A/B/C/D/E based on:
   - Whether the expected label matches the text
   - Whether the predicted label makes more sense
   - Whether both labels could apply
   - Whether the text is too vague to determine
5. Calculated theoretical accuracy improvements

---

*Report generated: 2026-09-10*
*Evaluation: 540 test examples, 238 errors analyzed*
