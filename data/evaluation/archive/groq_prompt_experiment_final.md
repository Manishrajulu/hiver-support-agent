# Groq Prompt Experiment - Final Summary

## Experiment Details
- **Model**: allam-2-7b
- **Subset**: 100 conversations (seed 42) from 540 test set
- **Original prompt**: `data/evaluation/groq_current_configuration.md`
- **Improved prompt**: `data/evaluation/groq_improved_prompt.md`

---

## 1. Original Prompt Performance on 100-Case Subset
- **Accuracy**: 19/100 = **19.00%**

## 2. Improved Prompt Performance
- **Accuracy (all 100)**: 9/100 = **9.00%**
- **Accuracy (valid only)**: 9/65 = **13.85%**

## 3. Successful Requests
- **Valid predictions**: 65/100

## 4. 429 Failures
- **Rate limit failures**: 35/100
- **Reason**: Daily token limit (500,000 TPD) exceeded during experiment

## 5. Accuracy on All 100
| Model | Correct | Accuracy |
|-------|---------|----------|
| Original | 19 | 19.00% |
| Improved | 9 | 9.00% |

## 6. Accuracy on Valid Predictions Only
| Model | Correct | Accuracy |
|-------|---------|----------|
| Original | 13 | 20.00% |
| Improved | 9 | 13.85% |

---

## 7. ORDER_STATUS Prediction Bias

| Metric | Actual | Original Predicted | Improved Predicted |
|--------|--------|-------------------|-------------------|
| ORDER_STATUS | 5 | 28 | 38 |

**Observation**: The improved prompt did NOT reduce ORDER_STATUS over-prediction. It INCREASED it (28 → 38).

---

## 8. Why the Comparison is Not Conclusive

1. **35% missing predictions** (429 rate limit failures) means we cannot compare the full 100-case sets
2. The 65 valid predictions represent a biased subset (those that completed before rate limit hit)
3. No statistical significance can be claimed with incomplete data
4. The 35 failed predictions could have improved or worsened the comparison

**The experiment produced NO conclusive evidence about prompt quality.**

---

## 9. Critical Observation: ORDER_STATUS Over-Prediction Persisted

Despite the improved prompt including:
- Narrower definitions for ORDER_STATUS
- Explicit distinctions between ORDER_STATUS vs DELIVERY_LATE
- Examples showing correct classification
- Emphasis on "OTHER is valid"

**The model still over-predicted ORDER_STATUS by 7.6x (38 vs 5 actual).**

This suggests the issue may be:
- Model-level bias toward ORDER_STATUS
- Prompt instructions being ignored or overridden by model's training
- Not purely a prompt engineering problem

---

## 10. Final Statement

**Prompt-only improvement has not demonstrated a benefit for allam-2-7b.**

The improved prompt did not reduce ORDER_STATUS over-prediction and performed worse on the valid subset. However, due to 35% rate limit failures, this result is **inconclusive**.

**We cannot claim the model is definitively bad based on this experiment.**

---

## Files Generated
- `groq_prompt_experiment_predictions.jsonl` - All 100 predictions with raw responses
- `groq_prompt_experiment_comparison.json` - Metrics JSON
- `groq_prompt_experiment_subset.json` - 100 conversation IDs
- `groq_prompt_experiment_report.md` - Initial report
- `groq_connectivity_diagnostic.md` - Connectivity test results
- `groq_api_failure_report.md` - Prior failure documentation

---

*Experiment completed: 2026-09-10*
