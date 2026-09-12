# Golden Set Evaluation Report

## Important Disclaimer

**This is an INDEPENDENT golden-set evaluation using manually labeled data.**
**It must NOT be presented as the official 71.11% Phase C test accuracy.**

The official 71.11% accuracy was obtained on a separate 540-example held-out test set
using the same Phase C model. This golden-set evaluation uses a different dataset
of 220 English-only examples with human-verified labels.

---

## Evaluation Configuration

| Setting | Value |
|---------|-------|
| Model | Phase C (TF-IDF + LinearSVC) |
| Model path | data/baseline/phaseC_model.joblib |
| Word n-grams | (1, 2) |
| Char n-grams | (3, 6) |
| Dataset | golden_set_labeled.csv |
| Examples | 220 |
| Language filter | English-only |

---

## Overall Results

| Metric | Value |
|--------|-------|
| **Accuracy** | **56.36%** |
| Correct | 124/220 |
| Incorrect | 96/220 |

---

## Integrity Checks

| Check | Result |
|-------|--------|
| Input rows | PASS (220) |
| Predictions generated | PASS (220) |
| Human labels present | PASS (220) |
| Missing predictions | PASS (0) |
| Missing human labels | PASS (0) |
| Invalid intent labels | PASS (0) |

---

## Human Label Distribution

| Intent | Count | Percentage |
|--------|-------|------------|
| DELIVERY_LATE | 50 | 22.7% |
| OTHER | 31 | 14.1% |
| DELIVERY_MISSING | 22 | 10.0% |
| PAYMENT_ISSUE | 16 | 7.3% |
| ACCOUNT_ACCESS | 15 | 6.8% |
| PRODUCT_ISSUE | 15 | 6.8% |
| RETURN_REQUEST | 11 | 5.0% |
| REFUND_REQUEST | 11 | 5.0% |
| DEVICE_ISSUE | 10 | 4.5% |
| CANCELLATION | 10 | 4.5% |
| VIDEO_STREAMING | 7 | 3.2% |
| APP_USAGE | 6 | 2.7% |
| DELIVERY_TRACKING | 6 | 2.7% |
| ORDER_STATUS | 6 | 2.7% |
| ORDER_MODIFY | 4 | 1.8% |

**Total examples:** 220

---

## Model Prediction Distribution

| Intent | Count | Percentage |
|--------|-------|------------|
| OTHER | 68 | 30.9% |
| DELIVERY_LATE | 41 | 18.6% |
| APP_USAGE | 16 | 7.3% |
| ORDER_STATUS | 14 | 6.4% |
| PAYMENT_ISSUE | 13 | 5.9% |
| DEVICE_ISSUE | 12 | 5.5% |
| DELIVERY_MISSING | 11 | 5.0% |
| RETURN_REQUEST | 10 | 4.5% |
| REFUND_REQUEST | 5 | 2.3% |
| VIDEO_STREAMING | 5 | 2.3% |
| PRODUCT_ISSUE | 5 | 2.3% |
| DELIVERY_TRACKING | 5 | 2.3% |
| ACCOUNT_ACCESS | 5 | 2.3% |
| CANCELLATION | 5 | 2.3% |
| ORDER_MODIFY | 5 | 2.3% |

---

## Per-Intent Metrics

| Intent | Actual | Predicted | Correct | Precision | Recall | F1 |
|--------|--------|-----------|---------|-----------|--------|-----|
| ACCOUNT_ACCESS | 15 | 15 | 5 | 33.3% | 33.3% | 33.3 |
| APP_USAGE | 6 | 6 | 5 | 83.3% | 83.3% | 83.3 |
| CANCELLATION | 10 | 10 | 4 | 40.0% | 40.0% | 40.0 |
| DELIVERY_LATE | 50 | 50 | 26 | 52.0% | 52.0% | 52.0 |
| DELIVERY_MISSING | 22 | 22 | 4 | 18.2% | 18.2% | 18.2 |
| DELIVERY_TRACKING | 6 | 6 | 5 | 83.3% | 83.3% | 83.3 |
| DEVICE_ISSUE | 10 | 10 | 6 | 60.0% | 60.0% | 60.0 |
| ORDER_MODIFY | 4 | 4 | 3 | 75.0% | 75.0% | 75.0 |
| ORDER_STATUS | 6 | 6 | 3 | 50.0% | 50.0% | 50.0 |
| OTHER | 31 | 31 | 29 | 93.5% | 93.5% | 93.5 |
| PAYMENT_ISSUE | 16 | 16 | 11 | 68.8% | 68.8% | 68.8 |
| PRODUCT_ISSUE | 15 | 15 | 4 | 26.7% | 26.7% | 26.7 |
| REFUND_REQUEST | 11 | 11 | 5 | 45.5% | 45.5% | 45.5 |
| RETURN_REQUEST | 11 | 11 | 9 | 81.8% | 81.8% | 81.8 |
| VIDEO_STREAMING | 7 | 7 | 5 | 71.4% | 71.4% | 71.4 |

