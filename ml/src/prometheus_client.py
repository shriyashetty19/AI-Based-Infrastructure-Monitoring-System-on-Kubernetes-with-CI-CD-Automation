import logging
import random
from typing import Dict, Any, List
import requests

from ml.src.config import settings

logger = logging.getLogger(settings.SERVICE_NAME)


class PrometheusMetricFetcher:
    """
    Queries Prometheus API endpoints for pod and container metrics.
    Provides graceful fallback to direct scrape endpoints or synthetic baseline metrics if Prometheus is unreachable.
    """

    def __init__(self, prometheus_url: str = settings.PROMETHEUS_URL):
        self.prometheus_url = prometheus_url.rstrip("/")

    def query_instant_metric(self, query: str) -> List[Dict[str, Any]]:
        """Queries instant metric value from Prometheus."""
        try:
            url = f"{self.prometheus_url}/api/v1/query"
            response = requests.get(url, params={"query": query}, timeout=3.0)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    return data.get("data", {}).get("result", [])
        except Exception as err:
            logger.debug("Prometheus query failed for '%s': %s", query, str(err))
        return []

    def fetch_current_metrics(self, target_service_url: str = None) -> Dict[str, float]:
        """
        Fetches current cluster/service CPU, Memory, and Latency metrics.
        """
        # Try fetching real metrics from Prometheus
        cpu_results = self.query_instant_metric("simulated_cpu_usage_percent")
        mem_results = self.query_instant_metric("simulated_memory_usage_bytes")
        lat_results = self.query_instant_metric("rate(http_request_duration_seconds_sum[1m])")

        cpu_val = float(cpu_results[0]["value"][1]) if cpu_results else None
        mem_val = float(mem_results[0]["value"][1]) / (1024 * 1024) if mem_results else None
        lat_val = float(lat_results[0]["value"][1]) * 1000.0 if lat_results else None

        # Fallback to direct app scrape if Prometheus is not yet set up
        if cpu_val is None and target_service_url:
            try:
                resp = requests.get(f"{target_service_url.rstrip('/')}/metrics", timeout=2.0)
                if resp.status_code == 200:
                    for line in resp.text.splitlines():
                        if line.startswith("simulated_cpu_usage_percent"):
                            cpu_val = float(line.split()[-1])
                        elif line.startswith("simulated_memory_usage_bytes"):
                            mem_val = float(line.split()[-1]) / (1024 * 1024)
            except Exception as e:
                logger.debug("Direct metrics scrape failed: %s", str(e))

        # Synthetic metric fallback for testing/offline scenarios
        if cpu_val is None:
            cpu_val = round(random.uniform(15.0, 45.0), 2)
        if mem_val is None:
            mem_val = round(random.uniform(64.0, 256.0), 2)
        if lat_val is None:
            lat_val = round(random.uniform(10.0, 80.0), 2)

        return {
            "cpu_usage_percent": cpu_val,
            "memory_usage_mb": mem_val,
            "latency_ms": lat_val
        }
