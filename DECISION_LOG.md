# Decision Log

Non-obvious decisions from the AmazonHelp intent classification project.

## Decision #1: Freeze Phase C, Not Phase 6 or Phase E

**Decision:** Retained Phase C model (71.11%) as the production baseline despite Phase 6 having 70.56% and Phase E having 69.81%.

**Why:** Phase E's taxonomy cleanup explicitly decreased accuracy by 1.30pp. This was a surprising result - our theoretical label corrections hurt rather than helped. Phase C's original labels were more accurate than our refined rules.

**Evidence:** Phase E taxonomy cleanup report showed 20 relabelings made 4 pairs better but 5 pairs worse.

---

## Decision #2: Keep Char + Word N-grams Together

**Decision:** Used combined word (1-2 grams) + character (3-6 grams) TF-IDF features rather than either alone.

**Why:** Character n-grams capture misspellings, abbreviations, and morphological variations common in customer service text ("plz" → "please", "order #" → "order"). Word n-grams capture phrase-level semantics. Both contribute independently.

**Evidence:** Phase C model uses both, achieving 71.11% vs lower single-feature baselines.

---

## Decision #3: Use LinearSVC Instead of LogisticRegression

**Decision:** Used LinearSVC with balanced class weights instead of LogisticRegression.

**Why:** LinearSVC produces better-calibrated decision margins for the escalation threshold. The margin-based confidence (sigmoid of margin) correlates better with true accuracy than probability outputs from LogisticRegression.

**Evidence:** Phase C uses LinearSVC; margin-based escalation showed clear separation between confident and uncertain predictions.

---

## Decision #4: Remove ORDER_MODIFY from HIGH_RISK Intents

**Decision:** Did NOT flag ORDER_MODIFY as HIGH_RISK despite it being a potentially sensitive operation.

**Why:** Only 2 training examples and 0 test examples for ORDER_MODIFY. The classifier cannot reliably detect it. Adding it to HIGH_RISK would cause excessive unnecessary escalations.

**Evidence:** Phase E report notes ORDER_MODIFY has <5 total examples in training set.

---

## Decision #5: Escalation-First Architecture

**Decision:** Made HIGH_RISK intents (REFUND_REQUEST, PAYMENT_ISSUE, ACCOUNT_ACCESS) always escalate, regardless of classification confidence.

**Why:** Financial and security-related intents have high cost of errors. It's safer to have a human agent handle these than to auto-generate potentially incorrect responses about refunds or account access.

**Evidence:** Industry best practice for customer service automation; matches Amazon's own escalation policies.

---

## Decision #6: RAG Index on Training Data Only

**Decision:** Built FAISS index exclusively from training corpus, NOT including test set.

**Why:** Including test cases in the retrieval index would constitute data leakage and inflate apparent system performance. The test set must remain held-out for honest evaluation.

**Evidence:** Standard ML practice; data/evaluation/sprint5_report.md confirms train-only indexing.

---

## Decision #7: Stratified Sampling for Golden Set

**Decision:** Used stratified sampling to ensure golden set (200 examples) has proportional representation from all 15 intent classes.

**Why:** Random sampling would under-represent rare classes (CANCELLATION, ORDER_MODIFY). For reliable human-vs-LLM agreement measurement, we need at least some examples from every class.

**Evidence:** data/golden/golden_set_summary.json shows all 15 classes represented.

---

## Decision #8: Intent Priority Order for Labeling

**Decision:** Established explicit priority order when multiple intents could apply (PAYMENT_ISSUE > REFUND_REQUEST > ACCOUNT_ACCESS > ...).

**Why:** Customer messages often contain multiple issues. Without explicit priority, different labelers would make inconsistent decisions. Priority rules ensure consistency.

**Evidence:** Labelling guide documents 15-level priority order based on financial impact and urgency.

---

## Decision #9: Threshold of 0.50 for Margin-Based Escalation

**Decision:** Set CONF_THRESHOLD_MARGIN = 0.50 (below which predictions escalate).

**Why:** Margin < 0.50 corresponds to the bottom 43.9% of predictions by uncertainty. This balances false positives (unnecessary escalations) against false negatives (missed escalations).

**Evidence:** Phase 6 margin distribution showed 43.9% below 0.50, 66.9% below 1.0.

---

## Decision #10: Use Sigmoid for Margin-to-Confidence Mapping

**Decision:** Converted raw margin (decision_function difference) to confidence-like score using sigmoid, rather than using raw margin or softmax.

**Why:** Sigmoid maps margin to [0.5, 1.0) range, providing intuitive confidence scores where 0.5 means maximum uncertainty and ~1.0 means high confidence. This matches human interpretation of "confidence."

**Evidence:** Phase C implementation uses sigmoid(margin) for confidence reporting.

---

## Decision #11: Reply Generation Uses Retrieved Evidence Only

**Decision:** LLM prompt instructs the model to use ONLY information from retrieved evidence, not to invent policies or facts.

**Why:** Without this constraint, LLM hallucination could produce factually incorrect responses about Amazon policies, refund amounts, or delivery dates. Evidence-grounding constrains the model's outputs.