---

## Confusion Matrix

| **True \ Pred** | ACCOUNT_ | APP_USAG | CANCELLA | DELIVERY | DELIVERY | DELIVERY | DEVICE_I | ORDER_MO | ORDER_ST | OTHER    | PAYMENT_ | PRODUCT_ | REFUND_R | RETURN_R | VIDEO_ST |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **ACCOUNT_ACCE** |        5 |        4 |        0 |        1 |        1 |        0 |        0 |        0 |        0 |        4 |        0 |        0 |        0 |        0 |        0 |
| **APP_USAGE   ** |        0 |        5 |        0 |        0 |        0 |        0 |        1 |        0 |        0 |        0 |        0 |        0 |        0 |        0 |        0 |
| **CANCELLATION** |        0 |        0 |        4 |        0 |        1 |        0 |        0 |        2 |        2 |        1 |        0 |        0 |        0 |        0 |        0 |
| **DELIVERY_LAT** |        0 |        4 |        0 |       26 |        2 |        0 |        0 |        0 |        4 |       14 |        0 |        0 |        0 |        0 |        0 |
| **DELIVERY_MIS** |        0 |        1 |        1 |        4 |        4 |        0 |        2 |        0 |        2 |        8 |        0 |        0 |        0 |        0 |        0 |
| **DELIVERY_TRA** |        0 |        0 |        0 |        1 |        0 |        5 |        0 |        0 |        0 |        0 |        0 |        0 |        0 |        0 |        0 |
| **DEVICE_ISSUE** |        0 |        1 |        0 |        0 |        0 |        0 |        6 |        0 |        0 |        3 |        0 |        0 |        0 |        0 |        0 |
| **ORDER_MODIFY** |        0 |        0 |        0 |        0 |        0 |        0 |        0 |        3 |        1 |        0 |        0 |        0 |        0 |        0 |        0 |
| **ORDER_STATUS** |        0 |        0 |        0 |        0 |        0 |        0 |        0 |        0 |        3 |        1 |        1 |        1 |        0 |        0 |        0 |
| **OTHER       ** |        0 |        1 |        0 |        1 |        0 |        0 |        0 |        0 |        0 |       29 |        0 |        0 |        0 |        0 |        0 |
| **PAYMENT_ISSU** |        0 |        0 |        0 |        1 |        1 |        0 |        1 |        0 |        0 |        2 |       11 |        0 |        0 |        0 |        0 |
| **PRODUCT_ISSU** |        0 |        0 |        0 |        2 |        1 |        0 |        1 |        0 |        1 |        6 |        0 |        4 |        0 |        0 |        0 |
| **REFUND_REQUE** |        0 |        0 |        0 |        2 |        1 |        0 |        0 |        0 |        1 |        0 |        1 |        0 |        5 |        1 |        0 |
| **RETURN_REQUE** |        0 |        0 |        0 |        2 |        0 |        0 |        0 |        0 |        0 |        0 |        0 |        0 |        0 |        9 |        0 |
| **VIDEO_STREAM** |        0 |        0 |        0 |        1 |        0 |        0 |        1 |        0 |        0 |        0 |        0 |        0 |        0 |        0 |        5 |

---

## Top 10 Confusion Pairs

