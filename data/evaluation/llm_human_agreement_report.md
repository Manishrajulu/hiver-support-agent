# LLM-as-Judge vs Human Agreement Report

## Executive Summary

**Evaluation Completed: 40 examples (LLM judge) vs 17 examples (human)**

| Metric | Value |
|--------|-------|
| LLM Judge Evaluated | 40/40 examples |
| Human Reviews Available | 17/40 examples |
| **Common examples for agreement** | **17** |
| **Decision Agreement Rate** | **76.5%** (13/17) |
| **Cohen's Kappa** | **0.443** (Moderate agreement) |
| **Overall Score Correlation (Spearman)** | **-0.181** (negative!) |
| **Overall Score Correlation (Pearson)** | **-0.211** (negative!) |

**Conclusion:** The LLM judge and human reviewer reach the same final verdict (ACCEPT/REVISE) most of the time (76.5%), but do **NOT** agree on underlying quality scores — meaning the rubric's dimension-level scoring is not yet reliable, even though the pass/fail outcome has moderate agreement.

---

## 1. Sample Coverage Analysis

### Why Only 17/40 Have Human Reviews?

| Category | Count | Reason |
|----------|-------|--------|
| ESCALATE (no draft_reply) | 23 | Pipeline escalates high-risk/low-confidence cases, no reply generated |
| AUTO_HANDLE (has draft_reply) | 17 | Human reviewed these 17 examples |

**The 23 ESCALATE examples were evaluated by LLM judge using auto-generated template replies, but have no human reviews for comparison.**

### LLM Judge Coverage: 40/40

- 17 AUTO_HANDLE: Real AI-generated replies
- 23 ESCALATE: Template replies (auto-generated for evaluation purposes)

---

## 2. Decision-Level Analysis (17 Common Examples)

### Confusion Matrix

|  | Human ACCEPT | Human REVISE | Total |
|--|--------------|--------------|-------|
| **LLM ACCEPT** | 10 | 1 | 11 |
| **LLM REVISE** | 3 | 3 | 6 |
| **Total** | 13 | 4 | 17 |

### Decision Distribution

| Reviewer | ACCEPT | REVISE |
|----------|--------|--------|
| LLM Judge | 11 (65%) | 6 (35%) |
| Human | 13 (76%) | 4 (24%) |

