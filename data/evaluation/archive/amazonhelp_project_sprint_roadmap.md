# AmazonHelp AI Support System — Project Sprint Roadmap

## Overall Pipeline

```text
AmazonHelp Conversations
        ↓
Data Preparation
        ↓
Intent Classification
        ↓
Baseline Comparison
        ↓
RAG / Similar Case Retrieval
        ↓
Reply Generation
        ↓
Escalation Decision
        ↓
Structured AI Response
        ↓
Evaluation
        ↓
Final API / Demo
```

---

# Sprint 0 — Project Foundation

## Goal
Make sure the dataset, taxonomy, and project structure are stable.

## Tasks
- [x] Collect AmazonHelp conversations
- [x] Understand conversation structure
- [x] Define intent taxonomy
- [x] Prepare 2,700-conversation working dataset
- [x] Establish project folder structure
- [x] Document system architecture

## Status
**DONE**

---

# Sprint 1 — Intent Classification

## Goal
Build a reliable classifier that answers:

> What is the customer's primary problem?

## Work Already Completed

### V1 — Rule-Based Classification
Keyword/rule matching was tested and exposed problems with keyword/context conflicts and a high OTHER rate.

### V2 / V2.1 / V2.2
Several context-aware rule versions were tested.

**Conclusion:** Do not keep endlessly tweaking deterministic rules.

### TF-IDF + Logistic Regression Baseline

```text
Conversation
     ↓
TF-IDF
     ↓
Logistic Regression
     ↓
Intent
```

Results:

| Model | Accuracy | Macro F1 |
|---|---:|---:|
| Majority Baseline | 37.6% | 0.039 |
| TF-IDF + Logistic Regression | **56.3%** | **0.507** |
| Groq allam-2-7b | 19.4% | 0.229 |

The TF-IDF + Logistic Regression model is our current baseline.

### Groq Experiment
Groq `allam-2-7b` performed significantly worse than the TF-IDF baseline and showed strong bias toward ORDER_STATUS and ORDER_MODIFY. Prompt improvements did not demonstrate a reliable benefit.

## What We Should NOT Do
- Do not spend another large amount of time trying to perfect the current `allam-2-7b` setup.
- Do not keep adding increasingly complicated keyword rules.
- Do not treat LLM-generated labels as human ground truth.

## Next Action
Choose/build the final semantic classification approach and compare it against the TF-IDF baseline.

## Status
**SUBSTANTIALLY COMPLETE — FINAL CLASSIFIER STILL TO BE SELECTED**

---

# Sprint 2 — Classification Evaluation

## Goal
Determine whether the final classifier is actually better than the baseline.

Compare:

```text
TF-IDF + Logistic Regression
          │
          ├──→ metrics
          │
Final Semantic Classifier
          │
          └──→ metrics
```

Measure:
- Accuracy
- Macro F1
- Weighted F1
- Precision per intent
- Recall per intent
- Confusion matrix
- OTHER rate
- Confidence distribution

The existing 200-conversation work can support development/reference, but LLM-generated labels must be clearly distinguished from genuine human ground truth.

## Status
**NOT STARTED**

---

# Sprint 3 — RAG / Similar Case Retrieval

## Goal
Given a new customer message, retrieve relevant historical conversations.

```text
New conversation
       ↓
Embedding
       ↓
Vector search
       ↓
Similar historical cases
```

## Tasks
- Generate embeddings
- Create vector index
- Store conversation + metadata
- Implement similarity search
- Retrieve top-k similar cases
- Filter by intent where useful

## Possible Technology
```text
Embedding Model
      ↓
FAISS / Vector Database
```

Start simple; do not over-engineer the first version.

## Status
**NOT STARTED**

---

# Sprint 4 — Reply Generation

## Goal
Generate a useful customer-support draft using the customer issue and retrieved evidence.

## Input
```text
Customer message
+
Predicted intent
+
Retrieved similar cases
```

## Output
```text
Draft reply
```

The response must be grounded in:
- Customer message
- Known information
- Retrieved evidence

The LLM should not blindly invent information.

## Status
**NOT STARTED**

---

# Sprint 5 — Escalation Engine

## Goal
Decide whether AI can safely handle the conversation or whether it should be escalated.

Example:

```text
High-confidence simple case
        ↓
   AUTO_HANDLE
```

```text
Low-confidence / risky case
        ↓
     ESCALATE
```

## Initial Policy

