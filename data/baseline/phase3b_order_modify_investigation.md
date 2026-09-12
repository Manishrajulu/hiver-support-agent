# Phase 3B: ORDER_MODIFY Investigation Report

## 1. Executive Summary

**Recommendation: RELABEL INDIVIDUAL EXAMPLES**

ORDER_MODIFY has only 2 examples in the entire dataset (both in training set, 0 in test). Neither example actually represents an order modification intent. The correct action is to relabel each example to its proper intent rather than merging into a broader class.

### Key Findings

| Metric | Value |
|--------|-------|
| ORDER_MODIFY examples in dataset | 2 |
| In training set | 2 |
| In test set | **0** |
| In Phase 3A predictions | 0 |
| CANCELLATION examples | 3 |
| ORDER_STATUS examples | 138 |

### Options Analysis

| Option | Action | Impact |
|--------|--------|--------|
| A. ORDER_MODIFY → ORDER_STATUS | Merge into ORDER_STATUS | Adds 2 noisy examples to 138 |
| B. ORDER_MODIFY → CANCELLATION | Merge into CANCELLATION | Adds 2 examples to 3 |
| C. Relabel individually | DELIVERY_LATE + CANCELLATION | Correct intent per example |
| D. Keep unchanged | Do nothing | Retain meaningless class |

**Recommended: Option C - Relabel individually**

---

## 2. Files Inspected

| File | Purpose |
|------|---------|
| `data/processed/amazonhelp_labeled_conversations_v21.jsonl` | Current dataset |
| `data/baseline/baseline_train_test_split.json` | Official train/test split |
| `data/baseline/phase3a_final_predictions.jsonl` | Phase 3A predictions |
| `data/baseline/phase3a_corrections_verified.json` | Phase 3A corrections |
| `data/baseline/phase3a_corrections.json` | Phase 3A correction candidates |
| `data/baseline/phase3_review_report.md` | Phase 3 review findings |

---

## 3. Current Dataset Counts

### 3.1 ORDER-RELATED Intents

| Intent | Train | Test | Total |
|--------|-------|------|-------|
| ORDER_MODIFY | 2 | 0 | 2 |
| ORDER_STATUS | 111 | 27 | 138 |
| CANCELLATION | 2 | 1 | 3 |
| DELIVERY_LATE | 426 | 106 | 532 |
| DELIVERY_MISSING | 124 | 31 | 155 |
| DELIVERY_TRACKING | 32 | 8 | 40 |

### 3.2 ORDER_MODIFY Examples in Detail

| ID | Location | Text | Current Label | Should Be |
|----|----------|------|--------------|----------|
| amazonhelp_073655 | Train | "ORDER #...will take over a month to reach... how?? So you want me to cancel my order" | ORDER_MODIFY | DELIVERY_LATE |
| amazonhelp_135737 | Train | "by mistake I cancel my order can u pls revert back" | ORDER_MODIFY | CANCELLATION |

### 3.3 CANCELLATION Examples

| ID | Location | Text (truncated) | Label |
|----|----------|------------------|-------|
| amazonhelp_101641 | Train | "i want to cancel my order but there is no option of cancellation" | CANCELLATION |
| amazonhelp_137758 | Test | "I'd like to cancel my order and just get my money back" | CANCELLATION |
| amazonhelp_143853 | Train | "would like to cancel order and cancel prime account" | CANCELLATION |

---

## 4. Test Set Analysis

### 4.1 Does ORDER_MODIFY appear in test?

| Metric | Value |
|--------|-------|
| ORDER_MODIFY in test (actual) | **0** |
| ORDER_MODIFY in test (predicted) | **0** |
| CANCELLATION in test | 1 |

**ORDER_MODIFY does NOT appear in the official test set at all.**

### 4.2 Impact on Test Set

Since ORDER_MODIFY does not appear in the test set:
- Changing ORDER_MODIFY labels in training does NOT affect test accuracy
- The official test set does NOT need to be regenerated
- Phase 3A's 57.22% baseline remains valid for comparison

---

## 5. Historical Analysis

### 5.1 ORDER_MODIFY Evolution

| Dataset | ORDER_MODIFY Count | CANCELLATION Count |
|---------|-------------------|-------------------|
| Original (V1) | 17 | 0 |
| v2 | 9 | 0 |
| v21_backup | 8 | 0 |
| Current v21 | 2 | 3 |

