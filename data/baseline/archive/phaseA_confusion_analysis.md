# Phase A: Confusion Analysis Report

## 1. Summary

| Metric | Value |
|--------|-------|
| Accuracy | 70.56% (381/540) |
| Correct | 381/540 |
| Errors | 159/540 |
| Test Set Size | 540 |

## 2. Per-Intent Metrics

| Intent | Precision | Recall | F1-Score | Support |
|--------|-----------|--------|----------|---------|
| ACCOUNT_ACCESS | 0.33 | 0.29 | 0.31 | 7 |
| APP_USAGE | 0.66 | 0.48 | 0.55 | 44 |
| CANCELLATION | 1.00 | 1.00 | 1.00 | 1 |
| DELIVERY_LATE | 0.75 | 0.70 | 0.72 | 109 |
| DELIVERY_MISSING | 0.68 | 0.56 | 0.61 | 34 |
| DELIVERY_TRACKING | 0.75 | 0.38 | 0.50 | 8 |
| DEVICE_ISSUE | 0.73 | 0.56 | 0.63 | 34 |
| ORDER_STATUS | 0.67 | 0.37 | 0.48 | 27 |
| OTHER | 0.74 | 0.92 | 0.82 | 183 |
| PAYMENT_ISSUE | 0.61 | 0.74 | 0.67 | 23 |
| PRODUCT_ISSUE | 0.57 | 0.36 | 0.44 | 11 |
| REFUND_REQUEST | 0.53 | 0.62 | 0.57 | 13 |
| RETURN_REQUEST | 0.68 | 0.84 | 0.75 | 31 |
| VIDEO_STREAMING | 0.67 | 0.40 | 0.50 | 15 |

## 3. Top Confusion Pairs (Ranked by Error Count)

| Rank | Actual → Predicted | Count |
|------|-------------------|-------|
| 1 | APP_USAGE → OTHER | 14 |
| 2 | DELIVERY_LATE → OTHER | 13 |
| 3 | DEVICE_ISSUE → OTHER | 9 |
| 4 | ORDER_STATUS → OTHER | 6 |
| 5 | DELIVERY_LATE → RETURN_REQUEST | 6 |
| 6 | DELIVERY_MISSING → DELIVERY_LATE | 6 |
| 7 | ACCOUNT_ACCESS → OTHER | 5 |
| 8 | APP_USAGE → DELIVERY_LATE | 4 |
| 9 | DELIVERY_LATE → DELIVERY_MISSING | 4 |
| 10 | OTHER → APP_USAGE | 4 |
| 11 | OTHER → DELIVERY_LATE | 4 |
| 12 | VIDEO_STREAMING → DELIVERY_LATE | 4 |
| 13 | VIDEO_STREAMING → OTHER | 4 |
| 14 | DELIVERY_MISSING → OTHER | 3 |
| 15 | ORDER_STATUS → PAYMENT_ISSUE | 3 |
| 16 | PRODUCT_ISSUE → REFUND_REQUEST | 3 |

## 4. Error Distribution Analysis

### By True Label (Errors where X was the true intent)

| True Intent | Errors | Total | Error Rate |
|-------------|--------|-------|------------|
| APP_USAGE | 29 | 44 | 65.9% |
| DELIVERY_LATE | 35 | 109 | 32.1% |
| DEVICE_ISSUE | 15 | 34 | 44.1% |
| ORDER_STATUS | 17 | 27 | 63.0% |
| ACCOUNT_ACCESS | 7 | 7 | 100.0% |
| DELIVERY_MISSING | 15 | 34 | 44.1% |
| DELIVERY_TRACKING | 5 | 8 | 62.5% |
| OTHER | 21 | 183 | 11.5% |
| PAYMENT_ISSUE | 8 | 23 | 34.8% |
| PRODUCT_ISSUE | 11 | 11 | 100.0% |
| REFUND_REQUEST | 5 | 13 | 38.5% |
| RETURN_REQUEST | 6 | 31 | 19.4% |
| VIDEO_STREAMING | 9 | 15 | 60.0% |

### By Predicted Label (Errors where model predicted X)

| Predicted | Errors | Total | Error Rate |
|-----------|--------|-------|------------|
| OTHER | 53 | - | - |
| DELIVERY_LATE | 16 | - | - |
| APP_USAGE | 7 | - | - |
| DELIVERY_MISSING | 2 | - | - |
| RETURN_REQUEST | 5 | - | - |

## 5. Key Confusion Pair Analysis

### 5.1 APP_USAGE ↔ OTHER (18 total errors)