**Agreement:** 13/17 = 76.5% (Cohen's Kappa = 0.443 = Moderate agreement)

---

## 3. Score Correlation Analysis (17 Common Examples)

### Overall Score Correlation

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Spearman r | **-0.181** | Negative! As LLM score goes up, human score goes down |
| Pearson r | **-0.211** | Weak negative linear relationship |
| p-value | >0.05 | Not statistically significant |

**Neither correlation is statistically significant. The score correlation is essentially random/noise.**

### Per-Dimension Correlation Analysis

| Dimension | Spearman r | Pearson r | Avg \|Diff\| | Exact Agree | Interpretation |
|-----------|------------|-----------|--------------|-------------|----------------|
| Factual Accuracy | -0.210 | -0.152 | 1.71 | 11.8% | **Inverse** - LLM rates what humans penalize |
| Policy Alignment | +0.015 | +0.045 | 1.59 | 11.8% | No correlation |
| Empathy & Tone | -0.018 | -0.032 | 1.24 | 23.5% | No correlation |
| Completeness | -0.036 | -0.116 | 1.29 | 23.5% | No correlation |
| Coherence | -0.056 | -0.056 | 1.00 | 23.5% | No correlation |

**Key Finding:** ALL correlations are weak or negative. No dimension shows meaningful agreement.

### Evidence: Decision Match but Score Divergence

**6 out of 17 examples (35%)** have matching ACCEPT/REVISE decisions but overall score difference ≥1.0:

| Example | Decision | LLM Score | Human Score | Diff |
|---------|----------|------------|-------------|------|
| golden_0006 | ACCEPT/ACCEPT | 5.00 | 2.80 | **+2.20** |
| golden_0024 | ACCEPT/ACCEPT | 4.00 | 2.60 | **+1.40** |
| golden_0029 | REVISE/REVISE | 2.00 | 3.80 | **-1.80** |
| golden_0031 | REVISE/REVISE | 2.00 | 3.40 | **-1.40** |
| golden_0032 | ACCEPT/ACCEPT | 4.00 | 2.60 | **+1.40** |
| golden_0034 | REVISE/REVISE | 2.00 | 3.40 | **-1.40** |

**Example: golden_0006**
- LLM scores: FA=5, PA=5, ET=4, C=4, CO=5 → avg=5.00
- Human scores: FA=2, PA=4, ET=2, C=1, CO=5 → avg=2.80
- LLM reasoning: "The customer's message is a general complaint without specific details..."
- Human reasoning: (did not capture detailed reasoning for this example)

---

## 4. Root Cause Hypothesis

### Why Do Scores Diverge Despite Matching Decisions?

**Hypothesis:** The LLM judge and human reviewer are using the rubric dimensions as **independent noise generators** rather than meaningful quality axes. The occasional decision agreement is coincidental, not indicative of reliable scoring.

**Evidence:**

1. **Zero meaningful correlations:** No dimension has Spearman r > 0.2 or < -0.2 with statistical significance.

2. **Arbitrary score patterns:** In golden_0006, LLM gives FA=5 (highest) while human gives FA=2 (lowest) — directly contradictory readings of the same reply.

3. **Completeness discrepancy:** LLM rates completeness low (1.85 avg across all 40) while other dimensions are higher. This suggests the LLM may be using "completeness" as a proxy for something else, or systematically misinterpreting the dimension.

4. **Human strictness varies by dimension:** Humans give higher empathy and lower completeness on average; LLM does the opposite.

**Possible contributing factors:**
- Rubric ambiguity: "Completeness" and "Factual Accuracy" may mean different things to different reviewers
- LLM judges may weight surface-level qualities (coherence, tone) over substantive ones
- The 1-5 scale may not be interpreted consistently
- Small sample (n=17) amplifies noise

---

## 5. Honest Interpretation

### What the Metrics Actually Mean

| Claim | Supported? |
|-------|------------|
| "LLM judge agrees with humans" | **PARTIAL** - 76.5% decision agreement is moderate |
| "Rubric dimensions are reliable" | **NO** - All correlations near zero or negative |
| "Judge can substitute for human" | **NO** - Dimension scores are not valid |
| "Scores correlate between judge and human" | **NO** - Negative correlation |

### Verdict

The LLM-as-judge rubric produces **borderline acceptable pass/fail decisions** (76.5% agreement, κ=0.443) but the **underlying dimension scores are unreliable** (Spearman r ≈ -0.18, not significant).

**Practical implication:** Using the LLM judge to ACCEPT/REVISE replies is marginally defensible, but using its dimension-level feedback to improve replies would be misleading.

---

## 6. Recommendations

1. **Do NOT use dimension scores for feedback** — they have no valid correlation with human judgment

2. **Consider simplifying to binary quality checks** — Instead of 5 rubric dimensions, use a single "overall quality" rating

3. **Calibrate the LLM judge with few-shot examples** — Current prompt lacks concrete scoring anchors

4. **Increase sample size** — n=17 is insufficient for stable correlation estimates

5. **Investigate completeness dimension** — LLM systematically rates this lower; rubric may need clarification

---

## 7. Files

| File | Description |
|------|-------------|
| `llm_judge_results.jsonl` | **40** LLM judge evaluations (all examples) |
| `llm_judge_results_16examples.jsonl` | Original 16 examples (before template replies) |
| `human_review_results.jsonl` | **17** human evaluations |
| `llm_human_agreement.json` | Agreement metrics JSON |

---

*Report generated: 2026-09-12*
*LLM-as-Judge validation study — Honest interpretation*