### 5.2 What Happened to Original ORDER_MODIFY?

Of the 17 original ORDER_MODIFY examples:

| Original → Current | Count |
|-------------------|-------|
| ORDER_MODIFY → ORDER_STATUS | 5 |
| ORDER_MODIFY → PAYMENT_ISSUE | 5 |
| ORDER_MODIFY → CANCELLATION | 3 |
| ORDER_MODIFY → OTHER | 2 |
| ORDER_MODIFY → DEVICE_ISSUE | 1 |
| ORDER_MODIFY → ORDER_MODIFY (still) | 2 |

**The cleanup already moved most ORDER_MODIFY examples to more appropriate intents.**

---

## 6. Intent Coherence Analysis

### 6.1 Does ORDER_MODIFY represent a coherent intent?

**NO.** Neither of the 2 remaining ORDER_MODIFY examples represents an actual order modification:

1. **amazonhelp_073655**: About delivery time ("will take over a month to reach") - should be DELIVERY_LATE
2. **amazonhelp_135737**: About canceling a cancellation ("by mistake I cancel my order") - should be CANCELLATION

### 6.2 Comparison with Related Intents

| Intent | Definition | Examples |
|--------|------------|----------|
| ORDER_MODIFY | "Modify an existing order" | **NONE** (0 examples) |
| ORDER_STATUS | General order inquiry | "Has my order shipped?" |
| CANCELLATION | Request to cancel order | "I want to cancel my order" |
| DELIVERY_LATE | Package did not arrive on time | "My package is late" |

### 6.3 Ambiguity Analysis

If ORDER_MODIFY were merged into ORDER_STATUS:
- Would ORDER_STATUS become too broad? ORDER_STATUS has 138 examples, adding 2 would be +1.4%
- Would this create ambiguity? No significant increase

If ORDER_MODIFY were merged into CANCELLATION:
- CANCELLATION would grow from 3 to 5 examples
- Still a very small class
- But examples are correctly categorized

---

## 7. Option Analysis

### 7.1 Option A: Merge into ORDER_STATUS

| Aspect | Assessment |
|--------|------------|
| Training impact | +2 examples to ORDER_STATUS (2 → 140) |
| Test impact | None (ORDER_MODIFY not in test) |
| Taxonomic clarity | Reduces clarity - ORDER_MODIFY examples aren't about status |
| Expected accuracy impact | Neutral to slight negative (adds noise) |

### 7.2 Option B: Merge into CANCELLATION

| Aspect | Assessment |
|--------|------------|
| Training impact | +2 examples to CANCELLATION (3 → 5) |
| Test impact | None (ORDER_MODIFY not in test) |
| Taxonomic clarity | Good - examples are about cancellation |
| Expected accuracy impact | Neutral to slight positive |

### 7.3 Option C: Relabel Individually (RECOMMENDED)

| Aspect | Assessment |
|--------|------------|
| Training impact | amazonhelp_073655 → DELIVERY_LATE, amazonhelp_135737 → CANCELLATION |
| Test impact | None |
| Taxonomic clarity | **Maximizes clarity** - each example in correct intent |
| Expected accuracy impact | **Positive** - better label signal |

### 7.4 Option D: Keep Unchanged

| Aspect | Assessment |
|--------|------------|
| Training impact | No change |
| Test impact | None |
| Taxonomic clarity | Poor - ORDER_MODIFY has 0 valid examples |
| Expected accuracy impact | Neutral (but keeps meaningless class) |

---

## 8. Impact on Official Test Set

### 8.1 Question: Does ORDER_MODIFY appear in test?

**Answer: NO**

| Split | ORDER_MODIFY | CANCELLATION | ORDER_STATUS |
|-------|-------------|--------------|--------------|
| Train | 2 | 2 | 111 |
| Test | **0** | 1 | 27 |
| Total | 2 | 3 | 138 |

### 8.2 Does changing training labels affect test accuracy?

**No.** Since both ORDER_MODIFY examples are in the training set and 0 are in the test set:
- Any relabeling in training does NOT affect test predictions
- The 57.22% Phase 3A baseline remains valid
- No need to regenerate test set

### 8.3 Can we evaluate fairly against Phase 3A?

**Yes.** The comparison is:
- Same dataset (v21)
- Same train/test split
- Same model configuration
- Only difference: ORDER_MODIFY labels changed

