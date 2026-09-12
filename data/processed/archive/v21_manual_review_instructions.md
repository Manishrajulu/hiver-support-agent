# V2.1 Manual Review Instructions

## Overview

You will review 200 conversations from the V2.1 labeled dataset to evaluate the quality of the deterministic rule-based labeling.

---

## IMPORTANT: Judge the Customer's Actual Problem

**DO NOT judge whether keywords matched the rules.**

**DO judge whether the assigned intent matches the CUSTOMER'S ACTUAL PROBLEM or QUESTION.**

The rule-based system looks for keywords. Human reviewers should look at MEANING.

---

## How to Review

For each conversation:

1. **Read all customer turns** - ignore agent responses
2. **Identify the customer's primary problem** - what are they frustrated about or asking for help with?
3. **Compare to the assigned intent** - does it match?
4. **Fill in your verdict**

---

## Verdict Options

### CORRECT

The assigned primary intent matches the customer's main issue.

**Example**: Customer says "My package is 3 days late" → assigned DELIVERY_LATE → **CORRECT**

### INCORRECT

The assigned primary intent does NOT match the customer's main issue.

**You must also provide the correct intent** from the frozen taxonomy:

| Correct Intent | When to Use |
|---------------|-------------|
| DELIVERY_MISSING | Package never arrived, marked delivered but not received |
| DELIVERY_LATE | Package is late, delayed, taking too long |
| DELIVERY_TRACKING | Customer wants to track a package |
| ORDER_STATUS | Customer asking about order status or updates |
| ORDER_MODIFY | Customer wants to cancel or change an order |
| PRODUCT_ISSUE | Wrong, damaged, or defective item received |
| RETURN_REQUEST | Customer wants to return an item |
| REFUND_REQUEST | Customer explicitly requesting a money refund |
| PAYMENT_ISSUE | Payment failed, card declined, incorrect charge |
| ACCOUNT_ACCESS | Login, password, or account access problems |
| APP_USAGE | App or website not working |
| DEVICE_ISSUE | Kindle, Echo, or other device issues |
| VIDEO_STREAMING | Prime Video or streaming problems |
| OTHER | No clear actionable intent |

**Example**: Customer says "I want to cancel my order" → assigned ORDER_STATUS → **INCORRECT** → correct = ORDER_MODIFY

### AMBIGUOUS

The conversation is genuinely unclear or could reasonably be interpreted multiple ways.

**Do NOT mark as AMBIGUOUS just because it's complex.**

Mark as AMBIGUOUS only when:
- Customer is venting without a specific request
- Customer's problem could reasonably be multiple intents
- No clear actionable problem stated

**Example**: "amazon you are the worst" → no specific problem → **AMBIGUOUS**

---

## Common Decision Points

### PAYMENT_ISSUE vs REFUND_REQUEST

| Customer Says | Correct Intent | Why |
|---------------|-----------------|-----|
| "I want a refund for my order" | REFUND_REQUEST | Explicitly asks for refund |
| "I was charged twice" | PAYMENT_ISSUE | Describes a payment problem |
| "Why was I charged? I want my money back" | REFUND_REQUEST | Primary request is for money back |
| "My payment failed" | PAYMENT_ISSUE | Payment processing problem |

**Rule**: If the customer explicitly asks for money back → REFUND_REQUEST. If they describe a payment problem → PAYMENT_ISSUE.

### DELIVERY_LATE vs DELIVERY_MISSING

| Customer Says | Correct Intent | Why |
|---------------|-----------------|-----|
| "My package is 3 days late" | DELIVERY_LATE | Explicitly mentions lateness |
| "My package never arrived" | DELIVERY_MISSING | States it never arrived |
| "Tracking says delivered but I don't have it" | DELIVERY_MISSING | Never received |
| "It's been a week, where is my package?" | DELIVERY_MISSING | Implies never received |

**Rule**: "Never" received → DELIVERY_MISSING. "Late" or "delayed" → DELIVERY_LATE.

### OTHER Cases

If a conversation in OTHER clearly has an actionable problem, mark INCORRECT and provide the correct intent.

If a conversation is genuinely unclassifiable (venting, general complaints, no specific request), mark AMBIGUOUS.

---

## What to Display for Each Conversation

```
conversation_id: amazonhelp_XXXXX
assigned_primary_intent: [the assigned intent]
confidence: [HIGH/MEDIUM/LOW]
human_verdict: [CORRECT/INCORRECT/AMBIGUOUS]
human_label: [correct intent if INCORRECT]
human_reason: [your explanation]
```

---

## Display Format

For each conversation, show:

1. **conversation_id** - the unique ID
2. **assigned_primary_intent** - what the system assigned
3. **confidence** - system's confidence level
4. **turns** - all conversation turns (speaker + text)
5. **human_verdict** - your verdict (CORRECT/INCORRECT/AMBIGUOUS)
6. **human_label** - correct intent (if INCORRECT)
7. **human_reason** - your reasoning (optional but recommended)

---

## File Structure

The review file is at: `data/samples/v21_manual_validation_review.json`

Each entry has this structure:

```json
{
  "conversation_id": "amazonhelp_XXXXX",
  "assigned_primary_intent": "INTENT_NAME",
  "assigned_secondary_intents": [],
  "confidence": "HIGH/MEDIUM/LOW",
  "num_turns": 2,
  "turns": [
    {"turn_number": 1, "speaker": "Customer", "text": "..."},
    {"turn_number": 2, "speaker": "Agent", "text": "..."}
  ],
  "review_reason": "why_in_sample",
  "human_verdict": null,
  "human_label": null,
  "human_reason": null
}
```

---

## Allowed Values

### human_verdict (required)
- `CORRECT` - intent is correct
- `INCORRECT` - intent is wrong
- `AMBIGUOUS` - genuinely unclear

### human_label (required if INCORRECT)
Must be one of the 14 frozen taxonomy intents:
- DELIVERY_MISSING
- DELIVERY_LATE
- DELIVERY_TRACKING
- ORDER_STATUS
- ORDER_MODIFY
- PRODUCT_ISSUE
- RETURN_REQUEST
- REFUND_REQUEST
- PAYMENT_ISSUE
- ACCOUNT_ACCESS
- APP_USAGE
- DEVICE_ISSUE
- VIDEO_STREAMING
- OTHER

### human_reason (optional)
Your notes explaining the verdict.

---

## Examples

### Example 1: CORRECT

```
conversation_id: amazonhelp_123456
assigned_primary_intent: DELIVERY_LATE
confidence: HIGH
human_verdict: CORRECT
human_label: null
human_reason: "Customer clearly states package is late"
```

### Example 2: INCORRECT

```
conversation_id: amazonhelp_654321
assigned_primary_intent: PAYMENT_ISSUE
confidence: MEDIUM
human_verdict: INCORRECT
human_label: REFUND_REQUEST
human_reason: "Customer explicitly asks for money back, not describing a payment problem"
```

### Example 3: AMBIGUOUS

```
conversation_id: amazonhelp_111222
assigned_primary_intent: OTHER
confidence: LOW
human_verdict: AMBIGUOUS
human_label: null
human_reason: "Customer is venting but doesn't state a specific problem"
```

---

## Summary

| Field | Required | Values |
|-------|----------|--------|
| human_verdict | Yes | CORRECT, INCORRECT, AMBIGUOUS |
| human_label | If INCORRECT | One of 14 taxonomy intents |
| human_reason | No | Your explanation |

---

**STOP after completing the review of all 200 conversations.**