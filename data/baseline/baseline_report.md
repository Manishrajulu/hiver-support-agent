# Baseline Classification Model Report

## 1. Dataset

| Metric | Value |
|--------|-------|
| Total conversations | 2,700 |
| Source | `data/processed/amazonhelp_labeled_conversations_v21.jsonl` |
| Text representation | Customer text only (all turns) |
| Target | `primary_intent` |

## 2. Label Distribution

| Intent | Count | Percentage |
|--------|-------|------------|
| OTHER | 1,013 | 37.5% |
| DELIVERY_LATE | 481 | 17.8% |
| APP_USAGE | 221 | 8.2% |
| DEVICE_ISSUE | 170 | 6.3% |
| RETURN_REQUEST | 153 | 5.7% |
| DELIVERY_MISSING | 143 | 5.3% |
| ORDER_STATUS | 133 | 4.9% |
| PAYMENT_ISSUE | 114 | 4.2% |
| VIDEO_STREAMING | 71 | 2.6% |
| REFUND_REQUEST | 67 | 2.5% |
| PRODUCT_ISSUE | 53 | 2.0% |
| DELIVERY_TRACKING | 40 | 1.5% |
| ACCOUNT_ACCESS | 33 | 1.2% |
| ORDER_MODIFY | 8 | 0.3% |

**Note**: Highly imbalanced - OTHER dominates (37.5%), ORDER_MODIFY nearly absent (0.3%).

## 3. Train/Test Methodology

| Parameter | Value |
|-----------|-------|
| Train size | 2,160 (80%) |
| Test size | 540 (20%) |
| Split method | Stratified by primary_intent |
| Random seed | 42 |
| Reproducible | Yes |

**Quality Checks**:
- No duplicate conversation IDs
- No missing labels
- Train + Test = 2,700
- No train/test overlap

## 4. Majority-Class Baseline Results

| Metric | Value |
|--------|-------|
| Majority class | OTHER |
| Accuracy | 0.3759 |
| Macro Precision | 0.0269 |
| Macro Recall | 0.0714 |
| Macro F1 | 0.0390 |
| Weighted F1 | 0.2054 |

The majority baseline simply predicts "OTHER" for everything, giving ~37.6% accuracy due to OTHER being the majority class.

## 5. TF-IDF + Logistic Regression Results

| Metric | Value |
|--------|-------|
| Accuracy | 0.5630 |
| Balanced Accuracy | 0.5717 |
| Macro Precision | 0.4731 |
| Macro Recall | 0.5717 |
| Macro F1 | 0.5070 |
| Weighted F1 | 0.5599 |

**Configuration**:
- TfidfVectorizer: max_features=10000, ngram_range=(1,2), min_df=2, max_df=0.95, sublinear_tf=True
- LogisticRegression: C=1.0, class_weight='balanced', solver='lbfgs'

## 6. Per-Intent Performance

| Intent | Precision | Recall | F1 | Support |
|--------|-----------|--------|-----|---------|
| ACCOUNT_ACCESS | 0.4000 | 0.6667 | 0.5000 | 6 |
| APP_USAGE | 0.3226 | 0.2273 | 0.2667 | 44 |
| DELIVERY_LATE | 0.4522 | 0.5417 | 0.4929 | 96 |
| DELIVERY_MISSING | 0.5143 | 0.6207 | 0.5625 | 29 |
| DELIVERY_TRACKING | 0.5385 | 0.8750 | 0.6667 | 8 |
| DEVICE_ISSUE | 0.6316 | 0.7059 | 0.6667 | 34 |
| ORDER_MODIFY | 0.0000 | 0.0000 | 0.0000 | 2 |
| ORDER_STATUS | 0.5312 | 0.6538 | 0.5862 | 26 |
| OTHER | 0.7622 | 0.5369 | 0.6301 | 203 |
| PAYMENT_ISSUE | 0.5000 | 0.6522 | 0.5660 | 23 |
| PRODUCT_ISSUE | 0.4286 | 0.2727 | 0.3333 | 11 |
| REFUND_REQUEST | 0.5000 | 0.7692 | 0.6061 | 13 |
| RETURN_REQUEST | 0.5417 | 0.8387 | 0.6582 | 31 |
| VIDEO_STREAMING | 0.5000 | 0.6429 | 0.5625 | 14 |

