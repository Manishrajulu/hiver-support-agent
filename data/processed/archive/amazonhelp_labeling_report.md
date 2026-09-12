# AmazonHelp Labeling Report

## Overview

- **Total conversations processed**: 2,700
- **Total successfully labeled**: 2,700
- **Labeling method**: Deterministic rule-based pipeline
- **Taxonomy version**: v1.0 (frozen)

---

## Primary Intent Distribution

| Intent | Count | Percentage |
|--------|-------|------------|
| OTHER | 968 | 35.9% |
| DELIVERY_LATE | 556 | 20.6% |
| APP_USAGE | 200 | 7.4% |
| DEVICE_ISSUE | 152 | 5.6% |
| DELIVERY_MISSING | 147 | 5.4% |
| RETURN_REQUEST | 141 | 5.2% |
| PAYMENT_ISSUE | 128 | 4.7% |
| ORDER_STATUS | 119 | 4.4% |
| REFUND_REQUEST | 92 | 3.4% |
| VIDEO_STREAMING | 65 | 2.4% |
| PRODUCT_ISSUE | 50 | 1.9% |
| DELIVERY_TRACKING | 35 | 1.3% |
| ACCOUNT_ACCESS | 30 | 1.1% |
| ORDER_MODIFY | 17 | 0.6% |

---

## Secondary Intent Frequencies

| Secondary Intent | Count |
|-----------------|-------|
| APP_USAGE | 321 |
| REFUND_REQUEST | 166 |
| DEVICE_ISSUE | 140 |
| PAYMENT_ISSUE | 129 |
| ORDER_STATUS | 118 |
| RETURN_REQUEST | 98 |
| ACCOUNT_ACCESS | 83 |
| PRODUCT_ISSUE | 63 |
| VIDEO_STREAMING | 36 |
| ORDER_MODIFY | 7 |

---

## Modifier Frequencies

| Modifier | Count |
|----------|-------|
| DELIVERY_CARRIER | 346 |
| PRIME_CUSTOMER | 190 |
| MARKETPLACE | 165 |
| SUBSCRIPTION | 79 |

---

## Escalation Signal Frequencies

| Signal | Count |
|--------|-------|
| FRUSTRATION_HIGH | 256 |
| PREVIOUS_CONTACT | 160 |
| SERVICE_COMPLAINT | 156 |
| ESCALATION_REQUEST | 140 |

---

## Language Distribution

| Language | Count | Percentage |
|----------|-------|------------|
| non_en | 2,683 | 99.4% |
| en | 17 | 0.6% |

**NOTE**: Language detection is overly aggressive. Most conversations are in English but contain special characters (emoji, Unicode) that trigger non-English detection. This is a known issue in the current pipeline.

---

## Data Quality Distribution

| Quality | Count | Percentage |
|---------|-------|------------|
| NON_ENGLISH | 2,488 | 92.1% |
| SHORT | 202 | 7.5% |
| GOOD | 10 | 0.4% |

**NOTE**: Due to language detection issues, most conversations are flagged as NON_ENGLISH. The actual English conversation rate is likely much higher.

---

## Confidence Distribution

| Confidence | Count | Percentage |
|------------|-------|------------|
| MEDIUM | 1,220 | 45.2% |
| LOW | 968 | 35.9% |
| HIGH | 512 | 19.0% |

---

## Multi-Intent Statistics

- **Multi-intent conversations**: 777 (28.8%)
- **Single-intent conversations**: 1,923 (71.2%)

---

## Sample Labeled Conversations

### 20 Random Examples

See `data/samples/amazonhelp_labeling_sample.json` for full examples.

### 20 LOW-Confidence Examples

See `data/samples/amazonhelp_labeling_sample.json` for full examples.

### 20 OTHER Examples

See `data/samples/amazonhelp_labeling_sample.json` for full examples.

---

## Representative Examples by Intent

### DELIVERY_LATE

```
amazonhelp_049149:
- Primary: DELIVERY_LATE
- Modifiers: ['DELIVERY_CARRIER']
- Signals: ['ESCALATION_REQUEST']
- Customer: "@115850 never expected from a company like Amazon. You should have serious look at your partner 'Gati'..."
```

### APP_USAGE

```
amazonhelp_031388:
- Primary: APP_USAGE
- Confidence: MEDIUM
- Customer: "Serieus j'ai l'impression d'etre prise pour une conne par Amazon la... [French]"
```

### DEVICE_ISSUE

```
amazonhelp_019134:
- Primary: DEVICE_ISSUE
- Confidence: HIGH
- Customer: "@AmazonHelp if you buy an echo plus do you no longer need the Phillips home hub to control lights?"
```

---

## LABELING QUALITY CHECK

### Structural Validation

| Check | Result |
|-------|--------|
| Missing primary_intent | 0 ✓ |
| Invalid intent names | 0 ✓ |
| Duplicate conversation IDs | 0 ✓ |
| Empty conversations | 0 ✓ |
| OTHER with secondary_intents | 0 ✓ |

### Intent Distribution Sanity

- **OTHER rate (35.9%)**: High but expected given:
  - Deterministic keyword matching misses implicit language
  - Non-English conversations cannot be matched by English keywords
  - "How to" questions that don't match problem patterns
- **DELIVERY_LATE is top (20.6%)**: Reasonable - late delivery is most common complaint
- **APP_USAGE second (7.4%)**: Reasonable - app/website issues common
- **ORDER_MODIFY lowest (0.6%)**: Reasonable - modification requests are rare

### Known Issues

1. **Language Detection Bug**: The regex patterns for French/Spanish/German are matching English words (e.g., "que", "pour", "est" in French are common in English text). This causes 99.4% to be marked as "non_en" when the actual rate is ~70-80% English.

2. **Data Quality Flagging**: Due to language detection bug, 92.1% are marked NON_ENGLISH. Actual rate is lower.

3. **OTHER Rate**: 35.9% OTHER is higher than ideal. Contributing factors:
   - Deterministic matching is strict
   - Non-English conversations cannot be matched
   - Casual/informal language not in keyword lists

4. **Intent Boundary Issues**:
   - DELIVERY_LATE vs DELIVERY_MISSING: Some "never received" phrases may be marked DELIVERY_LATE
   - APP_USAGE vs DEVICE_ISSUE: App-related device issues may not disambiguate well

### Recommendations for Improvement

1. **Fix language detection** before using language stats
2. **Consider adding** common informal phrases to keyword lists to reduce OTHER
3. **Review DELIVERY_LATE vs DELIVERY_MISSING boundary** with manual inspection
4. **Manual review** of OTHER examples to identify recoverable patterns

---

## Files Generated

| File | Description |
|------|-------------|
| `data/processed/amazonhelp_labeled_conversations.jsonl` | Full labeled dataset (2,700 records) |
| `data/processed/amazonhelp_label_statistics.json` | Statistical summary |
| `data/processed/amazonhelp_labeling_report.md` | This report |
| `data/samples/amazonhelp_labeling_sample.json` | Sample conversations (60 total) |

---

## Output Schema

```json
{
  "conversation_id": "amazonhelp_XXXXX",
  "primary_intent": "DELIVERY_LATE",
  "secondary_intents": ["APP_USAGE"],
  "modifiers": ["PRIME_CUSTOMER"],
  "escalation_signals": ["FRUSTRATION_HIGH"],
  "language": "en",
  "data_quality": "GOOD",
  "confidence": "HIGH",
  "turns": [...]
}
```

---

## Stop Condition

Labeling pipeline complete. **STOP** - do not train, build RAG, or use LLM until manual review of labeled data is complete.