| Rank | True Intent | Predicted As | Count |
|------|-------------|--------------|-------|
| 1 | DELIVERY_LATE | OTHER | 14 |
| 2 | DELIVERY_MISSING | OTHER | 8 |
| 3 | PRODUCT_ISSUE | OTHER | 6 |
| 4 | DELIVERY_LATE | APP_USAGE | 4 |
| 5 | DELIVERY_LATE | ORDER_STATUS | 4 |
| 6 | DELIVERY_MISSING | DELIVERY_LATE | 4 |
| 7 | ACCOUNT_ACCESS | APP_USAGE | 4 |
| 8 | ACCOUNT_ACCESS | OTHER | 4 |
| 9 | DEVICE_ISSUE | OTHER | 3 |
| 10 | RETURN_REQUEST | DELIVERY_LATE | 2 |

---

## Misclassified Examples

| Example ID | Human Label | Model Prediction |
|------------|-------------|-----------------|
| golden_0001 | RETURN_REQUEST | DELIVERY_LATE |
| golden_0003 | REFUND_REQUEST | DELIVERY_LATE |
| golden_0010 | DELIVERY_MISSING | OTHER |
| golden_0015 | ACCOUNT_ACCESS | APP_USAGE |
| golden_0016 | PRODUCT_ISSUE | OTHER |
| golden_0017 | PRODUCT_ISSUE | OTHER |
| golden_0020 | PAYMENT_ISSUE | DEVICE_ISSUE |
| golden_0023 | APP_USAGE | DEVICE_ISSUE |
| golden_0024 | DELIVERY_MISSING | OTHER |
| golden_0025 | REFUND_REQUEST | ORDER_STATUS |
| golden_0031 | REFUND_REQUEST | RETURN_REQUEST |
| golden_0033 | PRODUCT_ISSUE | OTHER |
| golden_0035 | ACCOUNT_ACCESS | OTHER |
| golden_0036 | DELIVERY_LATE | OTHER |
| golden_0042 | DELIVERY_LATE | OTHER |
| golden_0043 | DELIVERY_LATE | OTHER |
| golden_0044 | PRODUCT_ISSUE | ORDER_STATUS |
| golden_0045 | DELIVERY_LATE | OTHER |
| golden_0046 | DELIVERY_MISSING | OTHER |
| golden_0047 | DELIVERY_MISSING | ORDER_STATUS |
| golden_0048 | DELIVERY_LATE | APP_USAGE |
| golden_0051 | PRODUCT_ISSUE | DELIVERY_LATE |
| golden_0053 | DELIVERY_MISSING | DELIVERY_LATE |
| golden_0054 | DEVICE_ISSUE | OTHER |
| golden_0055 | OTHER | APP_USAGE |
| golden_0056 | CANCELLATION | OTHER |
| golden_0057 | DELIVERY_LATE | OTHER |
| golden_0059 | OTHER | DELIVERY_LATE |
| golden_0060 | DELIVERY_LATE | APP_USAGE |
| golden_0062 | PAYMENT_ISSUE | DELIVERY_LATE |
| golden_0064 | ACCOUNT_ACCESS | DELIVERY_MISSING |
| golden_0066 | PRODUCT_ISSUE | DELIVERY_MISSING |
| golden_0069 | DELIVERY_LATE | ORDER_STATUS |
| golden_0072 | ORDER_MODIFY | ORDER_STATUS |
| golden_0074 | DELIVERY_LATE | DELIVERY_MISSING |
| golden_0077 | ACCOUNT_ACCESS | OTHER |
| golden_0078 | DELIVERY_MISSING | ORDER_STATUS |
| golden_0080 | DEVICE_ISSUE | OTHER |
| golden_0081 | REFUND_REQUEST | DELIVERY_LATE |
| golden_0082 | PAYMENT_ISSUE | OTHER |
| golden_0083 | DELIVERY_LATE | ORDER_STATUS |
| golden_0085 | PAYMENT_ISSUE | DELIVERY_MISSING |
| golden_0088 | DELIVERY_MISSING | DEVICE_ISSUE |
| golden_0089 | VIDEO_STREAMING | DELIVERY_LATE |
| golden_0090 | PRODUCT_ISSUE | OTHER |
| golden_0091 | DELIVERY_LATE | OTHER |
| golden_0101 | DELIVERY_MISSING | DELIVERY_LATE |
| golden_0103 | DELIVERY_LATE | APP_USAGE |
| golden_0104 | ACCOUNT_ACCESS | APP_USAGE |
| golden_0105 | DELIVERY_LATE | DELIVERY_MISSING |
| golden_0106 | PRODUCT_ISSUE | OTHER |
| golden_0108 | DELIVERY_LATE | OTHER |
| golden_0111 | ACCOUNT_ACCESS | OTHER |
| golden_0114 | DELIVERY_MISSING | DELIVERY_LATE |
| golden_0117 | REFUND_REQUEST | DELIVERY_MISSING |
| golden_0119 | DELIVERY_LATE | OTHER |
| golden_0120 | DELIVERY_LATE | OTHER |
| golden_0124 | DELIVERY_LATE | OTHER |
| golden_0125 | CANCELLATION | DELIVERY_MISSING |
| golden_0126 | DELIVERY_MISSING | OTHER |
| golden_0128 | DELIVERY_MISSING | OTHER |
| golden_0131 | VIDEO_STREAMING | DEVICE_ISSUE |
| golden_0133 | DELIVERY_MISSING | DELIVERY_LATE |
| golden_0135 | DELIVERY_MISSING | DEVICE_ISSUE |
| golden_0143 | PAYMENT_ISSUE | OTHER |
| golden_0144 | PRODUCT_ISSUE | DEVICE_ISSUE |
| golden_0145 | DELIVERY_MISSING | OTHER |
| golden_0147 | DELIVERY_MISSING | OTHER |
| golden_0149 | DELIVERY_LATE | ORDER_STATUS |
| golden_0150 | CANCELLATION | ORDER_STATUS |
| golden_0152 | DEVICE_ISSUE | APP_USAGE |
| golden_0155 | ACCOUNT_ACCESS | OTHER |
| golden_0157 | DELIVERY_MISSING | APP_USAGE |
| golden_0160 | DELIVERY_MISSING | OTHER |
| golden_0161 | PRODUCT_ISSUE | OTHER |
| golden_0162 | ORDER_STATUS | PRODUCT_ISSUE |
| golden_0167 | CANCELLATION | ORDER_STATUS |
| golden_0168 | DEVICE_ISSUE | OTHER |
| golden_0169 | DELIVERY_LATE | OTHER |
| golden_0171 | DELIVERY_TRACKING | DELIVERY_LATE |
| golden_0172 | REFUND_REQUEST | PAYMENT_ISSUE |
| golden_0175 | ACCOUNT_ACCESS | DELIVERY_LATE |
| golden_0177 | DELIVERY_LATE | OTHER |
| golden_0179 | ACCOUNT_ACCESS | APP_USAGE |
| golden_0181 | ACCOUNT_ACCESS | APP_USAGE |
| golden_0185 | RETURN_REQUEST | DELIVERY_LATE |
| golden_0188 | DELIVERY_LATE | ORDER_STATUS |
| golden_0192 | DELIVERY_LATE | APP_USAGE |
| golden_0193 | ORDER_STATUS | OTHER |
| golden_0195 | PRODUCT_ISSUE | DELIVERY_LATE |
| golden_0196 | DELIVERY_LATE | OTHER |
| golden_0197 | DELIVERY_LATE | OTHER |
| golden_0200 | ORDER_STATUS | PAYMENT_ISSUE |
| golden_0215 | DELIVERY_MISSING | CANCELLATION |
| golden_0218 | CANCELLATION | ORDER_MODIFY |
| golden_0220 | CANCELLATION | ORDER_MODIFY |

**Total misclassified:** 96

---

## Class Balance Assessment

| Metric | Value |
|--------|-------|
| Min examples per intent | 4 |
| Max examples per intent | 50 |
| Balance ratio (min/max) | 0.08 |
| OTHER intent ratio | 14.1% |

**Conclusion:** The class distribution is HIGHLY IMBALANCED.
The OTHER intent dominates (14.1% of examples), which means overall accuracy
may be heavily influenced by the model's performance on OTHER versus specific intents.
Accuracy alone may not reflect true model performance across all intents.

---

## Production Model Status

- **Model file:** data/baseline/phaseC_model.joblib
- **Model changed:** NO
- **Official Phase C test accuracy:** 71.11% (384/540 on held-out test set)
- **This evaluation:** Independent golden-set evaluation with human-verified labels

---

*Report generated automatically*
*This evaluation is INDEPENDENT and must NOT be presented as the official 71.11% Phase C test accuracy.*