**APP_USAGE → OTHER (14):**
- Many APP_USAGE examples contain generic complaint language
- Model predicts OTHER due to low confidence signals for APP_USAGE
- Some examples are about website issues that could be APP_USAGE or OTHER

Example texts:
- "website not recognize the '1/2' in my address" → APP_USAGE (website issue)
- "Facing login issues on amazon" → APP_USAGE (account/access issue)
- "is there any Battlefront 2 available to pre order?" → ORDER_STATUS (not APP_USAGE)

**OTHER → APP_USAGE (4):**
- Model wrongly predicts APP_USAGE for generic texts
- These are likely correct errors (OTHER is appropriate)

### 5.2 DELIVERY_LATE ↔ OTHER (17 total errors)

**DELIVERY_LATE → OTHER (13):**
- Mixed bag: some about delivery delays, some about other issues
- Some examples contain promotional content mixed with complaints
- French/non-English content makes classification harder

Example texts:
- "package is 3 days late" → DELIVERY_LATE (correct label, model wrong)
- "iPhone fest is here!" → PROMOTIONAL (label may be wrong)
- "worst service ever" → GENERIC COMPLAINT (label may be OTHER)

**OTHER → DELIVERY_LATE (4):**
- Model predicts delivery but true label is OTHER
- Some texts mention delivery in passing but are about other issues

### 5.3 DEVICE_ISSUE ↔ OTHER (10 total errors)

**DEVICE_ISSUE → OTHER (9):**
- DEVICE_ISSUE examples often mixed with other intent signals
- Some are about account/app issues rather than device

Example texts:
- "switch to another spotify accounts on my echo" → APP_USAGE (not DEVICE_ISSUE)
- "reloaded $25, where is my $5" → PAYMENT_ISSUE (not DEVICE_ISSUE)

### 5.4 DELIVERY_LATE ↔ DELIVERY_MISSING (10 total errors)

**DELIVERY_LATE → DELIVERY_MISSING (4):**
- Ambiguous boundary between "not delivered yet" and "will never arrive"
- Some late deliveries become missing when customer gives up

**DELIVERY_MISSING → DELIVERY_LATE (6):**
- Items that were never received but labeled as DELIVERY_LATE
- "never arrived" vs "arrived late" confusion

### 5.5 DELIVERY_LATE ↔ RETURN_REQUEST (7 total errors)

- Customers returning items due to delivery issues
- Boundary confusion when return is triggered by delivery problem

### 5.6 ORDER_STATUS ↔ OTHER (7 total errors)

**ORDER_STATUS → OTHER (6):**
- ORDER_STATUS examples often generic complaints about orders
- Model struggles to distinguish specific order issues from generic OTHER

**OTHER → ORDER_STATUS (1):**
- One error only

## 6. Low-Support Intent Issues

### ACCOUNT_ACCESS (7 examples, 5 errors = 71.4% error rate)
- Very low support (7 examples)
- High error rate
- Confuses with OTHER heavily

### PRODUCT_ISSUE (11 examples, 11 errors = 100% error rate)
- All examples are errors in confusion pairs
- Not directly confused - involved in multiple confusion pairs

### VIDEO_STREAMING (15 examples, 9 errors = 60% error rate)
- High confusion with DELIVERY_LATE and OTHER
- Mixed content about streaming service issues

## 7. Observations

### 7.1 OTHER is a Catch-All
- OTHER has 183 examples (33.9% of test set)
- Error rate is relatively low (11.5%)
- Many intents confuse to/from OTHER

### 7.2 Delivery Intent Overlap
- DELIVERY_LATE, DELIVERY_MISSING, DELIVERY_TRACKING have overlapping boundaries
- Customers often describe delivery problems without clear specificity

### 7.3 APP_USAGE Boundary Issues
- APP_USAGE seems to capture any app/website issue
- But many examples are actually about account, payment, or order issues
- Unclear if APP_USAGE is well-defined

### 7.4 Low-Support Intents
- CANCELLATION (1), ACCOUNT_ACCESS (7), PRODUCT_ISSUE (11) have very low support
- Makes evaluation unreliable for these intents

## 8. Files Generated

| File | Description |
|------|-------------|
| `phaseA_confusion_matrix.json` | Full confusion matrix |
| `phaseA_intent_metrics.json` | Per-intent precision/recall/F1 |
| `phaseA_error_examples.jsonl` | All 159 error examples |
| `phaseA_summary.json` | Summary statistics |

---

*Report generated: 2026-09-11*
*Phase A: Confusion Analysis - COMPLETE*
