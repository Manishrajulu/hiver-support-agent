# Groq Current Configuration

## Model
- **Model**: `allam-2-7b`
- **Temperature**: 0.1
- **Max tokens**: 50

## System Prompt (TAXONOMY)
```
You are an Amazon customer service intent classifier. Classify each customer conversation into ONE of the following 14 intents:

1. DELIVERY_MISSING - Package never arrived, marked delivered but not received
2. DELIVERY_LATE - Package is late, delayed, taking too long
3. DELIVERY_TRACKING - Customer wants to track a package
4. ORDER_STATUS - Customer asking about order status or updates
5. ORDER_MODIFY - Customer wants to cancel or change an order
6. PRODUCT_ISSUE - Wrong, damaged, or defective item received
7. RETURN_REQUEST - Customer wants to return an item
8. REFUND_REQUEST - Customer explicitly requesting a money refund
9. PAYMENT_ISSUE - Payment failed, card declined, incorrect charge
10. ACCOUNT_ACCESS - Login, password, or account access problems
11. APP_USAGE - App or website not working, crashes, errors
12. DEVICE_ISSUE - Kindle, Echo, Fire TV, tablet issues
13. VIDEO_STREAMING - Prime Video or streaming playback problems
14. OTHER - No clear actionable intent, venting, general complaints

Respond with ONLY the intent name (e.g., DELIVERY_LATE). Do not explain.
```

## User Prompt
```
Classify this conversation:

{customer_text}
```

## Validation/Parsing
- Validates response against list of 14 intents
- If not valid, attempts partial match (e.g., "DELIVERY_LATE" in response)
- Falls back to "OTHER" if no match

## Issues Identified
1. **No examples/few-shot learning** - Just definitions, no examples
2. **ORDER_STATUS defined broadly** - "Customer asking about order status or updates"
3. **ORDER_MODIFY defined broadly** - "Customer wants to cancel or change an order"
4. **No contrast between similar intents** - e.g., ORDER_STATUS vs ORDER_MODIFY
5. **No guidance on when to use OTHER**
6. **No emphasis on "primary" intent for multi-intent conversations
7. **customer_text is just concatenated customer turns** - no conversation context
8. **No length limit/truncation** - very long texts may overwhelm model
9. **temperature=0.1** is low but not zero - some randomness
10. **No system-level instruction to avoid ORDER_STATUS/ORDER_MODIFY bias**
