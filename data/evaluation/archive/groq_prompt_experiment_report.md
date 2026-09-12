# Groq Prompt Experiment Report

## Experiment Overview
- **Subset**: 100 conversations (seed 42) from the 540 test set
- **Model**: allam-2-7b
- **Improved prompt**: `data/evaluation/groq_improved_prompt.md`
- **Original prompt**: `data/evaluation/groq_current_configuration.md`

## CRITICAL ISSUE: Rate Limiting
**35/100 predictions failed with HTTP 429 - Rate limit reached**

- Error: `Limit 500000, Used` (daily token limit exceeded)
- These are counted as failures, not as wrong predictions

## Results

### On ALL 100 Predictions (including failures)
| Metric | Original | Improved |
|--------|----------|----------|
| Accuracy | 19/100 (19%) | 9/100 (9%) |
| Failed | 0 | 35 (rate limit) |

### On 65 VALID Predictions Only
| Metric | Original | Improved |
|--------|----------|----------|
| Accuracy | 13/65 (20%) | 9/65 (13.85%) |
| Improvement | - | -6.15% |

## Prediction Distribution (65 valid)

| Intent | Actual | Original | Improved |
|--------|--------|----------|----------|
| ORDER_STATUS | 3 | 20 | **38** |
| OTHER | 29 | 5 | 4 |
| DELIVERY_LATE | 11 | 8 | 8 |

**Key finding**: Improved prompt over-predicts ORDER_STATUS even more than original (38 vs 20), while under-predicting OTHER (4 vs 5).

## Analysis

### Why did improved prompt fail?
1. **Rate limiting**: 35% of predictions failed - experiment is compromised
2. **Structured output parsing**: Many valid responses didn't match `primary_intent:` format
3. **ORDER_STATUS bias persists**: Even with clearer definitions, the model still massively over-predicts ORDER_STATUS

### Evidence of Parsing Issues
Of the 65 "successful" responses, many didn't follow the structured format:
- `primary_intent: X` not found in raw response
- Fallback to partial matching or OTHER

## Conclusion

**EXPERIMENT INCONCLUSIVE due to:**
1. Rate limiting (35% failure rate)
2. The 65 valid predictions show improved prompt performed WORSE (13.85% vs 20%)

**Cannot conclude**: Whether the prompt improvement helps or hurts.

## Files
- `groq_prompt_experiment_predictions.jsonl` - All 100 predictions
- `groq_prompt_experiment_comparison.json` - Metrics
- `groq_prompt_experiment_subset.json` - 100 conversation IDs

## Next Steps (if retrying)
1. Wait for rate limit to reset (daily limit)
2. Use a smaller test set (20-30 conversations)
3. Or use a different model with higher rate limits