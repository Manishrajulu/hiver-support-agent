# Phase B: Taxonomy Review Report

## 1. Executive Summary

Based on Phase A confusion analysis, this report reviews taxonomy boundaries and identifies potential label corrections.

**Key Finding:** Most confusion pairs represent genuine model limitations or ambiguous cases, NOT label errors. However, a small number of HIGH-CONFIDENCE label corrections are recommended.

---

## 2. Methodology

For each problematic boundary:
1. Inspect representative examples from both intents
2. Determine root cause: model failure, label error, ambiguity, or taxonomy issue
3. Assess confidence for potential correction
4. Document findings

---

## 3. Boundary Analysis

### 3.1 DELIVERY_LATE ↔ DELIVERY_MISSING

**Total confusion: 10 errors (4 + 6)**

**Analysis:**

| ID | True Label | Model Pred | Text Sample | Assessment |
|----|------------|------------|-------------|------------|
| amazonhelp_018062 | DELIVERY_MISSING | DELIVERY_LATE | "i opened an amazon account over a month ago...product which was supposed to deliver today" | Ambiguous - "supposed to deliver" suggests late, not missing |
| amazonhelp_001496 | DELIVERY_MISSING | DELIVERY_LATE | "product which was supposed to deliver on 19th oct" | Late, not missing |
| amazonhelp_139669 | DELIVERY_MISSING | DELIVERY_LATE | "Third time in two weeks I'm hunting my packages" | Hunting packages = missing, but model says late |
| amazonhelp_095529 | DELIVERY_MISSING | DELIVERY_LATE | "There is no carrier info because it hasn't been shipped" | Never shipped = DELIVERY_MISSING |

**DELIVERY_LATE Definition:**
"Customer says the promised/expected delivery date has passed or the delivery is explicitly delayed."

**DELIVERY_MISSING Definition:**
"Customer reports the package never arrived or was not received at all."

**Boundary Issue:** The distinction relies on customer certainty - "never arrived" vs "not yet arrived." This is often ambiguous in customer language.

**Recommended Corrections:**

| ID | Current | Proposed | Confidence | Reason |
|----|---------|----------|------------|--------|
| amazonhelp_018062 | DELIVERY_MISSING | DELIVERY_LATE | MEDIUM | "supposed to deliver today" implies promised date, not never arriving |

---

### 3.2 DELIVERY_LATE → OTHER (13 errors)

**Analysis of Error Patterns:**

Looking at the 13 examples where true=DELIVERY_LATE but model predicts OTHER:

| Category | Count | Example |
|----------|-------|---------|
| Genuine delivery late (model wrong) | 7 | "package is 3 days late", "Guaranteed 1 day delivery failed" |
| Generic complaint (label may be wrong) | 4 | "worst service ever", promotional content |
| Other issues (label wrong) | 2 | "A-to-z guarantee claim" (refund), "login issues" |

**Finding:** ~50% of these errors are genuine model failures on DELIVERY_LATE. ~50% may have incorrect labels.

**High-Confidence Label Correction Candidates:**

| ID | Current | Proposed | Confidence | Reason |
|----|---------|----------|------------|--------|
| amazonhelp_074202 | DELIVERY_LATE | OTHER | HIGH | Promotional tweet about iPhone festival, NOT about late delivery |
| amazonhelp_132432 | DELIVERY_LATE | OTHER | HIGH | "Timely delivered but worst service" - not about lateness |

---

### 3.3 APP_USAGE ↔ OTHER (18 total errors)

**APP_USAGE Definition:**
"Customer has a problem with the Amazon website, mobile app, or digital service (excluding account access issues)."

**Analysis:**

Looking at APP_USAGE true examples (labeled APP_USAGE but model says OTHER):

| ID | Text Sample | Assessment |
|----|-------------|------------|
| amazonhelp_099636 | "website not recognize the '1/2' in my address" | APP_USAGE - website issue |
| amazonhelp_051452 | "Battlefront 2 available to pre order?" | ORDER_STATUS - not APP_USAGE |
| amazonhelp_149200 | German: blocked from ordering | APP_USAGE (account blocked) |
| amazonhelp_013959 | "Facing login issues on amazon" | ACCOUNT_ACCESS - not APP_USAGE |

**Finding:** APP_USAGE examples are inconsistent. Some are about app/website issues, some are about account access, some are about orders.

**Proposed Refinement:**

The APP_USAGE category may be too broad. However, without clear semantic rules, we should NOT change labels.

**High-Confidence Label Correction Candidates:**

| ID | Current | Proposed | Confidence | Reason |
|----|---------|----------|------------|--------|
| amazonhelp_034718 | APP_USAGE | PRODUCT_ISSUE | MEDIUM | "There was a scratch on a product" - not app issue |

---

### 3.4 DEVICE_ISSUE → OTHER (9 errors)

**DEVICE_ISSUE Definition:**
"Customer has a problem with a physical Amazon device (Echo, Kindle, Fire Tablet, etc.)"

**Analysis:**

Looking at examples where true=DEVICE_ISSUE but model predicts OTHER:

| ID | Text Sample | Assessment |
|----|-------------|------------|
| amazonhelp_047943 | Ticket sales for concert (Morrissey) | NOT DEVICE_ISSUE - wrong label? |
| amazonhelp_148628 | "$25 reload not showing" | PAYMENT_ISSUE - not DEVICE_ISSUE |
| amazonhelp_124427 | "switch to another spotify accounts on my echo" | APP_USAGE - app/Account issue |

**Finding:** DEVICE_ISSUE seems to have label noise. Some examples are clearly not about physical device issues.

**High-Confidence Label Correction Candidates:**

