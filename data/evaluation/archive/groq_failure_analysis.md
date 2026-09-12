# Groq LLM Failure Analysis

## Executive Summary

**Groq LLM (allam-2-7b) severely underperformed TF-IDF + Logistic Regression**

| Metric | Baseline (TF-IDF+LR) | Groq | Difference |
|--------|---------------------|------|-----------|
| Accuracy | 56.30% | 19.44% | -36.9% |
| Macro F1 | 0.507 | 0.229 | -0.278 |
| Weighted F1 | 0.560 | 0.223 | -0.337 |

**Root Cause**: Groq has a massive bias toward ORDER_STATUS and ORDER_MODIFY, massively under-predicting OTHER and most other intents.

---

## 1. Current Groq Configuration

- **Model**: `allam-2-7b`
- **Temperature**: 0.1
- **Max tokens**: 50
- **System prompt**: Basic taxonomy with 14 intent definitions
- **User prompt**: "Classify this conversation:\n\n{customer_text}"
- **Validation**: Partial match fallback to "OTHER"

---

## 2. Prediction Distribution Analysis

| Intent | Actual | Groq Predicted | Ratio (Pred/Actual) |
|--------|--------|----------------|---------------------|
| ORDER_MODIFY | 2 | 112 | **56.0x** |
| ORDER_STATUS | 26 | 153 | **5.9x** |
| ACCOUNT_ACCESS | 6 | 22 | **3.7x** |
| PRODUCT_ISSUE | 11 | 25 | **2.3x** |
| OTHER | 203 | 32 | **0.16x** |
| DELIVERY_TRACKING | 8 | 1 | **0.12x** |
| DEVICE_ISSUE | 34 | 7 | **0.21x** |
| RETURN_REQUEST | 31 | 9 | **0.29x** |

**GROQ MASSIVELY OVER-PREDICTS**: ORDER_MODIFY (56x), ORDER_STATUS (6x)
**GROQ MASSIVELY UNDER-PREDICTS**: OTHER (16%), DELIVERY_TRACKING (12%)

---

## 3. Top Confusion Analysis

### OTHER -> ORDER_STATUS: 68 cases
**Analysis**: Groq thinks vague complaints are "order status questions"

### OTHER -> ORDER_MODIFY: 46 cases
**Analysis**: Groq thinks venting is "wanting to cancel/modify order"

### DELIVERY_LATE -> ORDER_STATUS: 33 cases
**Analysis**: Groq confuses "when will I get it" (delivery question) with "what's my order status"

---

## 4. Example Analysis

### Example: OTHER -> ORDER_STATUS

**Conversation ID**: amazonhelp_115316
- **Rule-based (actual)**: OTHER
- **Groq predicted**: ORDER_STATUS
- **Baseline predicted**: OTHER
- **Customer text**: "where the heck is my anthology? said it left hillsboro this morning..."

This is clearly NOT an order status question - it's a "where is my delivery" question. But Groq misclassified it.

### Example: OTHER -> ORDER_MODIFY

**Conversation ID**: amazonhelp_078660
- **Rule-based (actual)**: OTHER
- **Groq predicted**: ORDER_MODIFY
- **Customer text**: "Dear @115850 One of the worst service from you.. not expecting like this.."

This is venting/complaint, NOT order modification.

---

## 5. Prompt Quality Assessment

### Issues Identified:

1. **ORDER_STATUS definition is TOO BROAD**
   - "Customer asking about order status or updates"
   - Any question could be interpreted as "asking about status"

2. **ORDER_MODIFY definition is TOO BROAD**
   - "Customer wants to cancel or change an order"
   - "Change" is too vague - Groq interprets complaints as "wanting change"

3. **OTHER definition is UNDEREMPHASIZED**
   - "No clear actionable intent, venting, general complaints"
   - But no guidance on when to actually use it

4. **NO examples provided**
   - Model has no positive/negative examples
   - Cannot learn distinctions between similar intents

5. **NO contrast between similar intents**
   - ORDER_STATUS vs ORDER_MODIFY not contrasted
   - DELIVERY_LATE vs ORDER_STATUS not contrasted
   - PAYMENT_ISSUE vs REFUND_REQUEST not contrasted

6. **NO emphasis on "primary" intent**
   - Multi-intent conversations not handled
   - Model picks first matching intent

7. **No length management**
   - Very long customer texts may overwhelm model
   - No truncation or prioritization

---

## 6. Model vs Prompt Problem

### Evidence for PROMPT problem:
1. Systematic bias toward only 2 intents (ORDER_STATUS, ORDER_MODIFY)
2. This suggests the model is following flawed instructions, not a capability issue
3. The pattern is consistent - not random errors

### Evidence for MODEL problem:
1. allam-2-7b may not be well-tuned for classification
2. Not a chat model - may struggle with instruction-following

### Evidence for LABEL problem:
1. Rule-based labels have ~43.5% known error rate
2. "OTHER" being under-predicted (32 vs 203 actual) suggests model may be MORE correct than labels

**Conclusion: PRIMARY cause is PROMPT (instruction problem), SECONDARY is MODEL capability**

---

## 7. Dataset Concerns

- **Labels are rule-based, NOT human ground truth**
- Rule-based labels have known issues:
  - PAYMENT_ISSUE: 0% accuracy in manual review
  - APP_USAGE: 0% accuracy in manual review
- Groq's "errors" may actually be semantically correct classifications

**Key Question**: Is Groq wrong, or are the rule-based labels wrong?

---

## 8. Root Cause Ranking

| Rank | Cause | Evidence |
|------|-------|----------|
| 1 | **Prompt instruction problem** | Systematic bias toward 2 intents, consistent pattern |
| 2 | **Model not suited for classification** | allam-2-7b is not a classification model |
| 3 | **Label quality** | Comparing against flawed rule-based labels |

---

## 9. Most Likely Root Cause

**The prompt defines ORDER_STATUS and ORDER_MODIFY too broadly, causing the model to over-predict these intents when it should default to OTHER.**

Specific failure modes:
1. "When will I get my order?" → Should be DELIVERY_LATE, Groq says ORDER_STATUS
2. "I hate Amazon service" → Should be OTHER, Groq says ORDER_MODIFY
3. "Where is my package?" → Should be DELIVERY_TRACKING, Groq says ORDER_STATUS

---

## 10. Recommended ONE Next Experiment

**Improve the prompt with explicit negative examples and clearer definitions, then rerun on a small subset (50-100 conversations).**

Specific prompt changes:
1. Add "OTHER is the correct answer for venting, complaints, or general frustration without a specific actionable request"
2. Add "ORDER_STATUS is ONLY for explicit questions like 'where is my order' or 'any update on my order'"
3. Add "ORDER_MODIFY is ONLY for explicit requests like 'cancel my order' or 'change my address'"
4. Add 2-3 positive and negative examples for each confused intent pair
5. Test with same 540 test set after prompt improvement

**If improved prompt still fails, switch to a stronger model (GPT-4, Claude) before abandoning LLM approach.**

---

## Files Created

| File | Description |
|------|-------------|
| `groq_current_configuration.md` | Exact prompt and config |
| `groq_other_to_order_status_examples.json` | 10 examples |
| `groq_other_to_order_modify_examples.json` | 10 examples |
| `groq_delivery_late_to_order_status_examples.json` | 10 examples |
| `groq_failure_analysis.md` | This report |

---

*Analysis completed: 2026-09-10*
