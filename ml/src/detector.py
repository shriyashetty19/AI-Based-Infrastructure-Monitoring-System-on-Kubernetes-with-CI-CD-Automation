import logging
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from ml.src.config import settings

logger = logging.getLogger(settings.SERVICE_NAME)


class InfrastructureAnomalyDetector:
    """
    ML Anomaly Detector using scikit-learn Isolation Forest with statistical Z-score baseline fallback.
    Analyzes multi-dimensional infrastructure telemetry vectors: [CPU %, Memory MB, Latency ms].
    """

    def __init__(
        self,
        contamination: float = settings.CONTAMINATION_FACTOR,
        z_score_threshold: float = settings.Z_SCORE_THRESHOLD
    ):
        self.contamination = contamination
        self.z_score_threshold = z_score_threshold
        self.model = IsolationForest(
            contamination=self.contamination,
            random_state=42,
            n_estimators=100
        )
        self.is_trained = False
        self.baseline_stats: Dict[str, Dict[str, float]] = {}
        self._initialize_baseline_model()

    def _initialize_baseline_model(self):
        """Initializes baseline distribution for cold-start initialization."""
        np.random.seed(42)
        # Baseline normal operations dataset
        cpu_samples = np.random.normal(loc=25.0, scale=8.0, size=200)
        mem_samples = np.random.normal(loc=128.0, scale=30.0, size=200)
        lat_samples = np.random.normal(loc=25.0, scale=10.0, size=200)

        # Clip negative values
        cpu_samples = np.clip(cpu_samples, 2.0, 95.0)
        mem_samples = np.clip(mem_samples, 32.0, 1024.0)
        lat_samples = np.clip(lat_samples, 1.0, 500.0)

        X_baseline = np.column_stack([cpu_samples, mem_samples, lat_samples])
        self.fit(X_baseline)

    def fit(self, X: np.ndarray) -> None:
        """Trains Isolation Forest model and computes feature mean/std baseline statistics."""
        if len(X) < 10:
            logger.warning("Insufficient samples to train model (%d samples)", len(X))
            return

        self.model.fit(X)
        self.is_trained = True

        self.baseline_stats = {
            "cpu": {"mean": float(np.mean(X[:, 0])), "std": float(np.std(X[:, 0]) + 1e-5)},
            "memory": {"mean": float(np.mean(X[:, 1])), "std": float(np.std(X[:, 1]) + 1e-5)},
            "latency": {"mean": float(np.mean(X[:, 2])), "std": float(np.std(X[:, 2]) + 1e-5)},
        }
        logger.info("Anomaly detector model trained successfully on %d metric vectors", len(X))

    def evaluate_vector(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """
        Evaluates an instant metric dictionary:
        {'cpu_usage_percent': float, 'memory_usage_mb': float, 'latency_ms': float}
        """
        cpu = float(metrics.get("cpu_usage_percent", 0.0))
        mem = float(metrics.get("memory_usage_mb", 0.0))
        lat = float(metrics.get("latency_ms", 0.0))

        X_sample = np.array([[cpu, mem, lat]])

        # Predict using IsolationForest (-1 for anomaly, 1 for normal)
        prediction = int(self.model.predict(X_sample)[0])
        decision_score = float(self.model.decision_function(X_sample)[0])

        # Compute Statistical Z-Scores
        cpu_z = (cpu - self.baseline_stats["cpu"]["mean"]) / self.baseline_stats["cpu"]["std"]
        mem_z = (mem - self.baseline_stats["memory"]["mean"]) / self.baseline_stats["memory"]["std"]
        lat_z = (lat - self.baseline_stats["latency"]["mean"]) / self.baseline_stats["latency"]["std"]

        max_z_score = max(abs(cpu_z), abs(mem_z), abs(lat_z))
        is_z_anomaly = max_z_score > self.z_score_threshold

        is_anomaly = (prediction == -1) or is_z_anomaly
        confidence = min(0.99, max(0.50, abs(decision_score) * 2.0 + (max_z_score / 10.0)))

        # Determine primary contributing metric
        z_map = {"cpu_usage_percent": abs(cpu_z), "memory_usage_mb": abs(mem_z), "latency_ms": abs(lat_z)}
        primary_driver = max(z_map, key=z_map.get)

        severity = "NORMAL"
        if is_anomaly:
            if max_z_score > 5.0 or decision_score < -0.2:
                severity = "CRITICAL"
            elif max_z_score > 3.0 or decision_score < -0.05:
                severity = "WARNING"
            else:
                severity = "LOW"

        return {
            "is_anomaly": is_anomaly,
            "severity": severity,
            "isolation_forest_prediction": prediction,
            "anomaly_score": round(decision_score, 4),
            "max_z_score": round(max_z_score, 2),
            "confidence": round(confidence, 2),
            "primary_driver": primary_driver,
            "metrics_evaluated": {
                "cpu_usage_percent": cpu,
                "memory_usage_mb": mem,
                "latency_ms": lat
            },
            "z_scores": {
                "cpu": round(cpu_z, 2),
                "memory": round(mem_z, 2),
                "latency": round(lat_z, 2)
            }
        }