| ID | Current | Proposed | Confidence | Reason |
|----|---------|----------|------------|--------|
| amazonhelp_047943 | DEVICE_ISSUE | OTHER | HIGH | Concert ticket sales - NOT a device issue |
| amazonhelp_148628 | DEVICE_ISSUE | PAYMENT_ISSUE | MEDIUM | Amazon Cash reload issue |

---

### 3.5 ORDER_STATUS ↔ OTHER (7 total errors)

**ORDER_STATUS Definition:**
"Customer has a question about the status of an existing order or needs information about their order."

**Analysis:**

| ID | True | Predicted | Text Sample | Assessment |
|----|------|-----------|-------------|------------|
| amazonhelp_064611 | ORDER_STATUS | OTHER | "not delivering my order on time" | DELIVERY_LATE - wrong label |
| amazonhelp_068640 | ORDER_STATUS | OTHER | "gave my order to a random resident" | DELIVERY_MISSING - wrong label |

**Finding:** ORDER_STATUS examples often confused with delivery issues. The boundary between ORDER_STATUS and DELIVERY_LATE/DELIVERY_MISSING is fuzzy.

**High-Confidence Label Correction Candidates:**

| ID | Current | Proposed | Confidence | Reason |
|----|---------|----------|------------|--------|
| amazonhelp_064611 | ORDER_STATUS | DELIVERY_LATE | HIGH | "not delivering my order on time" - explicit late delivery |
| amazonhelp_068640 | ORDER_STATUS | DELIVERY_MISSING | HIGH | "gave my order to a random resident" - delivery to wrong address |

---

### 3.6 VIDEO_STREAMING Issues

**Observation:** VIDEO_STREAMING has 15 examples with 9 errors (60% error rate). This is very high.

Looking at VIDEO_STREAMING examples:
- Some are about Prime Video not working
- Some are about billing/charges for streaming
- Some are about unrelated content

**Finding:** VIDEO_STREAMING category may need definition refinement, but insufficient evidence for mass correction.

---

## 4. Proposed Corrections Summary

### HIGH-CONFIDENCE Corrections (Confidence = HIGH)

| ID | Current Label | Proposed Label | Reasoning |
|----|---------------|----------------|-----------|
| amazonhelp_074202 | DELIVERY_LATE | OTHER | Promotional tweet, not about late delivery |
| amazonhelp_132432 | DELIVERY_LATE | OTHER | "Timely delivered but worst service" - not about lateness |
| amazonhelp_047943 | DEVICE_ISSUE | OTHER | Concert tickets, not device issue |
| amazonhelp_064611 | ORDER_STATUS | DELIVERY_LATE | "not delivering my order on time" |
| amazonhelp_068640 | ORDER_STATUS | DELIVERY_MISSING | Order given to wrong person |

### MEDIUM-CONFIDENCE Corrections (Confidence = MEDIUM)

| ID | Current Label | Proposed Label | Reasoning |
|----|---------------|----------------|-----------|
| amazonhelp_018062 | DELIVERY_MISSING | DELIVERY_LATE | "supposed to deliver today" - late, not missing |
| amazonhelp_034718 | APP_USAGE | PRODUCT_ISSUE | "scratch on a product" |
| amazonhelp_148628 | DEVICE_ISSUE | PAYMENT_ISSUE | Amazon Cash reload issue |

### LOW-CONFIDENCE / NOT RECOMMENDED

| ID | Current | Proposed | Reason Not Recommended |
|----|---------|----------|----------------------|
| amazonhelp_051452 | APP_USAGE | ORDER_STATUS | Low confidence - text about pre-order but may be generic |
| amazonhelp_013959 | APP_USAGE | ACCOUNT_ACCESS | Ambiguous - login could be either |

---

## 5. Statistics

| Category | Count |
|----------|-------|
| HIGH-confidence corrections | 5 |
| MEDIUM-confidence corrections | 3 |
| LOW-confidence corrections | 0 |
| **Total recommended** | **8** |

---

## 6. Taxonomic Rule Refinements

### DELIVERY_LATE vs DELIVERY_MISSING

**Rule Refinement:**
- DELIVERY_LATE: Explicit mention of date/time that has passed, or "delayed", "late", "not on time"
- DELIVERY_MISSING: Explicit mention of "never arrived", "not received", "missing", "lost"

**Key Distinction:** Customer certainty about whether the package will arrive or not.

### APP_USAGE vs ACCOUNT_ACCESS

**Current:**
- APP_USAGE: App/website issues
- ACCOUNT_ACCESS: Account login/access issues

**Issue:** These overlap significantly. Login issues can be either.

**Recommendation:** Consider merging or clarifying boundary.

### ORDER_STATUS vs DELIVERY_*

**Rule Refinement:**
- ORDER_STATUS: Question about order state, tracking, or general order inquiry
- DELIVERY_LATE: Explicit complaint about delayed delivery
- DELIVERY_MISSING: Explicit complaint about non-delivery

**Key Distinction:** Whether the customer is asking a question (STATUS) vs making a complaint (DELIVERY_*)

---

## 7. Files Generated

| File | Description |
|------|-------------|
| `phaseB_relabel_proposals.json` | Structured list of proposed corrections |

---

## 8. Conclusion

**Summary of Findings:**
- 159 total errors in 540 examples
- Most errors are genuine model limitations or ambiguous cases
- 8 high/medium-confidence label corrections identified
- 5 HIGH-confidence corrections that could be applied
- 3 MEDIUM-confidence corrections requiring review

**Recommendation:**
- Apply ONLY the 5 HIGH-confidence corrections in Phase C
- Do NOT apply MEDIUM-confidence corrections automatically
- Monitor if corrections improve or harm other confusion pairs

---

*Report generated: 2026-09-11*
*Phase B: Taxonomy Review - COMPLETE*