```text
IF confidence < threshold
    → ESCALATE

IF high-risk intent
    → ESCALATE

IF insufficient evidence
    → ESCALATE

ELSE
    → AUTO_HANDLE
```

Keep the first version simple and explainable.

## Status
**NOT STARTED**

---

# Sprint 6 — Structured Output

## Goal
Create a clean response contract for the complete AI system.

Example:

```json
{
  "intent": "DELIVERY_LATE",
  "confidence": 0.91,
  "decision": "AUTO_HANDLE",
  "reason": "Customer reports delayed delivery",
  "draft_reply": "...",
  "evidence": [
    "similar_case_123",
    "similar_case_456"
  ]
}
```

Required fields:
- intent
- confidence
- decision
- reason
- draft_reply
- evidence

## Status
**NOT STARTED**

---

# Sprint 7 — End-to-End Pipeline

## Goal
Connect every component into one working pipeline.

```text
Customer Message
      ↓
Intent Classifier
      ↓
Intent + Confidence
      ↓
RAG Retrieval
      ↓
Similar Cases
      ↓
Reply Generator
      ↓
Draft Response
      ↓
Escalation Engine
      ↓
AUTO-HANDLE / ESCALATE
      ↓
Structured JSON
```

## Status
**NOT STARTED**

---

# Sprint 8 — Evaluation

## Goal
Prove that the system works.

### Classification
- Accuracy
- Macro F1
- Confusion matrix
- Per-intent performance

### Retrieval
- Recall@K
- Precision@K
- Qualitative relevance

### Reply Generation
- Relevance
- Correctness
- Groundedness
- Helpfulness
- Hallucination

### LLM Judge

```text
Customer issue
       +
Retrieved evidence
       +
Generated reply
       ↓
     Judge
       ↓
    Scores
```

## Status
**NOT STARTED**

---

# Sprint 9 — Repository Cleanup + Submission Preparation

## Goal
Prepare the repository for submission per assignment requirements.

## Assignment Requirements
- Public/private GitHub repository with runnable pipeline
- README instructions that reproduce headline results in under 15 minutes
- 150–250 hand-labelled golden evaluation examples
- Evaluation harness + LLM-as-judge + human agreement evidence
- Final report
- Decision log
- Submission through their form with the repository link and report

## Tasks
- [x] Verify repository structure is clean
- [x] Ensure pipeline runs locally without deployment
- [x] Update README with reproduction instructions
- [ ] Verify golden evaluation set (150-250 examples)
- [ ] Complete LLM-as-judge evaluation
- [ ] Prepare final submission report
- [ ] Prepare decision log

## Status
**IN PROGRESS**

---

# Sprint 10 — Final Demo + Documentation

## Goal
Package the project into a clear, demonstrable final system.

## Technical Documentation
- Architecture diagram
- Dataset processing
- Intent taxonomy
- Classification model
- Baseline comparison
- RAG implementation
- Reply generation
- Escalation policy
- Evaluation methodology

## Reports

```text
classification_report.md
baseline_report.md
retrieval_evaluation.md
reply_evaluation.md
final_evaluation.md
```

## Demo Flow

```text
Customer message
      ↓
Intent
      ↓
Confidence
      ↓
Similar cases
      ↓
Generated response
      ↓
Escalation decision
```

## Status
**NOT STARTED**

---

# Current Project Status

```text
Sprint 0   ██████████ DONE
Sprint 1   ██████████ DONE
Sprint 2   ██████████ DONE
Sprint 3   ██████████ DONE
Sprint 4   ██████████ DONE
Sprint 5   ██████████ DONE
Sprint 6   ██████████ DONE
Sprint 7   ██████████ DONE (API - NOT REQUIRED FOR ASSIGNMENT)
Sprint 8   ██████████ DONE
Sprint 9   ░░░░░░░░░░ IN PROGRESS
Sprint 10  ░░░░░░░░░░
```

**Note**: The assignment does NOT require deployment, production hosting, or a REST API.
The goal is a research/evaluation project with a runnable local pipeline.

# Immediate Execution Plan

1. Complete repository cleanup
2. Prepare README with reproduction instructions
3. Verify golden evaluation set completeness
4. Complete LLM-as-judge evaluation
5. Prepare final submission report
6. Prepare decision log
7. Submit through assignment form

## What This Project IS

- A research/evaluation project for customer service intent classification
- A local-run pipeline (no deployment required)
- A GitHub repository with reproducible results
- An evaluation harness with golden examples

## What This Project is NOT

- A production deployment
- A hosted API service
- A frontend application
- An AWS/Lightsail deployment
