#!/usr/bin/env python3
"""
Phase 8: FastAPI Backend for AmazonHelp Customer Service Pipeline

This module provides a REST API for the Phase 7 pipeline.

Endpoints:
- GET /health - Health check
- POST /predict - Intent classification and response

Usage:
    uvicorn api:app --reload --host 0.0.0.0 --port 8000
"""

import os
import sys
import logging
from contextlib import asynccontextmanager
from pathlib import Path

# Add data/ to path for pipeline imports
sys.path.insert(0, str(Path(__file__).parent / 'data'))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Import pipeline functions at module level for easy mocking in tests
from pipeline import classify, retrieve_similar, decide_escalation, generate_reply

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('api')


# =============================================================================
# Request/Response Schemas
# =============================================================================

class PredictRequest(BaseModel):
    """Request schema for /predict endpoint."""
    message: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Customer support message text"
    )
    skip_generation: bool = Field(
        default=False,
        description="Skip LLM reply generation (for faster responses)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message": "My package was supposed to arrive yesterday but it's still not here.",
                "skip_generation": False
            }
        }


class EvidenceItem(BaseModel):
    """Retrieved case evidence item."""
    conversation_id: str
    intent: str
    similarity_score: float
    customer_text: str


class PredictResponse(BaseModel):
    """Response schema for /predict endpoint."""
    message: str
    intent: str
    confidence: float
    margin: float
    decision: str
    reason: str
    draft_reply: str | None
    evidence: list[EvidenceItem]
    retrieved_case_ids: list[str]

    class Config:
        json_schema_extra = {
            "example": {
                "message": "My package was late",
                "intent": "DELIVERY_LATE",
                "confidence": 0.974,
                "margin": 3.642,
                "decision": "AUTO_HANDLE",
                "reason": "AUTO_HANDLE - intent=DELIVERY_LATE, margin=3.642, conf=0.974, avg_sim=0.718",
                "draft_reply": "I understand your package was delayed...",
                "evidence": [
                    {
                        "conversation_id": "amazonhelp_123456",
                        "intent": "DELIVERY_LATE",
                        "similarity_score": 0.852,
                        "customer_text": "My package hasn't arrived yet..."
                    }
                ],
                "retrieved_case_ids": ["amazonhelp_123456"]
            }
        }


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    detail: str | None = None


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str
    model_loaded: bool
    rag_loaded: bool
    groq_available: bool
    version: str


# =============================================================================
# Pipeline Components (Lazy Loaded)
# =============================================================================

class PipelineManager:
    """Manages pipeline component lifecycle."""

    def __init__(self):
        self._components = None
        self._pipeline = None
        self._load_error = None

    def load(self):
        """Load all pipeline components."""
        if self._components is not None:
            return

        try:
            from pipeline import load_components
            self._components = load_components()

            # Test classification to verify model works
            from pipeline import classify
            test_intent, test_conf, test_margin, _ = classify(
                "test message", self._components.phasec_model
            )
            logger.info(f"Pipeline loaded successfully: model={test_intent}")

        except Exception as e:
            logger.error(f"Failed to load pipeline: {e}")
            self._load_error = str(e)
            raise

    @property
    def is_loaded(self) -> bool:
        return self._components is not None

    @property
    def load_error(self) -> str | None:
        return self._load_error

    def get_pipeline(self):
        """Get the pipeline components."""
        if self._components is None:
            self.load()
        return self._components


# Global pipeline manager
pipeline_manager = PipelineManager()


# =============================================================================
# Application Lifespan
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting AmazonHelp API...")
    try:
        pipeline_manager.load()
        logger.info("Pipeline loaded successfully")
    except Exception as e:
        logger.error(f"Pipeline load failed: {e}")

    yield

    # Shutdown
    logger.info("Shutting down AmazonHelp API...")


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="AmazonHelp Customer Service API",
    description="Intent classification and response generation for Amazon customer support",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Endpoints
# =============================================================================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns the status of the API and its dependencies.
    """
    groq_available = False
    try:
        from groq import Groq
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            groq_available = True
    except ImportError:
        pass

    return HealthResponse(
        status="healthy" if pipeline_manager.is_loaded else "degraded",
        model_loaded=pipeline_manager.is_loaded,
        rag_loaded=pipeline_manager.is_loaded,
        groq_available=groq_available,
        version="1.0.0"
    )


@app.post("/predict", response_model=PredictResponse, tags=["Prediction"])
async def predict(request: PredictRequest):
    """
    Classify customer message and generate response.

    This endpoint:
    1. Classifies the intent using the Phase C model (71.11% accuracy)
    2. Retrieves similar cases via RAG
    3. Makes an escalation decision
    4. Generates a response if AUTO_HANDLE
    """
    # Validate message
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        # Get pipeline
        components = pipeline_manager.get_pipeline()

        # Stage 1: Classification (Phase C model - 71.11% accuracy)
        intent, confidence, margin, top_candidates = classify(
            message, components.phasec_model
        )

        # Stage 2: RAG Retrieval
        retrieved_cases = retrieve_similar(
            message,
            components.rag_model,
            components.rag_index,
            components.rag_metadata,
            top_k=5
        )

        # Stage 3: Escalation Decision
        escalation = decide_escalation(intent, confidence, margin, retrieved_cases)
        decision = escalation["decision"]

        # Stage 4: Generate reply (if AUTO_HANDLE and not skipped)
        draft_reply = None
        if decision == "AUTO_HANDLE" and not request.skip_generation:
            draft_reply = generate_reply(
                message, intent, confidence, margin,
                retrieved_cases, components.groq_client
            )

        # Build response
        response = PredictResponse(
            message=message,
            intent=intent,
            confidence=round(confidence, 4),
            margin=round(margin, 4),
            decision=decision,
            reason=escalation["reason"],
            draft_reply=draft_reply,
            evidence=[
                EvidenceItem(
                    conversation_id=case["conversation_id"],
                    intent=case["primary_intent"],
                    similarity_score=round(case["similarity_score"], 4),
                    customer_text=case["customer_text"]
                )
                for case in retrieved_cases
            ],
            retrieved_case_ids=[case["conversation_id"] for case in retrieved_cases]
        )

        return response

    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        reload=True,
        host="0.0.0.0",
        port=8000
    )