---

## 9. Detailed Example Analysis

### 9.1 amazonhelp_073655

**Current label**: ORDER_MODIFY

**Full text**:
```
.@115850 ORDER # 403-1563848-1833109 will take over a month to reach gujarat??? how ??? @AmazonHelp So you want me to cancel my order placed??? @119350 @AmazonHelp DM them.. @384052 @AmazonHelp Be hosiyaari DM ke liye follow karana padta hai pehle @119350 @AmazonHelp I have that option. Poor thing @384052 @AmazonHelp You rant so much . They have given you that privilege @119350 @AmazonHelp I speak point to point. I don't whine @384052 @AmazonHelp I don't whine. I fight for my right .. bloody 25 days to deliver a book @AmazonHelp I didn't any link . It just said if you want to cancel it
```

**Analysis**:
- Primary concern: delivery time ("will take over a month to reach", "25 days to deliver a book")
- Mentions "cancel my order" but only in passing
- **Should be**: DELIVERY_LATE

### 9.2 amazonhelp_135737

**Current label**: ORDER_MODIFY

**Full text**:
```
@115850 by mistake I cancel my order can u pls revert back and delivered to me asap. @115850 Order # 408-0365818-9451558  pls arrange delivery of my order by mistake it has been canceled by me 2day morning but I need this asap.
```

**Analysis**:
- Explicitly about canceling and reverting a cancellation
- "by mistake I cancel my order"
- "it has been canceled by me"
- **Should be**: CANCELLATION

---

## 10. Recommendation

### 10.1 Final Recommendation: RELABEL INDIVIDUALLY

**Action Plan**:
1. Relabel amazonhelp_073655: ORDER_MODIFY → DELIVERY_LATE
2. Relabel amazonhelp_135737: ORDER_MODIFY → CANCELLATION
3. ORDER_MODIFY class becomes empty and can be removed

### 10.2 Rationale

| Reason | Explanation |
|--------|-------------|
| Correct intent | Each example goes to its actual intent |
| No test impact | Both examples are in training set |
| No baseline change | 57.22% comparison remains valid |
| Clean taxonomy | Removes meaningless ORDER_MODIFY class |
| Supported by evidence | Both texts clearly indicate other intents |

### 10.3 What NOT to do

| Option | Why Not |
|--------|---------|
| Merge into ORDER_STATUS | Examples aren't about order status |
| Merge into CANCELLATION | One example is about delivery, not cancellation |
| Keep unchanged | ORDER_MODIFY has no valid examples |

### 10.4 Expected Outcome

| Metric | Current | After Relabeling |
|--------|---------|------------------|
| ORDER_MODIFY count | 2 | 0 (class removed) |
| DELIVERY_LATE count | 532 | 533 |
| CANCELLATION count | 3 | 4 |
| Test set | Unchanged | Unchanged |
| Phase 3A baseline | 57.22% | Valid for comparison |

---

## 11. Verification Checklist

| Item | Status |
|------|--------|
| Verified ORDER_MODIFY examples | ✓ 2 total, both in training |
| Verified test set has 0 ORDER_MODIFY | ✓ |
| Verified CANCELLATION examples | ✓ 3 total (1 test, 2 train) |
| Verified ORDER_STATUS examples | ✓ 138 total (27 test, 111 train) |
| Verified phase3a_corrections_verified.json | ✓ Neither ORDER_MODIFY ID in file |
| Verified historical lineage | ✓ From 17 to 2 through cleanup |
| Verified test impact | ✓ None - 0 ORDER_MODIFY in test |
| Verified Phase 3A baseline | ✓ 57.22% remains valid |

---

## 12. Conclusion

ORDER_MODIFY is a meaningless class with 2 examples that should not exist. Both examples clearly belong to other intents:
- One is about DELIVERY_LATE (delivery time concern)
- One is about CANCELLATION (canceling an order)

**Recommendation: RELABEL INDIVIDUALLY**

This action:
- Places each example in its correct intent
- Removes the meaningless ORDER_MODIFY class
- Does NOT affect the test set
- Does NOT invalidate the Phase 3A 57.22% baseline
- Requires no regeneration of train/test split

---

*Report generated: 2026-09-10*
*Investigation by: Claude Code*
*Status: COMPLETE - No files modified*
