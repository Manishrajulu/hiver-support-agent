# Deployment Cleanup Report

## Date: 2026-09-10

## Summary

Removed deployment-related files and infrastructure that were not required by the Hiver SDE Intern assignment. The assignment requires a GitHub repository with a runnable local pipeline, not production deployment.

---

## Assignment Requirements vs. What Was Removed

### Assignment Requirements
- Public/private GitHub repository with a runnable pipeline
- README instructions that reproduce headline results in under 15 minutes
- 150–250 hand-labelled golden evaluation examples
- Evaluation harness + LLM-as-judge + human agreement evidence
- Final report
- Decision log
- Submission through their form with the repository link and report

### NOT Required
- AWS/Lightsail deployment
- Docker deployment
- Production REST API
- CI/CD workflows
- Production hosting
- Frontend application

---

## Files Removed

| File/Directory | Reason for Removal |
|----------------|-------------------|
| `Dockerfile` | Docker deployment - not required |
| `.dockerignore` | Docker deployment - not required |
| `api/` directory | REST API - not required |
| `api/main.py` | FastAPI application - not required |
| `api/schemas.py` | API schemas - not required |
| `api/config.py` | API configuration - not required |
| `api/test_api.py` | API tests - not required |
| `api/__init__.py` | API package init - not required |
| `api/.env.example` | Environment template - not required |
| `docs/deployment.md` | Deployment documentation - not required |
| `requirements.txt` | FastAPI/uvicorn dependencies - not required for core pipeline |

---

## Files Intentionally Kept

| File/Directory | Reason for Keeping |
|----------------|-------------------|
| `data/pipeline.py` | Core end-to-end pipeline |
| `data/test_pipeline.py` | Evaluation test suite |
| `data/escalation_decision.py` | Escalation logic |
| `data/reply_generation.py` | Reply generation |
| `data/rag_retrieval.py` | RAG retrieval |
| `data/baseline/` | TF-IDF + LR classifier |
| `data/rag/` | FAISS index and metadata |
| `data/evaluation/` | All evaluation reports and results |
| `data/processed/` | Labeled dataset processing |
| `amazonhelp_project_sprint_roadmap.md` | Project roadmap (updated) |

---

## README Changes

Updated `amazonhelp_project_sprint_roadmap.md` to:
1. Remove Sprint 9 (API/Backend) references
2. Rename Sprint 9 to "Repository Cleanup + Submission Preparation"
3. Remove Sprint 10 (Deployment)
4. Rename Sprint 11 to Sprint 10 (Final Demo + Documentation)
5. Update status to reflect current state
6. Add note that deployment is NOT required by the assignment

Updated `data/evaluation/sprint6_integration_report.md` to:
1. Clarify this is a local-run pipeline
2. Remove references to REST API

---

## Verification Tests Performed

### 1. Core Pipeline Test

```python
from pipeline import run_pipeline, validate_response
result = run_pipeline("My package is late", skip_generation=True)
```

**Result**: PASSED
- Classification works
- RAG retrieval works
- Escalation decision works
- Schema validation passes

### 2. Full Pipeline Test Suite (50 conversations)

```bash
python data/test_pipeline.py
```

**Result**: PASSED
- 50/50 successful runs
- 0 schema errors
- AUTO_HANDLE rate: 24%
- ESCALATE rate: 76%
- Intent accuracy: 58%
- All components load correctly

---

## Core Pipeline Confirmation

The core pipeline (`data/pipeline.py`) still works correctly:

```
Customer conversation
        ↓
Stage 1: Classification (TF-IDF + LR)
        ↓
Intent + confidence
        ↓
Stage 2: RAG Retrieval (top-k=5)
        ↓
Stage 3: Reply Generation (Groq) - ONLY if AUTO_HANDLE
        ↓
Stage 4: Escalation Decision
        ↓
Structured final response
```

**All components verified:**
- Classifier: baseline_model.joblib ✓
- RAG: faiss_index_train.bin + metadata ✓
- Generation: Groq qwen/qwen3.8-27b ✓
- Escalation: conf<0.25, sim<0.3 ✓

---

## Assignment Functionality Checklist

| Requirement | Status |
|------------|--------|
| Runnable local pipeline | ✓ VERIFIED |
| Dataset processing | ✓ EXISTS |
| Intent taxonomy | ✓ EXISTS |
| Classification (TF-IDF + LR) | ✓ EXISTS |
| RAG retrieval | ✓ EXISTS |
| FAISS index | ✓ EXISTS |
| Reply generation | ✓ EXISTS |
| Escalation decision | ✓ EXISTS |
| Evaluation harness | ✓ EXISTS |
| Evaluation reports | ✓ EXISTS |
| Decision log | ✓ EXISTS |

---

## Conclusion

No required assignment functionality was removed. The cleanup successfully removed:

1. Docker deployment infrastructure
2. REST API implementation
3. FastAPI web server
4. Deployment documentation
5. Deployment-specific dependencies (FastAPI, uvicorn)

The repository now contains only what is needed for the assignment:
- A runnable local pipeline
- Evaluation tools and reports
- Dataset processing
- Research documentation

The core pipeline and all evaluation functionality remain intact and operational.

---

*Report generated: 2026-09-10*
