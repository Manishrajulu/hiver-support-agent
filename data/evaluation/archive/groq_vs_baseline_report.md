# Groq LLM vs TF-IDF + Logistic Regression Comparison Report

## Test Set
- **Size**: 540 conversations (exact same as baseline)
- **Split**: 80/20 stratified, random_state=42
- **Labels**: Rule-based primary_intent from v2.1 labeling

---

## Model Comparison

| Model | Accuracy | Macro F1 | Weighted F1 |
|-------|----------|----------|-------------|
| Majority Baseline | 0.3759 | 0.0390 | 0.2054 |
| TF-IDF + Logistic Regression | **0.5630** | **0.5070** | **0.5599** |
| Groq LLM (allam-2-7b) | 0.1944 | 0.2291 | 0.2226 |

**Groq performed WORSE than TF-IDF baseline by significant margins.**

---

## Key Finding

**Surprising Result**: The Groq LLM significantly underperformed the traditional ML baseline.

| Metric | Groq vs TF-IDF Difference |
|--------|--------------------------|
| Accuracy | -0.3685 (-36.9%) |
| Macro F1 | -0.2778 (-27.8%) |
| Weighted F1 | -0.3373 (-33.7%) |

---

## Per-Intent F1 Comparison

| Intent | Baseline F1 | Groq F1 | Difference |
|--------|-------------|---------|-----------|
| ORDER_MODIFY | 0.000 | 0.035 | **+0.035** |
| APP_USAGE | 0.267 | 0.180 | -0.087 |
| PRODUCT_ISSUE | 0.333 | 0.278 | -0.056 |
| DELIVERY_LATE | 0.493 | 0.339 | -0.153 |
| DELIVERY_MISSING | 0.562 | 0.062 | **-0.501** |
| DELIVERY_TRACKING | 0.667 | 0.222 | -0.444 |
| DEVICE_ISSUE | 0.667 | 0.244 | -0.423 |
| ORDER_STATUS | 0.586 | 0.123 | -0.463 |
| OTHER | 0.630 | 0.179 | -0.451 |
| PAYMENT_ISSUE | 0.566 | 0.410 | -0.156 |
| VIDEO_STREAMING | 0.563 | 0.353 | -0.210 |
| ACCOUNT_ACCESS | 0.500 | 0.286 | -0.214 |
| REFUND_REQUEST | 0.606 | 0.348 | -0.258 |
| RETURN_REQUEST | 0.658 | 0.150 | **-0.508** |

**Groq only outperformed baseline on ORDER_MODIFY** (0.035 vs 0.000).

---

## Top Groq Confusions

| Actual -> Predicted | Count |
|---------------------|-------|
| OTHER -> ORDER_STATUS | 68 |
| OTHER -> ORDER_MODIFY | 46 |
| DELIVERY_LATE -> ORDER_STATUS | 33 |
| RETURN_REQUEST -> ORDER_MODIFY | 20 |
| OTHER -> DELIVERY_LATE | 19 |
| OTHER -> DELIVERY_MISSING | 16 |
| OTHER -> APP_USAGE | 13 |
| DEVICE_ISSUE -> APP_USAGE | 13 |

**Analysis**: Groq heavily biases toward ORDER_STATUS and ORDER_MODIFY, misclassifying many OTHER and DELIVERY cases.

---

## Top Baseline Confusions

| Actual -> Predicted | Count |
|---------------------|-------|
| OTHER -> DELIVERY_LATE | 39 |
| APP_USAGE -> OTHER | 15 |
| DELIVERY_LATE -> OTHER | 13 |
| OTHER -> APP_USAGE | 13 |
| APP_USAGE -> DELIVERY_LATE | 8 |

---

## Why Did Groq Perform Poorly?

### Hypothesis 1: Model Selection
- **allam-2-7b** may not be well-tuned for classification tasks
- This is an API model, not specifically fine-tuned for intent classification
- May need a different model (GPT, Claude, or fine-tuned model)

### Hypothesis 2: Prompt Engineering
- The taxonomy prompt may not be optimal
- May need few-shot examples
- Temperature/settings may need adjustment

### Hypothesis 3: Label Quality
- Comparing against rule-based labels (v2.1), NOT human ground truth
- Rule-based labels have ~43.5% error rate
- Groq may be making semantically correct predictions that differ from rules

### Hypothesis 4: Order Bias
- Groq heavily predicts ORDER_STATUS and ORDER_MODIFY
- This suggests the model may be defaulting to common intents
- May need re-ranking or threshold tuning

---

## Important Caveat

**These results compare Groq against rule-based labels, NOT human ground truth.**

The rule-based labels (from v2.1) are known to have issues:
- Earlier manual review found 56.5% error rate for rules
- Groq's "incorrect" predictions may actually be semantically correct

A proper comparison would require human-annotated ground truth.

---

## Conclusion

1. **Groq LLM (allam-2-7b) significantly underperformed TF-IDF + Logistic Regression**
2. **TF-IDF baseline remains the stronger classifier** on this task with these labels
3. **The Groq model choice matters** - allam-2-7b may not be suitable for classification
4. **Proper evaluation requires human ground truth**, not rule-based labels

### Recommendations

1. **For production**: TF-IDF + Logistic Regression is currently the best performer
2. **For improvement**: Try different LLM models (GPT, Claude) or fine-tune
3. **For proper comparison**: Generate human-annotated ground truth
4. **For hybrid approach**: Use rules for high-confidence cases, LLM for uncertain cases

---

## Files Created

| File | Description |
|------|-------------|
| `groq_test_predictions.jsonl` | 540 Groq predictions |
| `groq_test_metrics.json` | Groq metrics |
| `groq_vs_baseline_comparison.json` | Full comparison data |
| `groq_vs_baseline_error_analysis.json` | Error examples |
| `groq_test_confusion_matrix.json` | Confusion matrices |
| `groq_vs_baseline_report.md` | This report |

---

*Report generated: 2026-09-10*
