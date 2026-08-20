import pytest
from fastapi.testclient import TestClient
from ml.src.main import app
from ml.src.detector import InfrastructureAnomalyDetector

client = TestClient(app)


def test_detector_normal_vector():
    detector = InfrastructureAnomalyDetector()
    normal_metrics = {
        "cpu_usage_percent": 25.0,
        "memory_usage_mb": 128.0,
        "latency_ms": 20.0
    }
    res = detector.evaluate_vector(normal_metrics)
    assert "is_anomaly" in res
    assert res["is_anomaly"] is False
    assert res["severity"] == "NORMAL"


def test_detector_extreme_spike_anomaly():
    detector = InfrastructureAnomalyDetector()
    extreme_metrics = {
        "cpu_usage_percent": 98.5,
        "memory_usage_mb": 2048.0,
        "latency_ms": 1500.0
    }
    res = detector.evaluate_vector(extreme_metrics)
    assert res["is_anomaly"] is True
    assert res["severity"] in ["CRITICAL", "WARNING"]
    assert res["max_z_score"] > 3.0


def test_ml_api_endpoints():
    health_res = client.get("/health")
    assert health_res.status_code == 200

    metrics_res = client.get("/metrics")
    assert metrics_res.status_code == 200

    custom_eval_res = client.post(
        "/api/v1/evaluate-custom",
        json={"cpu_usage_percent": 15.0, "memory_usage_mb": 100.0, "latency_ms": 12.0}
    )
    assert custom_eval_res.status_code == 200
    assert custom_eval_res.json()["is_anomaly"] is False

    detect_res = client.get("/api/v1/detect")
    assert detect_res.status_code == 200
    assert "is_anomaly" in detect_res.json()
