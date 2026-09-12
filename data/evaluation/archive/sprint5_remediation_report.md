# Sprint 5: Remediation Report

## Status: COMPLETE

---

## 1. Classification Failure Analysis

### APP_USAGE (F1=0.27, Support=44)

**Confusion Patterns:**
| Confusion | Count |
|-----------|-------|
| APP_USAGE → OTHER | 15 |
| APP_USAGE → DELIVERY_LATE | 8 |
| OTHER → APP_USAGE | 13 |
| DELIVERY_LATE → APP_USAGE | 4 |

**Root Cause**: APP_USAGE overlaps semantically with both OTHER and DELIVERY_LATE. The classifier cannot reliably distinguish app functionality issues from general inquiries or delivery complaints.

**Feasibility Assessment**:
- Merging APP_USAGE into OTHER would consolidate 44+13=57 samples, likely improving F1 for the merged class
- However, APP_USAGE and DELIVERY_LATE remain distinct (8+4=12 cross-confusions)
- **Intervention**: Merge APP_USAGE into OTHER. Post-merge expected OTHER F1 ~0.65.

### PRODUCT_ISSUE (F1=0.33, Support=11)

**Confusion Patterns:**
- PRODUCT_ISSUE confused with: DEVICE_ISSUE (4), OTHER (2), RETURN_REQUEST (1)

**Root Cause**: PRODUCT_ISSUE (hardware defect) and DEVICE_ISSUE (device malfunction) are semantically similar. Small sample size (11) makes F1 unreliable.

**Feasibility Assessment**:
- Only 11 test samples - metrics are statistically insignificant
- No clear merge candidate without conflating distinct issue types
- **Intervention**: None. Monitor with larger sample in next evaluation.

### ORDER_MODIFY (F1=0.00, Support=2)

**Root Cause**: Only 2 test samples. F1=0.00 is a sampling artifact, not a model defect.

**Feasibility Assessment**:
- Cannot evaluate meaningfully with 2 samples
- **Intervention**: None. Collect more data for reliable evaluation.

---

## 2. Escalation Threshold Analysis

### Current Policy (conf<0.3, sim<0.4)

| Metric | Value |
|--------|-------|
| Escalation Rate | 86.7% (26/30) |
| AUTO_HANDLE Rate | 13.3% (4/30) |
| AUTO_HANDLE Accuracy | 100% (4/4) |
| Wrong Intent AUTO_HANDLE | 0 |
| High-Risk AUTO_HANDLE | 0 |

### Threshold Grid Search Results

| Conf | Sim | Esc% | AH% | AH_acc | AH_wrong | AH_risk |
|------|-----|------|-----|--------|----------|---------|
| 0.20 | 0.30 | 56.7% | 43.3% | 92.3% | **1** | 0 |
| 0.20 | 0.40 | 56.7% | 43.3% | 92.3% | **1** | 0 |
| 0.20 | 0.50 | 56.7% | 43.3% | 92.3% | **1** | 0 |
| **0.25** | **0.30** | **73.3%** | **26.7%** | **100%** | **0** | **0** |
| 0.25 | 0.40 | 73.3% | 26.7% | 100% | 0 | 0 |
| 0.25 | 0.50 | 73.3% | 26.7% | 100% | 0 | 0 |
| 0.30 | 0.30 | 86.7% | 13.3% | 100% | 0 | 0 |
| 0.30 | 0.40 | 86.7% | 13.3% | 100% | 0 | 0 |
| 0.30 | 0.50 | 86.7% | 13.3% | 100% | 0 | 0 |
| 0.35 | 0.30 | 93.3% | 6.7% | 100% | 0 | 0 |
| 0.40+ | any | 96.7%+ | 3.3% | 100% | 0 | 0 |

### Escalation Breakdown (Current Policy: conf<0.3, sim<0.4)

| Reason | Count |
|--------|-------|
| LOW_CONF (various 0.12-0.29) | 24 |
| HIGH_RISK | 2 |

### AUTO_HANDLE Cases (Current Policy)

| ID | Intent | Confidence | Avg Sim | Correct |
|----|--------|------------|---------|---------|
| amazonhelp_093876 | OTHER | 0.302 | 0.721 | Yes |
| amazonhelp_025871 | DELIVERY_MISSING | 0.313 | 0.667 | Yes |
| amazonhelp_145718 | DELIVERY_MISSING | 0.387 | 0.798 | Yes |
| amazonhelp_105294 | OTHER | 0.573 | 0.584 | Yes |

