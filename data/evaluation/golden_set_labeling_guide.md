# Golden Set Labeling Guide

## Purpose

This guide defines the labeling methodology for the AmazonHelp golden evaluation set.
Each example must be labeled with a single primary intent.

---

## Intent Taxonomy (15 Classes)

### Delivery-Related (3)
| Intent | Definition | Examples |
|--------|------------|----------|
| **DELIVERY_LATE** | Package has not arrived by promised date, is delayed | "My package was supposed to arrive yesterday", "3 days late" |
| **DELIVERY_MISSING** | Package never arrived, not received, or lost | "Package never came", "I never received my order" |
| **DELIVERY_TRACKING** | Request for tracking information or status | "Where is my package?", "Track my order" |

### Order-Related (2)
| Intent | Definition | Examples |
|--------|------------|----------|
| **ORDER_STATUS** | Asking about order state or information | "Where is my order?", "Order #123 status" |
| **ORDER_MODIFY** | Want to cancel or modify an order | "Cancel my order", "Change shipping address" |

### Product-Related (2)
| Intent | Definition | Examples |
|--------|------------|----------|
| **PRODUCT_ISSUE** | Wrong item, damaged, defective, not as described | "Received wrong item", "Product arrived damaged" |
| **RETURN_REQUEST** | Want to return an item for exchange or refund | "I want to return my order", "How do I return?" |

### Financial (2)
| Intent | Definition | Examples |
|--------|------------|----------|
| **REFUND_REQUEST** | Explicitly requests money back | "I want a refund", "Give me my money back" |
| **PAYMENT_ISSUE** | Payment failure, double charge, wrong amount | "Charged twice", "Payment failed", "Wrong amount" |

### Account (1)
| Intent | Definition | Examples |
|--------|------------|----------|
| **ACCOUNT_ACCESS** | Login problems, password issues, cannot access | "Can't log in", "Forgot my password" |

### Technical (3)
| Intent | Definition | Examples |
|--------|------------|----------|
| **APP_USAGE** | Problem with Amazon website, app, or digital service | "App not working", "Website won't load" |
| **DEVICE_ISSUE** | Problem with Amazon device (Kindle, Echo, Fire TV) | "Kindle frozen", "Echo won't connect" |
| **VIDEO_STREAMING** | Issue with Prime Video streaming | "Video won't play", "Prime Video buffering" |

### Other (2)
| Intent | Definition | Examples |
|--------|------------|----------|
| **OTHER** | No clear actionable intent or issue not covered | "Hello?", "Thank you", "General question" |
| **CANCELLATION** | Want to cancel subscription or service | "Cancel Prime membership", "Stop subscription" |

---

## Labeling Rules

### Rule 1: Single Primary Intent
Assign **ONE** primary intent per conversation. Choose the most specific actionable intent.

### Rule 2: Priority Order When Multiple Intents Apply
If multiple intents seem applicable, use this priority:

1. **PAYMENT_ISSUE** (financial - immediate action)
2. **REFUND_REQUEST** (financial - immediate action)
3. **ACCOUNT_ACCESS** (blocks all other actions)
4. **ORDER_MODIFY** (immediate action)
5. **DELIVERY_MISSING** (urgent)
6. **DELIVERY_LATE** (urgent)
7. **PRODUCT_ISSUE**
8. **RETURN_REQUEST**
9. **DELIVERY_TRACKING**
10. **ORDER_STATUS**
11. **DEVICE_ISSUE**
12. **APP_USAGE**
13. **VIDEO_STREAMING**
14. **OTHER**
15. **CANCELLATION**

### Rule 3: Ambiguous Cases

| Scenario | Label | Reason |
|----------|-------|--------|
| "not delivered" without time reference | DELIVERY_MISSING | Implies never arriving |
| "not delivered by [date]" or "late" | DELIVERY_LATE | Explicit promised date |
| "where is my order?" without complaint | ORDER_STATUS | General inquiry, not complaint |
| Delivery mentioned but main issue different | OTHER | Delivery is incidental |

### Rule 4: Non-English Messages
For non-English conversations, classify based on:
- **Subject matter**: What are they complaining about?
- **Keywords**: cancel, refund, late, missing, etc.
- **Emotional tone**: Frustrated about what?

---

## Edge Case Examples

| Customer Message | Correct Label | Reasoning |
|-----------------|---------------|-----------|
| "My package was supposed to arrive yesterday but it's not here" | DELIVERY_LATE | Explicit promised date mentioned |
| "My package never arrived" | DELIVERY_MISSING | No date reference, implies never |
| "I ordered a week ago and haven't heard anything" | ORDER_STATUS | General inquiry, not explicit complaint |
| "The video keeps buffering on Prime Video" | VIDEO_STREAMING | Explicit streaming issue |
| "I want to cancel my Prime membership" | CANCELLATION | Explicit cancellation request |
| "My Kindle screen is black and won't turn on" | DEVICE_ISSUE | Physical device problem |
| "I can't log into my account" | ACCOUNT_ACCESS | Login/access issue |
| "The Amazon app keeps crashing" | APP_USAGE | App/website issue |
| "I was charged $50 but my order was only $30" | PAYMENT_ISSUE | Payment discrepancy |
| "Thanks for your help" | OTHER | No actionable intent |
| "My package shows delivered but I don't have it" | DELIVERY_MISSING | Delivered but not received |
| "I want to return my order because it's damaged" | PRODUCT_ISSUE | Damaged is the primary issue |

---

## Common Confusion Points

### DELIVERY_LATE vs DELIVERY_MISSING
- **DELIVERY_LATE**: Customer implies package IS coming, just late
- **DELIVERY_MISSING**: Customer implies package will NEVER arrive

### ORDER_STATUS vs DELIVERY_LATE
- **ORDER_STATUS**: Customer asking ABOUT order status (question)
- **DELIVERY_LATE**: Customer COMPLAINING about late delivery (complaint)

### APP_USAGE vs DEVICE_ISSUE
- **APP_USAGE**: Problems with app or website functionality
- **DEVICE_ISSUE**: Problems with physical Amazon devices (Echo, Kindle, Fire)

### PAYMENT_ISSUE vs REFUND_REQUEST
- **PAYMENT_ISSUE**: Problem with payment itself (failed, wrong amount, double charge)
- **REFUND_REQUEST**: Customer explicitly wants money back

### PRODUCT_ISSUE vs RETURN_REQUEST
- **PRODUCT_ISSUE**: The item itself has a problem (wrong, damaged, defective)
- **RETURN_REQUEST**: Customer wants to send item back

---

## How to Label

### Step 1: Read the customer message
Focus on the customer's message only. Do not consider agent responses.

### Step 2: Identify the primary issue
What is the customer asking about or complaining about?

### Step 3: Match to an intent
Use the definitions and priority order to assign the best intent.

### Step 4: Note any ambiguity (optional)
Use `human_notes` to explain your decision or flag any edge cases.

### Step 5: Assign the label
Write the intent in the `human_label` field exactly as shown (e.g., DELIVERY_LATE).

---

## Label Values Reference

Use exactly one of these 15 labels:

```
ACCOUNT_ACCESS
APP_USAGE
CANCELLATION
DELIVERY_LATE
DELIVERY_MISSING
DELIVERY_TRACKING
DEVICE_ISSUE
ORDER_MODIFY
ORDER_STATUS
OTHER
PAYMENT_ISSUE
PRODUCT_ISSUE
REFUND_REQUEST
RETURN_REQUEST
VIDEO_STREAMING
```

---

*Labeling guide version: 1.0*
*Created: 2026-09-11*