**Best performing**: DELIVERY_TRACKING (F1=0.67), DEVICE_ISSUE (F1=0.67), RETURN_REQUEST (F1=0.66)
**Worst performing**: ORDER_MODIFY (F1=0.00), APP_USAGE (F1=0.27), PRODUCT_ISSUE (F1=0.33)

## 7. Confusion Matrix

| Actual \ Predicted | OTHER | DELIVERY_LATE | APP_USAGE | DEVICE_ISSUE | RETURN_REQUEST |
|-------------------|-------|---------------|-----------|--------------|----------------|
| OTHER | 109 | 39 | 13 | 6 | 8 |
| DELIVERY_LATE | 13 | 52 | 3 | 0 | 0 |
| APP_USAGE | 15 | 8 | 10 | 1 | 0 |
| DEVICE_ISSUE | 6 | 0 | 1 | 24 | 0 |
| RETURN_REQUEST | 4 | 0 | 0 | 0 | 26 |

**Key observations**:
- 39 OTHER cases misclassified as DELIVERY_LATE
- 15 APP_USAGE cases misclassified as OTHER
- 13 DELIVERY_LATE cases misclassified as OTHER

## 8. Error Analysis

### Top 10 Confusion Pairs

| Actual -> Predicted | Count |
|---------------------|-------|
| OTHER -> DELIVERY_LATE | 39 |
| APP_USAGE -> OTHER | 15 |
| DELIVERY_LATE -> OTHER | 13 |
| OTHER -> APP_USAGE | 13 |
| APP_USAGE -> DELIVERY_LATE | 8 |
| DELIVERY_MISSING -> DELIVERY_LATE | 8 |
| OTHER -> RETURN_REQUEST | 8 |
| OTHER -> DELIVERY_MISSING | 7 |
| OTHER -> VIDEO_STREAMING | 6 |
| OTHER -> DEVICE_ISSUE | 6 |

### Root Causes of Errors

1. **OTHER <-> DELIVERY_LATE confusion**: Customers complaining about late delivery without explicit "late" keywords are hard to classify
2. **APP_USAGE misclassified**: App-related complaints often mention delivery or other intents
3. **ORDER_MODIFY has 0 predictions**: Only 8 training samples - too few for model to learn

## 9. Limitations

1. **Class imbalance**: ORDER_MODIFY has only 8 samples (0.3%), making it nearly impossible to learn
2. **OTHER dominates**: 37.5% of data is OTHER, biasing the model
3. **Short text**: Twitter messages are brief, limiting feature extraction
4. **Multi-intent**: Some conversations have multiple issues but single-label classification is required
5. **Class imbalance affects recall**: APP_USAGE, PRODUCT_ISSUE, ORDER_MODIFY have very low recall

## 10. Final Conclusion

**"How well can a conventional ML classifier perform on this dataset without using an LLM?"**

| Baseline | Accuracy | Macro F1 | Weighted F1 |
|----------|----------|----------|-------------|
| Majority Class | 37.6% | 0.039 | 0.205 |
| TF-IDF + LR | **56.3%** | **0.507** | **0.560** |

The TF-IDF + Logistic Regression achieves:
- **56.3% accuracy** (vs 37.6% baseline)
- **0.507 Macro F1** (vs 0.039 baseline)
- **0.560 Weighted F1** (vs 0.205 baseline)

**This is a significant improvement** over the majority baseline, demonstrating that conventional ML can capture meaningful patterns in customer intent from text.

**However**, the model struggles with:
- Rare classes (ORDER_MODIFY: 0 F1)
- Ambiguous cases (OTHER vs specific intents)
- Context-dependent intent (delivery issues vs app issues)

**For production use**, this baseline provides a reasonable foundation but:
- Would need more training data for rare intents
- LLM-based classification likely to significantly improve on this
- Consider treating OTHER as a "fallback" requiring human review

---

## Artifacts

| File | Description |
|------|-------------|
| `baseline_model.joblib` | Trained sklearn pipeline |
| `baseline_metrics.json` | Summary metrics |
| `baseline_classification_report.json` | Full sklearn classification report |
| `baseline_confusion_matrix.json` | Confusion matrix data |
| `baseline_predictions.jsonl` | Test set predictions |
| `baseline_error_analysis.json` | Error examples and analysis |
| `baseline_train_test_split.json` | Train/test IDs for reproducibility |

---

*Report generated: 2026-09-10*
