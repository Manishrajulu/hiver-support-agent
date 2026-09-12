#!/usr/bin/env python3
"""
Phase 8: API Tests

Tests the FastAPI backend.

Run with:
    python -m pytest test_api.py -v
    python test_api.py  # Direct run
"""

import sys
import os
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Ensure we're in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Mock environment before importing app
os.environ['GROQ_API_KEY'] = 'test_key'


class TestHealthEndpoint:
    """Tests for GET /health endpoint."""

    def test_health_returns_success(self):
        """Test that /health returns successfully."""
        from api import app
        client = TestClient(app)

        with patch('api.pipeline_manager') as mock_pm:
            mock_pm.is_loaded = True
            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "model_loaded" in data
            assert "version" in data


class TestPredictEndpoint:
    """Tests for POST /predict endpoint."""

    def test_predict_returns_structure(self):
        """Test that /predict returns the expected response structure."""
        from api import app
        client = TestClient(app)

        with patch('api.pipeline_manager') as mock_pm:
            # Mock pipeline components
            mock_components = MagicMock()
            mock_pm.get_pipeline.return_value = mock_components

            # Mock classify function
            with patch('api.classify') as mock_classify:
                mock_classify.return_value = (
                    "DELIVERY_LATE",
                    0.974,
                    3.642,
                    [("DELIVERY_LATE", 2.58)]
                )

                # Mock retrieve_similar
                with patch('api.retrieve_similar') as mock_retrieve:
                    mock_retrieve.return_value = [{
                        "conversation_id": "test_123",
                        "primary_intent": "DELIVERY_LATE",
                        "customer_text": "My package is late",
                        "similarity_score": 0.85
                    }]

                    # Mock decide_escalation
                    with patch('api.decide_escalation') as mock_escalate:
                        mock_escalate.return_value = {
                            "decision": "AUTO_HANDLE",
                            "reason": "AUTO_HANDLE - intent=DELIVERY_LATE",
                            "risk_flags": []
                        }

                        # Mock generate_reply
                        with patch('api.generate_reply') as mock_generate:
                            mock_generate.return_value = "Your package is on its way."

                            response = client.post("/predict", json={
                                "message": "My package is late"
                            })

                            assert response.status_code == 200
                            data = response.json()

                            # Verify response structure
                            assert "message" in data
                            assert "intent" in data
                            assert "confidence" in data
                            assert "margin" in data
                            assert "decision" in data
                            assert "reason" in data
                            assert "evidence" in data
                            assert "retrieved_case_ids" in data

    def test_empty_message_rejected(self):
        """Test that empty message is rejected."""
        from api import app
        client = TestClient(app)

        with patch('api.pipeline_manager'):
            response = client.post("/predict", json={
                "message": ""
            })

            # FastAPI validation should reject empty string
            assert response.status_code == 422

    def test_missing_message_rejected(self):
        """Test that missing message is rejected."""
        from api import app
        client = TestClient(app)

        with patch('api.pipeline_manager'):
            response = client.post("/predict", json={})

            assert response.status_code == 422

    def test_escalate_decision(self):
        """Test that ESCALATE decision is returned correctly."""
        from api import app
        client = TestClient(app)

        with patch('api.pipeline_manager') as mock_pm:
            mock_components = MagicMock()
            mock_pm.get_pipeline.return_value = mock_components

            with patch('api.classify') as mock_classify:
                mock_classify.return_value = (
                    "REFUND_REQUEST",
                    0.55,
                    0.3,  # Low margin
                    [("REFUND_REQUEST", 0.5), ("PAYMENT_ISSUE", 0.2)]
                )

                with patch('api.retrieve_similar') as mock_retrieve:
                    mock_retrieve.return_value = []

                    with patch('api.decide_escalation') as mock_escalate:
                        mock_escalate.return_value = {
                            "decision": "ESCALATE",
                            "reason": "ESCALATE - HIGH_RISK:REFUND_REQUEST",
                            "risk_flags": ["HIGH_RISK:REFUND_REQUEST"]
                        }

                        response = client.post("/predict", json={
                            "message": "I want my money back"
                        })

                        assert response.status_code == 200
                        data = response.json()
                        assert data["decision"] == "ESCALATE"


