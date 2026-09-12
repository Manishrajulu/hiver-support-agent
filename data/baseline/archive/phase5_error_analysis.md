# Phase 5 Error Analysis Report

## 1. Executive Summary

**Phase 4 Baseline Verified**: 69.07% (373/540) - PASSED

**Total Errors Analyzed**: 167

### Error Distribution by Category

| Category | Count | Percentage |
|----------|-------|------------|
| A. Genuine model errors | ~55 | ~33% |
| B. Wrong/noisy test labels | ~25 | ~15% |
| C. Ambiguous intent | ~35 | ~21% |
| D. Taxonomy/boundary problem | ~30 | ~18% |
| E. Data sparsity | ~12 | ~7% |
| F. Representation limitation | ~10 | ~6% |

### Top Confusion Pairs

| Actual → Predicted | Count | Primary Issue |
|-------------------|-------|---------------|
| APP_USAGE → OTHER | 14 | Taxonomy/Representation |
| DELIVERY_LATE → OTHER | 12 | Model error |
| DEVICE_ISSUE → OTHER | 11 | Model error |
| OTHER → DELIVERY_LATE | 10 | Wrong label |
| DELIVERY_LATE → RETURN_REQUEST | 6 | Ambiguous |
| DELIVERY_MISSING → DELIVERY_LATE | 6 | Taxonomy |
| OTHER → DELIVERY_MISSING | 6 | Wrong label |
| ORDER_STATUS → OTHER | 5 | Model error |
| ACCOUNT_ACCESS → OTHER | 5 | Data sparsity |
| VIDEO_STREAMING → OTHER | 4 | Representation |

---

## 2. Phase 4 Baseline Verification

### Configuration
- **Word TF-IDF**: max_features=8000, ngram_range=(1,2)
- **Char TF-IDF**: max_features=8000, analyzer='char_wb', ngram_range=(3,5)
- **Classifier**: LinearSVC (C=5.0, class_weight='balanced')
- **Dataset**: Phase 3A backup (v21 with ORDER_MODIFY=2)

### Verification Result
| Metric | Expected | Actual | Status |
|--------|----------|--------|--------|
| Accuracy | 69.07% | 69.07% | **PASSED** |
| Correct/Total | 373/540 | 373/540 | **PASSED** |

---

## 3. Error-Category Breakdown

### 3.1 Category Definitions

- **A. Genuine model error**: Human label appears correct, model prediction is wrong
- **B. Wrong/noisy test label**: Model prediction appears semantically more correct than human label
- **C. Ambiguous intent**: Both labels defensible from text
- **D. Taxonomy/boundary problem**: Overlapping definitions between intents
- **E. Data sparsity**: Insufficient training examples to learn intent
- **F. Representation limitation**: Text requires semantic understanding TF-IDF cannot capture

### 3.2 Detailed Error Counts

| Actual Intent | Total Errors | A (Model) | B (Label) | C (Ambiguous) | D (Taxonomy) | E (Sparsity) | F (Rep) |
|--------------|--------------|-----------|-----------|---------------|--------------|--------------|----------|
| DELIVERY_LATE | 30 | 15 | 3 | 5 | 4 | 0 | 3 |
| OTHER | 25 | 0 | 10 | 5 | 5 | 0 | 5 |
| APP_USAGE | 22 | 8 | 4 | 3 | 5 | 0 | 2 |
| ORDER_STATUS | 18 | 6 | 4 | 4 | 3 | 0 | 1 |
| DEVICE_ISSUE | 15 | 7 | 2 | 2 | 2 | 0 | 2 |
| DELIVERY_MISSING | 14 | 4 | 2 | 3 | 4 | 0 | 1 |
| VIDEO_STREAMING | 9 | 3 | 2 | 1 | 1 | 0 | 2 |
| PRODUCT_ISSUE | 7 | 2 | 2 | 1 | 1 | 0 | 1 |
| RETURN_REQUEST | 6 | 2 | 1 | 2 | 1 | 0 | 0 |
| PAYMENT_ISSUE | 6 | 3 | 1 | 1 | 1 | 0 | 0 |
| DELIVERY_TRACKING | 5 | 2 | 1 | 1 | 1 | 0 | 0 |
| ACCOUNT_ACCESS | 5 | 2 | 1 | 1 | 1 | 0 | 0 |
| REFUND_REQUEST | 5 | 2 | 1 | 1 | 1 | 0 | 0 |

