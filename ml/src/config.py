import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "ai-anomaly-detector"
    PORT: int = int(os.getenv("PORT", "8001"))
    PROMETHEUS_URL: str = os.getenv("PROMETHEUS_URL", "http://prometheus-k8s.monitoring.svc.cluster.local:9090")
    CONTAMINATION_FACTOR: float = float(os.getenv("CONTAMINATION_FACTOR", "0.05"))
    Z_SCORE_THRESHOLD: float = float(os.getenv("Z_SCORE_THRESHOLD", "3.0"))
    ANALYSIS_INTERVAL_SECONDS: int = int(os.getenv("ANALYSIS_INTERVAL_SECONDS", "15"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
