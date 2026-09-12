# V2.1 Manual Validation Plan

## Overview

This document describes the manual validation sample for V2.1 labeled conversations.

---

## 1. Total V2.1 Conversations

| Metric | Value |
|--------|-------|
| Total conversations | 2,700 |
| File source | `data/processed/amazonhelp_labeled_conversations_v21.jsonl` |

---

## 2. Sampling Methodology

### Stratified Random Sampling

Conversations were selected using **stratified random sampling with deterministic selection**:

1. **Fixed random seed**: `42` (for reproducibility)
2. **Stratification by primary intent**: Each target intent had a quota
3. **Borderline case enrichment**: Conversations near decision boundaries were preferentially included
4. **Final shuffle**: Sample was shuffled to prevent ordering bias

### Borderline Case Detection

Borderline cases were identified using keyword patterns that indicate proximity to related intents:

| Intent Pair | Borderline Keywords |
|-------------|---------------------|
| PAYMENT_ISSUE ↔ REFUND_REQUEST | refund, money back, charged, charge |
| DELIVERY_LATE ↔ DELIVERY_MISSING | late, delayed, never arrived, never received, not arrived |
| OTHER → various intents | payment, refund, delivery, app, website |

---

## 3. Number Selected Per Intent

| Assigned Intent | Target | Selected | Borderline Count |
|----------------|--------|----------|-----------------|
| PAYMENT_ISSUE | 30 | 30 | ~100 borderline available, 30 selected |
| REFUND_REQUEST | 30 | 30 | ~67 borderline available, 30 selected |
| DELIVERY_LATE | 30 | 30 | ~346 borderline available, 30 selected |
| DELIVERY_MISSING | 30 | 30 | ~44 borderline available, 30 selected |
| ORDER_STATUS | 20 | 20 | Normal cases |
| APP_USAGE | 20 | 20 | Normal cases |
| DEVICE_ISSUE | 20 | 20 | Normal cases |
| OTHER | 20 | 20 | ~201 borderline available |
| **TOTAL** | **200** | **200** | |

---

## 4. Number of Borderline Cases

| Review Reason | Count | Description |
|---------------|-------|-------------|
| `payment_refund_boundary` | 15 | PAYMENT_ISSUE or REFUND_REQUEST with keywords from the other intent |
| `delivery_late_missing_boundary` | 36 | DELIVERY_LATE or DELIVERY_MISSING with keywords from the other intent |
| `other_possible_missed_intent` | 89 | OTHER conversations that may have a clear intent |
| `random_stratified` | 60 | Random selection from non-borderline cases |
| **TOTAL** | **200** | |

---

## 5. Fixed Random Seed

**Random seed: `42`**

This ensures the sample is reproducible. Any reviewer using the same seed will get the same sample.

---

## 6. How Manual Reviewers Should Judge Correctness

### Review Labels

For each conversation, reviewers should assign one of three labels:

| Label | Meaning |
|-------|---------|
| **CORRECT** | The assigned primary intent matches the customer's main problem or question |
| **INCORRECT** | The assigned primary intent does NOT match; provide the correct intent |
| **AMBIGUOUS** | The conversation is genuinely unclear; explain why |

---

### Judging Guidelines

#### CORRECT
- The customer's primary issue aligns with the assigned intent
- Even if secondary intents exist, the primary is the main concern

#### INCORRECT
- The customer's primary issue is clearly a different intent
- Provide the correct intent from the existing taxonomy:

| Correct Intent | When to Use |
|---------------|-------------|
| DELIVERY_MISSING | Package never arrived, marked delivered but not received |
| DELIVERY_LATE | Package is late, delayed, taking too long |
| DELIVERY_TRACKING | Customer wants to track a package |
| ORDER_STATUS | Customer asking about order status/updates |
| ORDER_MODIFY | Customer wants to cancel or change an order |
| PRODUCT_ISSUE | Wrong, damaged, or defective item received |
| RETURN_REQUEST | Customer wants to return an item |
| REFUND_REQUEST | Customer explicitly requesting a refund |
| PAYMENT_ISSUE | Payment failed, card declined, incorrect charge |
| ACCOUNT_ACCESS | Login, password, or account access problems |
| APP_USAGE | App or website not working |
| DEVICE_ISSUE | Kindle, Echo, or other device issues |
| VIDEO_STREAMING | Prime Video or streaming problems |
| OTHER | No clear actionable intent |

#### AMBIGUOUS
- The customer's message is vague or genuinely unclear
- Could reasonably be interpreted as multiple intents
- Customer is just venting or making general complaints
- **Do NOT create a new intent**

---

### Special Cases

#### PAYMENT_ISSUE vs REFUND_REQUEST

| Scenario | Assigned | Correct? |
|----------|----------|----------|
| "I was charged incorrectly" | PAYMENT_ISSUE | CORRECT |
| "I want a refund for my order" | REFUND_REQUEST | CORRECT |
| "I was charged and want my money back" | Depends on emphasis | AMBIGUOUS |
| "Where is my refund?" | REFUND_REQUEST | CORRECT |
| "Why was I charged twice?" | PAYMENT_ISSUE | CORRECT |

**Rule**: If customer explicitly asks for money back/refund → REFUND_REQUEST. If customer describes a payment problem → PAYMENT_ISSUE.

#### DELIVERY_LATE vs DELIVERY_MISSING

| Scenario | Assigned | Correct? |
|----------|----------|----------|
| "My package is 3 days late" | DELIVERY_LATE | CORRECT |
| "My package never arrived" | DELIVERY_MISSING | CORRECT |
| "Tracking says delivered but I don't have it" | DELIVERY_MISSING | CORRECT |
| "My package was supposed to arrive yesterday" | DELIVERY_LATE | CORRECT |
| "Still waiting for my package" (no explicit delivery context) | DELIVERY_LATE or OTHER | AMBIGUOUS |

**Rule**: "Never" + "received" → DELIVERY_MISSING. "Late" + "delayed" → DELIVERY_LATE.

#### OTHER Cases

If a conversation in OTHER has clear intent evidence, mark INCORRECT and provide the correct intent.

If a conversation is genuinely unclassifiable or just general venting, mark AMBIGUOUS.

---

## 7. Output Format

Reviewers should create a JSON file with the following structure:

```json
{
  "reviews": [
    {
      "conversation_id": "amazonhelp_XXXXX",
      "review_label": "CORRECT | INCORRECT | AMBIGUOUS",
      "correct_intent": "INTENT_NAME (if INCORRECT)",
      "notes": "Optional reviewer notes"
    }
  ]
}
```

---

## 8. File Locations

| File | Description |
|------|-------------|
| `data/samples/v21_manual_validation_sample.json` | Sample of 200 conversations to review |
| `data/processed/v21_manual_validation_plan.md` | This document |

---

## 9. Summary Statistics

| Metric | Value |
|--------|-------|
| Total sample size | 200 |
| Random seed | 42 |
| Borderline cases | 140 (70%) |
| Pure random cases | 60 (30%) |
| Target intent coverage | 8 primary intents + OTHER |

---

## 10. Stop Criteria

Manual review should stop when:
- All 200 conversations have been reviewed, OR
- Budget/time constraints are reached

Even a partial review (100+ reviews) provides valuable signal about labeling quality.

---

**STOP after completing manual validation review.**