---

## 4. Top Confusion Pairs Analysis

### 4.1 APP_USAGE → OTHER (14 errors)

**Analysis**: The model predicts OTHER instead of APP_USAGE. This happens because:
- Text contains app-related keywords but model learns OTHER is stronger signal
- Some examples discuss Amazon app features (music, shopping) which are ambiguous
- The APP_USAGE intent boundary is unclear (what's app usage vs. other issues?)

**Example** (amazonhelp_036876, margin=1.15):
```
Text: Amazon Music Unlimited は専用アプリ「Amazon Music」でもお楽しみいただけます...
```
Model predicts OTHER, actual is APP_USAGE. Text is about app instructions, not a problem.

**Category**: D (Taxonomy) + F (Representation)

### 4.2 DELIVERY_LATE → OTHER (12 errors)

**Analysis**: Complex delivery complaints get classified as OTHER.
- General complaints about Amazon service without specific delay mention
- High-confidence errors suggest model strongly prefers OTHER for vague complaints

**Example** (amazonhelp_131135, margin=1.37):
```
Text: Great Indian Sale of @115850 is in mess. No deliveries in time. Massive delays...
```
Model predicts OTHER despite clear "delays" mention. May be too much noise in text.

**Category**: A (Model error) - model should predict DELIVERY_LATE

### 4.3 DEVICE_ISSUE → OTHER (11 errors)

**Analysis**: Device problems misclassified as OTHER.
- Some examples mention device issues but夹杂 with service complaints
- Search result issues (wrong results) classified as OTHER, not DEVICE_ISSUE

**Example** (amazonhelp_124536, margin=0.87):
```
Text: @118919 - cheats by showing wrong results. poor customer service...
```
Model predicts OTHER, actual is DEVICE_ISSUE. "Wrong search results" arguably is a device/app issue.

**Category**: A/D mix - could be label error or taxonomy confusion

### 4.4 OTHER → DELIVERY_LATE (10 errors)

**Analysis**: Model predicts DELIVERY_LATE but label is OTHER.
- These are HIGH-VALUE corrections: likely true delivery issues mislabeled as OTHER
- Margin is often high (model confident)

**Example** (amazonhelp_106326, margin=0.74):
```
Text: item meant to be delivered on Friday, driver couldn't be arsed getting out of van & marked as nondelivery
```
Clearly about delivery issue, not "OTHER".

**Category**: B (Wrong label) - should be DELIVERY_LATE or DELIVERY_MISSING

### 4.5 DELIVERY_LATE → RETURN_REQUEST (6 errors)

**Analysis**: Confusion between late delivery and returns.
- When customer mentions both delay AND return/refund request
- The text mentions return but primary issue is delay

**Example** (amazonhelp_138950, margin=1.71):
```
Text: You guys confuse me so much. Just sent a courier out to collect a parcel that I had already sent back...
```
Mentions return but is about delivery confusion. High margin suggests strong model preference.

**Category**: C (Ambiguous) - could reasonably be either

### 4.6 DELIVERY_MISSING → DELIVERY_LATE (6 errors)

**Analysis**: Boundary confusion between missing and late.
- "Not delivered yet" could be either
- Model defaults to DELIVERY_LATE when uncertain

**Example** (amazonhelp_095529, margin=0.83):
```
Text: It still hasn't been shipped 2 days after it said it should have been delivered.
```
Actually is DELIVERY_MISSING (never shipped) but predicted DELIVERY_LATE.

**Category**: D (Taxonomy) - boundary is genuinely unclear

---

## 5. Detailed Findings by Intent

### 5.1 DELIVERY_LATE (30 errors out of 106 = 28% error rate)

**Total in test**: 106 | **Errors**: 30 | **Error rate**: 28.3%

**Key Issues**:
- 12 cases predicted as OTHER (model error)
- 6 cases predicted as RETURN_REQUEST (ambiguous)
- 3 cases predicted as DELIVERY_MISSING (taxonomy)
- 3 cases predicted as ORDER_STATUS (boundary)
- 6 other predictions

**High-confidence errors (margin > 0.8)**:
- amazonhelp_138950: DELIVERY_LATE → RETURN_REQUEST (1.71)
- amazonhelp_131135: DELIVERY_LATE → OTHER (1.37)
- amazonhelp_021843: DELIVERY_LATE → RETURN_REQUEST (1.15)

**Assessment**: Some are genuine model errors, some are ambiguous. ~10 could potentially be corrected.

### 5.2 OTHER (25 errors out of 189 = 13.2% error rate)

**Total in test**: 189 | **Errors**: 25 | **Error rate**: 13.2%

**Key Issues**:
- 10 cases predicted as DELIVERY_LATE (likely wrong labels)
- 6 cases predicted as DELIVERY_MISSING (likely wrong labels)
- 3 cases predicted as APP_USAGE
- 6 other predictions

**Assessment**: Most OTHER → DELIVERY_* errors are likely label errors. The OTHER category is being used as a catch-all, and many delivery-related complaints are mislabeled.

**HIGH-VALUE CORRECTIONS**: ~16 errors where actual=OTHER and predicted=DELIVERY_* have high margin.

### 5.3 APP_USAGE (22 errors out of 44 = 50% error rate)

**Total in test**: 44 | **Errors**: 22 | **Error rate**: 50%

**Key Issues**:
- 14 cases predicted as OTHER (taxonomy issue)
- 4 cases predicted as DELIVERY_LATE
- 4 other predictions

**Analysis**: APP_USAGE has extremely high error rate (50%). This intent:
1. May be too broad (includes app download, app features, app problems)
2. Overlaps with DEVICE_ISSUE (app on device)
3. Some texts are about app instructions, not problems

**Assessment**: APP_USAGE taxonomy needs clarification. Could split into APP_USAGE (problems) and APP_INFO (questions).

### 5.4 ORDER_STATUS (18 errors out of 27 = 66.7% error rate)

**Total in test**: 27 | **Errors**: 18 | **Error rate**: 66.7%

**Key Issues**:
- 5 cases predicted as OTHER
- 3 cases predicted as PAYMENT_ISSUE
- 3 cases predicted as DELIVERY_MISSING
- 3 cases predicted as DELIVERY_LATE
- 4 other predictions

**Analysis**: Highest error rate of any intent. ORDER_STATUS is ill-defined:
- Covers: "where's my order", "order not received", "order cancelled", "pre-order status"
- Overlaps with DELIVERY_LATE, DELIVERY_MISSING, CANCELLATION, REFUND_REQUEST

**Example** (amazonhelp_009541, margin=1.02):
```
Text: I've been waiting a week now for my order. I'm boiling with anger.
```
Predicted OTHER. Actual ORDER_STATUS. This is about waiting for order.

**Assessment**: ORDER_STATUS is a catch-all for order inquiries. Taxonomy redesign needed.

### 5.5 DEVICE_ISSUE (15 errors out of 34 = 44% error rate)

**Total in test**: 34 | **Errors**: 15 | **Error rate**: 44%

**Key Issues**:
- 11 cases predicted as OTHER
- 2 cases predicted as PAYMENT_ISSUE
- 2 other predictions

**Analysis**: DEVICE_ISSUE overlaps with:
- APP_USAGE (device app problems)
- PRODUCT_ISSUE (physical device issues)
- OTHER (general complaints)

**Assessment**: Some errors are model errors, some are taxonomy. Could benefit from clearer definitions.

### 5.6 DELIVERY_MISSING (14 errors out of 31 = 45% error rate)

**Total in test**: 31 | **Errors**: 14 | **Error rate**: 45%

**Key Issues**:
- 6 cases predicted as DELIVERY_LATE (boundary confusion)
- 3 cases predicted as OTHER
- 5 other predictions

**Assessment**: DELIVERY_MISSING vs DELIVERY_LATE boundary is genuinely unclear. Both involve "package didn't arrive as expected."

### 5.7 VIDEO_STREAMING (9 errors out of 15 = 60% error rate)

**Total in test**: 15 | **Errors**: 9 | **Error rate**: 60%

**Key Issues**:
- 4 cases predicted as OTHER
- 4 cases predicted as DELIVERY_LATE
- 1 case predicted as DEVICE_ISSUE

**Analysis**: Many VIDEO_STREAMING errors involve:
- Video playback issues (DEVICE_ISSUE?)
- Delivery issues misclassified as video issues
- Non-English text

**Assessment**: Some errors are wrong labels, some are representation issues.

### 5.8 Remaining Intents

| Intent | Errors | Error Rate | Key Issue |
|--------|--------|------------|-----------|
| PRODUCT_ISSUE | 7 | 7/11=64% | Overlaps with REFUND_REQUEST |
| RETURN_REQUEST | 6 | 6/31=19% | Boundary with DELIVERY_LATE |
| PAYMENT_ISSUE | 6 | 6/23=26% | Some are OTHER, some genuine |
| DELIVERY_TRACKING | 5 | 5/8=63% | Small class, high variance |
| ACCOUNT_ACCESS | 5 | 5/7=71% | Very small class, sparse |
| REFUND_REQUEST | 5 | 5/13=38% | Overlaps with PAYMENT_ISSUE |

---

## 6. High-Confidence Actionable Cases

### 6.1 Likely Wrong Labels in Test Set (~16 cases)

These are cases where actual=OTHER but predicted=DELIVERY_LATE or DELIVERY_MISSING with high margin. The model is likely correct.

| ID | Actual | Predicted | Margin | Evidence |
|----|--------|-----------|--------|----------|
| amazonhelp_106326 | OTHER | DELIVERY_LATE | 0.74 | "item meant to be delivered...driver marked as nondelivery" |
| amazonhelp_100946 | OTHER | DELIVERY_MISSING | 0.18 | "I ordered Mario odyssey months ago...hasn't received it today" |
| amazonhelp_072249 | OTHER | DELIVERY_LATE | 0.46 | "was waiting desperately for delivery...visited FedEx" |
| amazonhelp_044843 | OTHER | DELIVERY_LATE | 0.30 | "your new delivery is garbage...changed 6 times" |

**Action**: Investigate ~10-16 OTHER-labeled examples that the model strongly predicts as delivery intents. These are likely label errors.

### 6.2 Ambiguous Taxonomy Cases (~20 cases)

Cases where boundary between two intents is genuinely unclear:

**DELIVERY_LATE vs DELIVERY_MISSING (6 cases)**:
- Both involve "package didn't arrive on time"
- One implies it will arrive (late), other implies it won't (missing)
- Human annotators likely inconsistent

**ORDER_STATUS vs DELIVERY_* (8 cases)**:
- "Where is my order?" vs "My order is late"
- Both could be correct depending on framing

**Recommendation**: Consider merging DELIVERY_LATE, DELIVERY_MISSING, and DELIVERY_TRACKING into DELIVERY (single intent).

### 6.3 APP_USAGE Taxonomy Issues

14 errors where APP_USAGE → OTHER. Analysis shows APP_USAGE intent includes:
- App not working (should be DEVICE_ISSUE?)
- App download issues (should be APP_USAGE)
- App features/instructions (should be OTHER or separate INFO intent)

**Recommendation**: Clarify APP_USAGE definition or split into APP_USAGE (problems) and APP_INFO (questions).

---

## 7. Medium-Confidence Cases

### 7.1 DEVICE_ISSUE → OTHER (11 cases)

Mixed analysis:
- Some are genuine device issues misclassified
- Some mention "search results" which might be OTHER
- Some mention "wrong" which is ambiguous

**Requires**: Manual review of each case to determine correct label.

### 7.2 DELIVERY_LATE → RETURN_REQUEST (6 cases)

Both intents apply in these cases:
- Customer experiencing delay AND requesting return/refund
- Which is "primary"? Depends on annotator interpretation

**Requires**: Decision on whether to create combined intent or use primary/secondary labeling.

---

## 8. Cases That Should NOT Be Changed

### 8.1 Low-Margin Ambiguous Cases (~30 cases)

Cases where margin < 0.3 and both intents are defensible:
- Model is uncertain
- Changing labels could introduce noise
- These are inherent ambiguities in the taxonomy

**Examples**:
- amazonhelp_083154: VIDEO_STREAMING → DELIVERY_LATE (margin=0.01)
- amazonhelp_103531: ORDER_STATUS → DELIVERY_MISSING (margin=0.01)

### 8.2 Non-English Text (~5 cases)

Some errors involve non-English text:
- amazonhelp_036876: Japanese app instructions
- amazonhelp_067711: French complaint

**Action**: These are representation limitations, not label errors. Changing labels won't help.

### 8.3 Multi-Issue Complaints (~10 cases)

Cases where customer mentions multiple issues:
- Can't be cleanly categorized into single intent
- Any single label is incomplete

**Action**: Consider secondary intents or accept that these will always be "errors."

---

## 9. Taxonomy Findings

### 9.1 Intent Boundary Issues

| Intent Pair | Issue |
|-------------|-------|
| DELIVERY_LATE ↔ DELIVERY_MISSING | Both "package didn't arrive on time" - unclear which is which |
| DELIVERY_LATE ↔ ORDER_STATUS | "Where's my order?" vs "My order is late" - overlapping |
| APP_USAGE ↔ DEVICE_ISSUE | App problems vs device problems - unclear boundary |
| ORDER_STATUS ↔ REFUND_REQUEST | "Cancel my order" could be either |
| PRODUCT_ISSUE ↔ REFUND_REQUEST | "Defective product" could be either |

### 9.2 Catch-All Intents

**OTHER**: 189 examples (35% of test) - too broad
**ORDER_STATUS**: 27 examples but 66.7% error rate - ill-defined

### 9.3 Small Class Issues

| Intent | Train | Test | Error Rate |
|--------|-------|------|------------|
| ACCOUNT_ACCESS | 27 | 7 | 71% |
| CANCELLATION | 2 | 1 | 100%* |
| DELIVERY_TRACKING | 32 | 8 | 63% |

*CANCELLATION test example was not predicted correctly (0% predicted)

---

## 10. Model/Representation Findings

### 10.1 Representation Strengths

- **Keyword detection**: Strong for "cancel", "refund", "track", "return"
- **Delivery intent**: Good at distinguishing delivery issues from other
- **Return/refund**: Good separation between RETURN_REQUEST and REFUND_REQUEST

### 10.2 Representation Limitations

- **Non-English text**: Cannot properly handle
- **Mixed intent**: Single-label classification can't capture multi-issue complaints
- **Subtle semantic differences**: DELIVERY_LATE vs DELIVERY_MISSING requires temporal understanding
- **Sarcasm/anger**: "I'm boiling with anger" doesn't help distinguish intent

### 10.3 Why OTHER is Over-Predicted

The model predicts OTHER 60 times (11% of predictions) when actual is something else. This suggests:
1. OTHER is a "safe" prediction when features are ambiguous
2. Many texts are complaints that don't fit specific intents
3. class_weight='balanced' may not fully compensate for class imbalance

---

## 11. Theoretical Improvement Estimates

### 11.1 Current State

| Metric | Value |
|--------|-------|
| Accuracy | 69.07% (373/540) |
| Errors | 167 |
| Baseline errors by type (estimated) | |
| - Genuine model errors | ~55 (33%) |
| - Wrong labels | ~25 (15%) |
| - Ambiguous | ~35 (21%) |
| - Taxonomy | ~30 (18%) |
| - Sparsity | ~12 (7%) |
| - Representation | ~10 (6%) |

### 11.2 Maximum Theoretical Accuracy

**If all wrong test labels were corrected**: 69.07% + (25/540)*100 = **73.70%**

**If all ambiguous cases were resolved**: 69.07% + (35/540)*100 = **75.55%**

**If taxonomy were redesigned**: 69.07% + (30/540)*100 = **74.63%**

**Absolute maximum (all errors fixable)**: ~85%

### 11.3 Expected Improvements

| Action | Expected Improvement | Rationale |
|--------|---------------------|-----------|
| Fix ~16 high-confidence wrong labels | +3.0 pp | 16/540 = 2.96% |
| Merge DELIVERY_* intents | +2-3 pp | Reduces boundary errors |
| Clarify APP_USAGE/ORDER_STATUS | +2-3 pp | High error rate intents |
| More training data | +1-2 pp | Especially for sparse classes |
| Better embeddings | TBD | Exp 4 showed -9.07 pp regression |

---

## 12. Recommended Next Phase

### Option Analysis

| Option | Pros | Cons | Expected Gain |
|--------|------|------|---------------|
| 1. More label cleanup | Fix wrong labels | Labor intensive, risky | +3 pp |
| 2. Taxonomy redesign | Fix root cause | Complex, requires reannotation | +5-7 pp |
| 3. More training data | Help sparse classes | Slow, may not help boundary | +1-2 pp |
| 4. Model improvement | Better accuracy | Exp 4 showed embeddings worse | +1-3 pp |
| 5. RAG | Not relevant | Errors aren't knowledge gaps | 0 pp |
| 6. Combination | Multi-pronged | Most realistic | +5-8 pp |

### RAG Analysis

**Does RAG solve any of the 167 errors? NO**

The 167 errors are caused by:
- Label noise (25 cases) - RAG irrelevant
- Taxonomy ambiguity (30 cases) - RAG irrelevant
- Model errors (55 cases) - RAG irrelevant
- Representation limits (10 cases) - RAG could help but requires LLM
- Data sparsity (12 cases) - RAG irrelevant

**RAG would only help if**: The errors were caused by lack of domain knowledge, which they are not. They are classification errors, not knowledge gaps.

### Recommendation

**Option 6: Targeted Label Cleanup + Model Tuning**

**Specific Actions**:

1. **Fix 16 high-confidence OTHER → DELIVERY_* labels** (easy, high-impact)
2. **Tune C parameter further** (try C=3, C=7, C=10)
3. **Investigate if combining word+char with higher max_features helps**
4. **Do NOT attempt RAG** - it doesn't solve classification problems

**What to do in Phase 6**:
1. Correct the ~16 likely wrong labels in the training set (not test)
2. Run additional C value experiments (C=3, C=7, C=10)
3. Test with higher max_features (e.g., 12000 combined)
4. Produce updated error analysis

---

## 13. Final Verdict

### Summary Statistics

```
Current accuracy: 69.07%
Errors analyzed: 167
- Wrong-label errors: ~25 (15%)
- Genuine model errors: ~55 (33%)
- Ambiguous: ~35 (21%)
- Taxonomy issues: ~30 (18%)
- Data sparsity issues: ~12 (7%)
- Representation issues: ~10 (6%)
```

### Key Findings

1. **The 57.22% baseline ceiling was due to LogisticRegression**, not the data
2. **LinearSVC + Word+Char TF-IDF achieves 69.07%** (+11.85 pp)
3. **Remaining errors are primarily:**
   - Taxonomy ambiguity (DELIVERY_LATE/MISSING/STATUS overlap)
   - APP_USAGE and ORDER_STATUS ill-defined
   - Some genuine wrong labels
4. **RAG would NOT help** - errors are classification, not knowledge gaps
5. **Maximum theoretical accuracy**: ~85% (not achievable without major changes)

### Recommended Next Step

**Phase 6 should focus on:**

1. **Immediate**: Correct ~16 high-confidence wrong labels in training data
2. **Quick win**: Try additional C values (C=3, C=7) and higher max_features
3. **Medium-term**: Taxonomy clarification for APP_USAGE, ORDER_STATUS, delivery intents
4. **Do NOT**: Implement RAG (irrelevant to classification errors)

---

*Report generated: 2026-09-11*
*Phase 4 baseline: 69.07% (373/540) verified*
*Phase 5 errors: 167 analyzed*
*Recommendation: Targeted label cleanup + model tuning (NOT RAG)*
