import time
import logging
from typing import Dict, Any, List
from collections import deque
from fastapi import FastAPI, Response, BackgroundTasks
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
from pydantic import BaseModel, Field

from ml.src.config import settings
from ml.src.prometheus_client import PrometheusMetricFetcher
from ml.src.detector import InfrastructureAnomalyDetector

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(settings.SERVICE_NAME)

app = FastAPI(
    title=settings.SERVICE_NAME,
    description="AI Anomaly Detection Microservice for Kubernetes Infrastructure",
    version="1.0.0"
)

# Initialize Components
fetcher = PrometheusMetricFetcher()
detector = InfrastructureAnomalyDetector()

# History store for anomaly events (keep last 100)
anomaly_history: deque = deque(maxlen=100)

# Prometheus Metrics Definition for ML Service
AI_ANOMALY_GAUGE = Gauge(
    "ai_anomaly_flag",
    "Indicates whether an anomaly is active (1 for anomaly, 0 for normal)"
)

AI_ANOMALY_SCORE_GAUGE = Gauge(
    "ai_anomaly_score",
    "Raw decision score from Isolation Forest model"
)

ANOMALY_EVALUATION_COUNTER = Counter(
    "ai_metric_evaluations_total",
    "Total metric vectors evaluated by ML anomaly detector",
    ["result"]
)


class CustomEvaluationRequest(BaseModel):
    cpu_usage_percent: float = Field(..., ge=0.0, le=100.0)
    memory_usage_mb: float = Field(..., ge=0.0, le=16384.0)
    latency_ms: float = Field(..., ge=0.0, le=30000.0)


@app.get("/", tags=["Health"])
def read_root() -> Dict[str, str]:
    return {
        "service": settings.SERVICE_NAME,
        "status": "online",
        "model_trained": str(detector.is_trained)
    }


@app.get("/health", tags=["Health"])
def health_check() -> Dict[str, str]:
    return {"status": "UP"}


@app.get("/metrics", tags=["Monitoring"])
def get_metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/v1/detect", tags=["Anomaly Detection"])
def evaluate_current_infrastructure(target_service_url: str = None) -> Dict[str, Any]:
    """
    Fetches real-time metric vectors from Prometheus/Service and runs ML anomaly detection.
    """
    metrics = fetcher.fetch_current_metrics(target_service_url=target_service_url)
    result = detector.evaluate_vector(metrics)
    result["timestamp"] = time.time()

    # Update Prometheus Exporter Gauges
    is_anomaly = 1 if result["is_anomaly"] else 0
    AI_ANOMALY_GAUGE.set(is_anomaly)
    AI_ANOMALY_SCORE_GAUGE.set(result["anomaly_score"])
    ANOMALY_EVALUATION_COUNTER.labels(result="anomaly" if is_anomaly else "normal").inc()

    if is_anomaly:
        anomaly_history.appendleft(result)
        logger.warning(
            "ANOMALY DETECTED: Severity=%s | Primary Driver=%s | Z-Score=%.2f",
            result["severity"], result["primary_driver"], result["max_z_score"]
        )

    return result


@app.post("/api/v1/evaluate-custom", tags=["Anomaly Detection"])
def evaluate_custom_metrics(payload: CustomEvaluationRequest) -> Dict[str, Any]:
    """
    Evaluates custom payload metric values directly.
    """
    metrics = {
        "cpu_usage_percent": payload.cpu_usage_percent,
        "memory_usage_mb": payload.memory_usage_mb,
        "latency_ms": payload.latency_ms
    }
    result = detector.evaluate_vector(metrics)
    result["timestamp"] = time.time()
    return result


@app.get("/api/v1/anomalies/history", tags=["Anomaly History"])
def get_anomaly_history(limit: int = 20) -> List[Dict[str, Any]]:
    """Returns recent anomaly detections."""
    return list(anomaly_history)[:limit]


@app.get("/api/v1/status", tags=["Status"])
def get_model_status() -> Dict[str, Any]:
    return {
        "service": settings.SERVICE_NAME,
        "is_trained": detector.is_trained,
        "contamination": detector.contamination,
        "z_score_threshold": detector.z_score_threshold,
        "baseline_stats": detector.baseline_stats,
        "anomaly_events_recorded": len(anomaly_history)
    }
