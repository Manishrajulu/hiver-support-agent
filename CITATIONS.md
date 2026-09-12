# Citations

## 1. Dataset

**Customer Support on Twitter (twcs.csv)**
- Source: Kaggle, user `thoughtvector`
- URL: https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter
- Filtering applied: Extracted only @AmazonHelp brand conversations from the full dataset
- Original dataset size: 2,811,774 conversations (August 2011 - December 2017)
- Final filtered dataset: ~2,700 AmazonHelp conversations

---

## 2. Libraries & Models

### scikit-learn
- **Purpose:** TF-IDF vectorization (word + character n-grams) and LinearSVC classifier
- **Version:** 1.9.0
- **Citation:** Pedregosa et al., "Scikit-learn: Machine Learning in Python," JMLR 12, pp. 2825-2830, 2011.
- **URL:** https://scikit-learn.org/
- **Usage:** Standard off-the-shelf usage — no modifications to algorithm internals

### sentence-transformers (all-MiniLM-L6-v2)
- **Purpose:** Semantic embeddings for RAG retrieval
- **Version:** 6.0.1
- **Model:** all-MiniLM-L6-v2
- **Citation:** Reimers & Gurevych, "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks," EMNLP 2019
- **HuggingFace Model Card:** https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
- **Usage:** Off-the-shelf for embedding generation; index built on training corpus only (no test leakage)

### FAISS (Facebook AI Similarity Search)
- **Purpose:** Fast approximate nearest-neighbor search for RAG retrieval
- **Version:** 1.15.0 (faiss-cpu)
- **Citation:** Johnson et al., "Billion-scale similarity search with GPUs," arXiv:1702.08734, 2017
- **URL:** https://github.com/facebookresearch/faiss
- **Usage:** CPU index on training corpus embeddings for retrieval

### Groq API (LLM Generation & LLM-as-Judge)
- **Purpose:** Reply generation (pipeline stage 3) and LLM-as-judge evaluation
- **SDK Version:** 1.7.0 (groq Python package)
- **Model:** `qwen/qwen3.8-27b` (used for both reply generation and judge evaluation)
- **API URL:** https://console.groq.com/
- **Usage:** Cloud API; all prompts are custom-developed for this project (see Section 4)

### FastAPI & uvicorn
- **Purpose:** Web framework and ASGI server for API
- **FastAPI Version:** 0.137.0
- **uvicorn Version:** 0.49.0
- **URL:** https://fastapi.tiangolo.com/ / https://www.uvicorn.org/
- **Usage:** Standard web framework usage

### Pydantic
- **Purpose:** Data validation for API request/response schemas
- **Version:** 2.13.4
- **URL:** https://docs.pydantic.dev/
- **Usage:** Standard schema definition

### Python-dotenv
- **Purpose:** Environment variable management (GROQ_API_KEY)
- **Version:** 1.2.2
- **URL:** https://pypi.org/project/python-dotenv/

---

## 3. AI Coding Assistance

**AI coding assistants were used freely throughout development, per assignment allowance.**

### Claude Code (Anthropic)
- **Pipeline code:** Help designing the 4-stage pipeline architecture (classify → retrieve → escalate → generate)
- **Analysis scripts:** Assistance writing evaluation scripts, agreement calculators, and data processing utilities
- **Debugging:** Troubleshooting Groq API integration, rate limiting, and environment variable loading issues
- **Documentation:** Drafting README sections, report writing, and this citations page
- **Nature of assistance:** All final code, analysis, and documentation represents human decisions; AI assistance was used for implementation speed and pattern reference, not as a black-box solution

### Other Tools
- **scikit-learn documentation:** Standard reference for API usage
- **HuggingFace documentation:** Standard reference for sentence-transformers and model cards
- **Groq API documentation:** Standard reference for API integration

---

## 4. Borrowed Code or Prompts

**No code was directly copied from external sources beyond standard library/framework usage as cited above.**

### Prompts (Custom-Developed)
- `pipeline.py` `generate_reply()` prompt: Custom prompt instructing LLM to ground replies in retrieved evidence only — developed specifically for this project to prevent hallucination
- `llm_judge.py` `JUDGE_PROMPT` and `RUBRIC`: Custom 5-dimension evaluation rubric (factual accuracy, policy alignment, empathy/tone, completeness, coherence) — developed specifically for this project
- No prompt templates, rubric designs, or code snippets were borrowed from tutorials, Stack Overflow, blog posts, or published papers

### Code Patterns
- Standard library usage throughout (csv, json, os, sys, etc.) — no attribution required
- sklearn/pipeline patterns follow official tutorials only
- No code was adapted from Stack Overflow answers, blog posts, or other public repositories

---

*CITATIONS.md generated: 2026-09-12*
*Last updated: 2026-09-12*