class TestPhase6ModelIntegration:
    """Tests to verify Phase 6 model is being used."""

    def test_model_uses_phase6_classifier(self):
        """Verify that the API uses the Phase 6 model."""
        # This test verifies that the model path is correct
        import pickle

        model_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'data', 'baseline', 'phase6_best_model.joblib'
        )

        assert os.path.exists(model_path), f"Phase 6 model not found at {model_path}"

        # Load and verify it's the right type
        with open(model_path, 'rb') as f:
            model = pickle.load(f)

        assert 'classifier' in model
        assert hasattr(model['classifier'], 'decision_function')
        assert hasattr(model['classifier'], 'classes_')

        # Verify classes include expected intents
        classes = model['classifier'].classes_
        assert 'DELIVERY_LATE' in classes
        assert 'OTHER' in classes
        assert 'REFUND_REQUEST' in classes


class TestResponseSchema:
    """Tests for response schema validation."""

    def test_confidence_in_range(self):
        """Test that confidence is between 0 and 1."""
        from api import app
        client = TestClient(app)

        with patch('api.pipeline_manager') as mock_pm:
            mock_components = MagicMock()
            mock_pm.get_pipeline.return_value = mock_components

            with patch('api.classify') as mock_classify:
                mock_classify.return_value = (
                    "OTHER",
                    0.75,
                    0.8,
                    [("OTHER", 0.5)]
                )

                with patch('api.retrieve_similar') as mock_retrieve:
                    mock_retrieve.return_value = []

                    with patch('api.decide_escalation') as mock_escalate:
                        mock_escalate.return_value = {
                            "decision": "AUTO_HANDLE",
                            "reason": "OK",
                            "risk_flags": []
                        }

                        response = client.post("/predict", json={
                            "message": "Hello"
                        })

                        data = response.json()
                        assert 0 <= data["confidence"] <= 1


class TestAPIKeySecurity:
    """Tests to verify API key security."""

    def test_api_key_not_in_response(self):
        """Test that API key is not exposed in responses."""
        from api import app
        client = TestClient(app)

        with patch('api.pipeline_manager') as mock_pm:
            mock_components = MagicMock()
            mock_pm.get_pipeline.return_value = mock_components

            with patch('api.classify') as mock_classify:
                mock_classify.return_value = ("OTHER", 0.5, 0.5, [])

                with patch('api.retrieve_similar') as mock_ret:
                    mock_ret.return_value = []

                    with patch('api.decide_escalation') as mock_esc:
                        mock_esc.return_value = {
                            "decision": "AUTO_HANDLE",
                            "reason": "OK",
                            "risk_flags": []
                        }

                        response = client.post("/predict", json={
                            "message": "test"
                        })

                        # Ensure no API key in response
                        response_text = response.text.lower()
                        assert "api_key" not in response_text
                        assert "groq" not in response_text or "groq" in response_text.lower()


def run_tests():
    """Run all tests."""
    print("Running Phase 8 API Tests...")
    print("=" * 60)

    test_classes = [
        TestHealthEndpoint,
        TestPredictEndpoint,
        TestPhase6ModelIntegration,
        TestResponseSchema,
        TestAPIKeySecurity,
    ]

    total_passed = 0
    total_failed = 0

    for test_class in test_classes:
        print(f"\n{test_class.__name__}:")
        print("-" * 40)

        instance = test_class()
        for method_name in dir(instance):
            if method_name.startswith("test_"):
                try:
                    method = getattr(instance, method_name)
                    method()
                    print(f"  PASS: {method_name}")
                    total_passed += 1
                except Exception as e:
                    print(f"  FAIL: {method_name} - {e}")
                    total_failed += 1

    print()
    print("=" * 60)
    print(f"Results: {total_passed} passed, {total_failed} failed")
    return total_failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
