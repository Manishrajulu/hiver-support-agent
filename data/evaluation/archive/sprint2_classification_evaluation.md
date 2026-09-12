# Sprint 2 — Classification Evaluation

## Status: COMPLETED

## Goal
Determine whether the final classifier is actually better than the baseline.

## Completed Work

### Final Classifier Decision (per `final_classifier_decision.md`)

| Model | Accuracy | Macro F1 | Weighted F1 |
|-------|----------|----------|-------------|
| Majority Baseline | 37.59% | 0.039 | 0.205 |
| **TF-IDF + Logistic Regression** | **56.30%** | **0.507** | **0.560** |
| Groq allam-2-7b | 19.44% | 0.229 | 0.223 |

### Conclusion

**TF-IDF + Logistic Regression** is the best-supported classifier:

1. **Highest accuracy**: 56.30% (vs 37.59% majority, 19.44% Groq)
2. **Highest Macro F1**: 0.507 (vs 0.039, 0.229)
3. **Highest Weighted F1**: 0.560 (vs 0.205, 0.223)
4. **No rate limiting issues** (unlike Groq)
5. **Reproducible** with deterministic split

### Groq allam-2-7b Results
- Performed **worse than majority baseline**
- Strong bias toward ORDER_STATUS (5.88x over-prediction)
- ORDER_MODIFY over-predicted 56x
- Prompt improvement experiment was **inconclusive** due to rate limiting
- **Groq is NOT recommended as the classifier**

### Known Caveats
- Labels are rule-based (v2.1), NOT human-verified ground truth
- Actual model accuracy on true human intent is unknown
- 43.5% known error rate in rule-based labels

## Frozen Artifacts
- `data/baseline/baseline_model.joblib` - TF-IDF + Logistic Regression
- `data/baseline/baseline_train_test_split.json` - Stratified 80/20 split
- `data/baseline/baseline_metrics.json` - Metrics
- `data/evaluation/final_classifier_decision.md` - Full decision documentation

## Sprint 2 COMPLETE - Ready for Sprint 3