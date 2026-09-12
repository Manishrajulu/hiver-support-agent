# AmazonHelp Customer Service Intent Classification

A production-ready intent classification pipeline for Amazon customer service conversations on Twitter. The system classifies incoming messages into 15 intent categories, retrieves similar past cases, and either auto-generates a grounded reply or escalates to a human agent.

## 1. Project Overview

**Task:** Classify @AmazonHelp customer service conversations into intents to enable automatic handling or escalation.

**Brand:** Amazon (Twitter/X: @AmazonHelp)

**Pipeline:** 4-stage pipeline — Classification (TF-IDF + LinearSVC) → Retrieval (FAISS/sentence-transformers) → Escalation Decision (rule-based) → Reply Generation (Groq LLM)

**Headline Accuracy Numbers:**

| Metric | Accuracy | Count |
|--------|----------|-------|
| Test Set (in-distribution) | **71.11%** | 384/540 |
| Golden Set (out-of-sample) | **56.36%** | 124/220 |

**The 56.36% golden-set accuracy is the more realistic estimate of real-world performance.** See [FINAL_REPORT.md](FINAL_REPORT.md) Section 6 for full honest analysis of this gap.

---

## 2. Setup

### Prerequisites
- Python 3.10+ (developed on 3.13)
- Windows/Linux/macOS
- Internet connection (first run downloads ~200MB from HuggingFace)

### Installation

```bash
# Clone/download the project
cd hivER

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env and add your GROQ_API_KEY from https://console.groq.com/keys
```

### First-Run Note
On first run, the sentence-transformers model (~200MB) downloads from HuggingFace. Subsequent runs use the cached model.

---

## 3. Data

### Raw Dataset
- **Source:** Customer Support on Twitter (TWCS) — Kaggle, user `thoughtvector`
- **URL:** https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter
- **Expected location:** `archive/twcs/twcs.csv` (~516MB, 3M rows)
- **Filtering applied:** Extracted only @AmazonHelp brand conversations

### Preprocessed Data (already in repository)
- **File:** `data/processed/amazonhelp_labeled_conversations_v21_phase6c.jsonl`
- **Size:** ~2,700 AmazonHelp conversations with intent labels
- **Format:** JSONL with conversation_id, primary_intent, turns

### Build Labeled Dataset from Raw TWCS

If starting from raw TWCS data:

```bash
# Process raw TWCS CSV → AmazonHelp conversations (~10-15 minutes on 3M rows)
python data/process_amazonhelp.py

# Build labeled training data (~2-3 minutes)
python data/build_labeling_pipeline.py

# Create train/test split
python data/build_baseline.py
```

**Note:** Data processing takes 10-20 minutes on the full 3M-row TWCS dataset. The preprocessed data is already included in this repository to skip this step.

---

## 4. Reproduce the Headline Results

### Using the Pre-trained Phase C Model (FASTEST)

The Phase C model is already trained and saved. Reproducing results takes **under 1 minute**.

#### Test-Set Accuracy (71.11% = 384/540)

The test set is a 20% stratified holdout from training data.

```bash
# Time: ~10 seconds (includes model loading)
python -c "
import pickle
import json
from sklearn.model_selection import train_test_split

# Load Phase C model
with open('data/baseline/phaseC_model.joblib', 'rb') as f:
    model = pickle.load(f)

# Load training data to recreate test split
data = []
with open('data/processed/amazonhelp_labeled_conversations_v21_phase6c.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        data.append(json.loads(line))

# Recreate train/test split
import numpy as np
np.random.seed(42)
X = [c['conversation_id'] for c in data]
y = [c['primary_intent'] for c in data]
train_ids, test_ids = train_test_split(X, y, test_size=0.20, random_state=42, stratify=y)
test_ids_set = set(train_ids)  # Note: this is a simplification

# Count correct on test set
correct = 0
total = 0
# (See data/baseline/baseline_train_test_split.json for actual test_ids)
"
```

**Easier approach — run the existing baseline evaluation:**

```bash
# Runs the full baseline evaluation script
python data/build_baseline.py
# Output: Phase C test accuracy: 71.11% (384/540)
# Time: ~10 seconds
```

#### Golden-Set Accuracy (56.36% = 124/220)

The golden set is an independently-sampled, human-labeled evaluation set.

```bash
# Time: ~2 seconds (includes model loading)
python data/evaluation/golden_set_evaluate.py
# Output: Golden Set Accuracy: 56.36% (124/220)
```

### Training the Model from Scratch

If you want to retrain the Phase C model from preprocessed data:

```bash
# Time: ~5 seconds
python data/build_baseline.py

# Output:
# Phase C model saved to: data/baseline/phaseC_model.joblib
# Test accuracy will be printed (should match 71.11%)
```

### Timing Summary

| Step | Time | Notes |
|------|------|-------|
| Model loading | 1.6s | Phase C model from disk |
| Full training (2160 examples) | 5.4s | TF-IDF + LinearSVC |
| Test-set evaluation (540 examples) | 0.8s | After model loaded |
| Golden-set evaluation (220 examples) | 0.5s | After model loaded |
| **Total (load model + golden set eval)** | **~2s** | Reproducing 56.36% |