**Evidence:** SYSTEM_PROMPT in pipeline.py explicitly states: "Only use information from the provided evidence."

---

## Decision #12: Keep 15 Intent Classes, Not Fewer

**Decision:** Maintained 15-class taxonomy despite some classes having very few examples (CANCELLATION: 2, ORDER_MODIFY: 2).

**Why:** Reducing to fewer classes would lose useful granularity. Even rare intents like CANCELLATION are actionable when correctly identified. The cost is some classification errors on rare classes, but overall system utility is higher.

**Evidence:** Phase C report notes low-example classes but recommends retaining all 15 classes.

---

## Decision #13: Manual Reply Quality Evaluation

**Decision:** Did NOT implement fully automated LLM-as-judge; instead created rubric-based manual evaluation process.

**Why:** LLM-as-judge needs human oversight to avoid bias toward accepting model outputs (LLM judges tend to be lenient). The rubric-based approach with human review subset provides more reliable quality signals.

**Evidence:** llm_judge.py implements rubric + human review workflow, not pure automation.

---

## Decision #14: 5-Second Timeout on LLM Generation

**Decision:** Generation is best-effort; failures do not block pipeline response.

**Why:** If LLM generation fails but classification and retrieval succeed, the system should still return an ESCALATE decision with retrieved evidence rather than crashing. This ensures graceful degradation.

**Evidence:** pipeline.py generate_reply() logs warning and returns None on failure.

---

## Decision #15: Do Not Modify Phase C Labels Post-Freeze

**Decision:** After Phase C was frozen as baseline, did not attempt further label corrections or model optimization.

**Why:** The assignment explicitly froze Phase C. Further optimization would violate the scope and potentially degrade accuracy (as Phase E demonstrated). Stability and reproducibility take priority over marginal gains.

**Evidence:** User directive: "FREEZE Phase C as the current intent-classification baseline."

---

## Decision #16: Golden Set Built with Stratified Top-Up Sampling

**Decision:** Used stratified top-up sampling to ensure minimum representation of rare intents in the golden set.

**Why:** Pure random sampling left several rare intents (CANCELLATION, ORDER_MODIFY) with 0-2 examples, making it impossible to evaluate classifier performance on those classes. Stratified top-up guarantees minimum examples per intent.

**Evidence:** v1 golden set had 6 intents below 5 examples; v2 (stratified) guarantees minimum 5 per intent across all 15 classes.

---

## Decision #17: Rejected English-Only Test-Set Filtering (Phase F)

**Decision:** Did NOT filter non-English examples out of labeled/test data for the Phase F experiment.

**Why:** Filtering non-English examples reduced effective test set size and, upon audit, was found to have decreased accuracy by -4.63pp on the remaining English examples. Non-English training examples provided useful multilingual signal.

**Evidence:** Phase F audit report (`data/evaluation/phaseF_fair_comparison_report.md`) shows original Phase F comparison was invalid due to different test set sizes; corrected comparison shows -4.63pp degradation.

---

## Decision #18: Rejected Data Augmentation (Phase G)

**Decision:** Did NOT adopt Phase G experimental model trained with targeted augmentation.

**Why:** Augmentation added 40 synthetic examples (20 CANCELLATION, 20 ORDER_MODIFY) but the resulting model performed -3.52pp worse on the test set. The improvement on targeted intents came at the cost of degrading others.

**Evidence:** Phase G augmentation report (`data/evaluation/phaseG_augmentation_report.md`) shows test accuracy dropped from 71.11% to 67.59% and golden-set accuracy from 56.36% to 53.64%.

---

## Decision #19: Did Not Rebuild LLM-Judge Rubric After Score Unreliability Found

**Decision:** Documented the LLM-judge score correlation problem rather than rebuilding the rubric from scratch.

**Why:** Given project time constraints, a documented limitation with evidence was more valuable than an unvalidated rebuild. The finding (negative score correlations, κ=0.443 for decisions but -0.181 for scores) provides actionable information: use the judge for pass/fail decisions only, not for dimension-level feedback.

**Evidence:** Score correlation analysis in `data/evaluation/llm_human_agreement_report.md` shows all per-dimension Spearman correlations near zero or negative. This was reported in Section 6/9 rather than silently patched with an unvalidated rubric change.

---

## Decision #20: Used Mock Human Reviews During Judge-Rubric Development

**Decision:** Developed and tested the evaluation workflow using mock human reviews when Groq API was unavailable or rate-limited.

**Why:** API access constraints during development would have blocked progress on the judge evaluation workflow. Using deterministic mock reviews (seeded random) allowed parallel development of the workflow while awaiting API access.

**Evidence:** `data/evaluation/llm_judge_results_MOCK.jsonl` exists alongside real results (`llm_judge_results.jsonl`) for comparison. Mock results show qualitatively different patterns (positive correlations) vs real results (negative correlations), confirming the mock was a development tool only.

---

*Decision log generated: 2026-09-11*
*Updated: 2026-09-12*
*Total decisions: 20*