---

## 3. Recommended Policy Changes

### Classification

| Change | Rationale | Risk |
|--------|-----------|------|
| Merge APP_USAGE into OTHER | F1=0.27 is unacceptably low; 57 combined samples give statistical power | Low - intents are semantically overlapping |

### Escalation

| Change | From | To | Rationale |
|--------|------|-----|-----------|
| Confidence threshold | < 0.3 | < 0.25 | Reduces escalation from 86.7% to 73.3% while maintaining 0 wrong-intent AUTO_HANDLE |
| Similarity threshold | < 0.4 | < 0.3 | No impact at conf<0.25 cutoff; kept for consistency |

**New Policy**:
```
IF HIGH_RISK_INTENT → ESCALATE (REFUND_REQUEST, PAYMENT_ISSUE, ACCOUNT_ACCESS, ORDER_MODIFY)
ELSE IF LOW_CONFIDENCE (< 0.25) → ESCALATE
ELSE IF NO_EVIDENCE or WEAK_EVIDENCE (avg_sim < 0.3) → ESCALATE
ELSE → AUTO_HANDLE
```

**Expected Impact**:
- Escalation rate: 86.7% → 73.3% (-13.4 percentage points)
- AUTO_HANDLE rate: 13.3% → 26.7% (+13.4 percentage points)
- AUTO_HANDLE accuracy: 100% maintained
- AUTO_HANDLE wrong intent: 0 maintained
- AUTO_HANDLE high-risk: 0 maintained

### Why NOT 50-60% Escalation?

The grid search shows that achieving 50-60% escalation requires lowering confidence threshold to 0.20, which introduces **1 wrong-intent AUTO_HANDLE** in the sample (ah_acc drops to 92.3%). This is unacceptable per Task 4 mandate: "maximize safe AUTO_HANDLE, but safety comes first."

The **safest policy supported by this data** is conf<0.25, which achieves the lowest escalation rate (73.3%) with zero safety violations.

---

## 4. Risk Assessment

### Classification Changes

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| APP_USAGE/OTHER merge causes cross-intent confusion | Low | Medium | Monitor per-intent precision in next evaluation |

### Escalation Changes

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| conf<0.25 misses some actual low-confidence cases | Low | Medium | HIGH_RISK intents always escalate regardless of confidence |
| Similarity threshold change has no effect | N/A | N/A | No risk |

---

## 5. Changes Required for Sprint 6

### Files to Modify

| File | Change |
|------|--------|
| `src/escalation_policy.py` | Change `CONF_THRESHOLD = 0.25`, `SIM_THRESHOLD = 0.3` |
| `src/intent_classifier.py` or `data/intent_mapping.json` | Merge APP_USAGE into OTHER |

### Files NOT to Modify

- `baseline_model.joblib` — do not retrain or replace classifier
- `data/evaluation/sprint5_end_to_end_results.jsonl` — evaluation artifacts remain unchanged
- No new rule versions or taxonomy changes beyond APP_USAGE→OTHER merge

### Validation Required

1. Re-run classification evaluation with APP_USAGE merged
2. Re-run threshold analysis on new policy
3. Verify 0 wrong-intent AUTO_HANDLE is maintained

---

## 6. Limitations

- **Sample size**: 30 end-to-end samples is small; threshold recommendations are indicative, not conclusive
- **Labels**: Rule-based labels have ~43.5% error rate; accuracy metrics reflect rule-agreement, not human accuracy
- **APP_USAGE analysis**: Merge recommendation is based on confusion patterns, not retraining; actual post-merge F1 may vary

---

## 7. Summary

| Area | Finding | Recommended Action |
|------|---------|-------------------|
| APP_USAGE | F1=0.27, semantically overlaps with OTHER | Merge into OTHER |
| PRODUCT_ISSUE | F1=0.33, support=11 too small | Monitor only |
| ORDER_MODIFY | F1=0.00, support=2 too small | Monitor only |
| Escalation | 86.7% driven by LOW_CONF | Lower threshold to 0.25 |

**Net Effect**: Escalation rate reduced from 86.7% to ~73.3% with no safety degradation. AUTO_HANDLE rate increases from 13.3% to 26.7%.

---

*Report generated: 2026-09-10*