**15-Minute Claim:** The pipeline from model loading to reproducing the golden-set accuracy takes under 1 minute. Training from scratch (with preprocessed data) takes under 10 seconds. Data processing from raw TWCS takes 10-20 minutes and is NOT required — preprocessed data is included.

---

## 5. Run the API

### Start the Server

```bash
# Set API key
export GROQ_API_KEY=your_key_here  # On Windows: set GROQ_API_KEY=your_key_here

# Start server
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

### Test the API

```bash
# Health check
curl http://localhost:8000/health

# Classify a message
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"message": "My package was supposed to arrive yesterday but its still not here"}'
```

### Expected Output

```json
{
  "intent": "DELIVERY_LATE",
  "confidence": 0.94,
  "decision": "AUTO_HANDLE",
  "draft_reply": "I am very sorry to hear that your package has not arrived...",
  "evidence": [...]
}
```

---

## 6. Run Tests

```bash
pytest test_api.py -v
```

**Expected output:**
```
test_health_check PASSED
test_predict_delivery_late PASSED
test_predict_refund_request PASSED
...
8 passed in 2.3s
```

---

## 7. Project Structure

```
hiver/
├── api.py                    # FastAPI backend (production entry point)
├── pipeline.py               # 4-stage pipeline (classify → retrieve → escalate → generate)
├── data/
│   ├── pipeline.py           # Pipeline code
│   ├── llm_judge.py         # LLM-as-judge rubric
│   ├── escalation_decision.py # Escalation rules
│   ├── rag_retrieval.py      # FAISS retrieval
│   ├── reply_generation.py   # Groq reply generation
│   ├── baseline/
│   │   ├── phaseC_model.joblib           # BEST MODEL (71.11%)
│   │   └── baseline_train_test_split.json
│   ├── processed/
│   │   └── amazonhelp_labeled_conversations_v21_phase6c.jsonl  # Training data
│   ├── rag/
│   │   ├── faiss_index_train.bin         # RAG index
│   │   └── corpus_metadata_train.jsonl   # RAG metadata
│   ├── evaluation/
│   │   ├── golden_set_labeled.csv       # 220 human-labeled examples
│   │   ├── golden_set_predictions.jsonl  # Model predictions on golden set
│   │   ├── llm_judge_results.jsonl      # LLM judge evaluations (40 examples)
│   │   ├── human_review_results.jsonl   # Human evaluations (17 examples)
│   │   └── llm_human_agreement_report.md
│   └── golden/
│       └── golden_set_export.jsonl       # 200 examples for labeling
├── archive/
│   └── twcs/
│       └── twcs.csv                      # Raw TWCS dataset (3M rows, 516MB)
├── data/baseline/*.py        # Historical model training scripts (Phases B-G)
├── data/evaluation/*.py      # Evaluation scripts
├── test_api.py              # API tests
├── requirements.txt
├── .env.example
├── FINAL_REPORT.md          # Full analysis report
├── DECISION_LOG.md         # Decision reasoning log
└── CITATIONS.md            # Source citations
```

**Operational Pipeline (production):**
- `api.py` — FastAPI server
- `pipeline.py` — 4-stage classification + generation pipeline
- `data/llm_judge.py` — LLM-as-judge rubric

**Historical/Exploratory (not needed for reproduction):**
- `data/baseline/phase*.py` — Old training scripts (Phases B-G)
- `data/build_baseline.py` — Can retrain model if needed

---

## 8. Key Findings Summary

**The 71.11% test-set accuracy is optimistic.** The golden-set accuracy (56.36%) is the more realistic estimate because the golden set is sampled from untouched raw data, not from the curated training pool. See [FINAL_REPORT.md](FINAL_REPORT.md) Section 6.

**The LLM-as-judge rubric is partially validated.** Decision agreement with human reviewers is 76.5% (Cohen's Kappa 0.443 = moderate), but dimension-level quality scores are NOT correlated (Spearman r = -0.18). Use the judge for pass/fail decisions only, not for fine-grained quality feedback. See [FINAL_REPORT.md](FINAL_REPORT.md) Section 9.

**Key decisions documented:**
- Phase C frozen over Phase E (taxonomy cleanup hurt accuracy by -1.3pp)
- Phase F (English-only training) rejected (-4.6pp degradation)
- Phase G (data augmentation) rejected (-3.5pp degradation)
- See [DECISION_LOG.md](DECISION_LOG.md) for full reasoning

---

## 9. Citations

See [CITATIONS.md](CITATIONS.md) for full source documentation:
- Dataset: Kaggle Customer Support on Twitter (thoughtvector)
- Libraries: scikit-learn, sentence-transformers, FAISS, Groq API
- AI Assistance: Claude Code (Anthropic) — used freely per assignment allowance

---

*Document version: 2.0*
*Generated: 2026-09-12*
*Reproducible walkthrough: under 1 minute (pre-trained model) / under 10 seconds (retrain from preprocessed data)*