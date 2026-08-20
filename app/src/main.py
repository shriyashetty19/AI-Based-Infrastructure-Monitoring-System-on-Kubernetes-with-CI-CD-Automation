import time
import math
import logging
from typing import Dict, Any
from fastapi import FastAPI, Response, status, HTTPException
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from pydantic import BaseModel, Field

from app.src.config import settings

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(settings.APP_NAME)

app = FastAPI(
    title=settings.APP_NAME,
    description="Demo microservice for infrastructure monitoring testing",
    version="1.0.0"
)

# Prometheus Metrics Definition
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests processed",
    ["method", "endpoint", "status_code"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"]
)

SIMULATED_CPU_GAUGE = Gauge(
    "simulated_cpu_usage_percent",
    "Simulated CPU usage percentage"
)

SIMULATED_MEMORY_GAUGE = Gauge(
    "simulated_memory_usage_bytes",
    "Simulated memory allocation in bytes"
)

WORKLOAD_EXECUTIVE_COUNT = Counter(
    "workload_executions_total",
    "Total number of compute workload executions completed"
)

# In-memory allocated state for synthetic memory testing
memory_buffer = []


class WorkloadRequest(BaseModel):
    duration_seconds: float = Field(default=1.0, ge=0.1, le=10.0)
    intensity: int = Field(default=100000, ge=1000, le=5000000)


class MemorySpikeRequest(BaseModel):
    size_mb: int = Field(default=50, ge=1, le=500)


@app.middleware("http")
async def track_metrics_middleware(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    endpoint = request.url.path
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=endpoint,
        status_code=response.status_code
    ).inc()
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=endpoint
    ).observe(duration)
    
    return response


@app.get("/", tags=["Health"])
def read_root() -> Dict[str, str]:
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV
    }


@app.get("/health", tags=["Health"])
def health_check() -> Dict[str, str]:
    return {"status": "UP"}


@app.get("/metrics", tags=["Monitoring"])
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/api/v1/work", tags=["Workload"])
def execute_workload(req: WorkloadRequest) -> Dict[str, Any]:
    """
    Simulates CPU intensive operations by calculating prime factors or trigonometry functions.
    """
    start_time = time.time()
    iterations = 0
    end_time = start_time + req.duration_seconds
    
    # Simulate CPU intensive loop
    while time.time() < end_time:
        for _ in range(req.intensity):
            _ = math.sin(iterations) * math.cos(iterations)
            iterations += 1
            
    elapsed = time.time() - start_time
    calculated_cpu = min(99.9, (req.intensity / 50000.0) * 15.0 + 10.0)
    SIMULATED_CPU_GAUGE.set(calculated_cpu)
    WORKLOAD_EXECUTIVE_COUNT.inc()
    
    logger.info("Executed workload: %d iterations in %.2f seconds", iterations, elapsed)
    return {
        "status": "completed",
        "iterations": iterations,
        "elapsed_seconds": elapsed,
        "simulated_cpu_usage": calculated_cpu
    }


@app.post("/api/v1/simulate-memory", tags=["Workload"])
def simulate_memory_spike(req: MemorySpikeRequest) -> Dict[str, Any]:
    """
    Simulates memory allocations by appending bytes to a global buffer.
    """
    global memory_buffer
    byte_count = req.size_mb * 1024 * 1024
    chunk = bytearray(byte_count)
    memory_buffer.append(chunk)
    
    total_allocated_bytes = sum(len(b) for b in memory_buffer)
    SIMULATED_MEMORY_GAUGE.set(total_allocated_bytes)
    
    logger.info("Allocated %d MB. Total simulated memory: %d MB", req.size_mb, total_allocated_bytes / (1024 * 1024))
    return {
        "status": "memory_allocated",
        "allocated_mb": req.size_mb,
        "total_simulated_mb": total_allocated_bytes / (1024 * 1024)
    }


@app.delete("/api/v1/clear-memory", tags=["Workload"])
def clear_simulated_memory() -> Dict[str, Any]:
    """
    Clears allocated memory buffer to restore baseline usage.
    """
    global memory_buffer
    memory_buffer.clear()
    SIMULATED_MEMORY_GAUGE.set(0)
    return {"status": "memory_cleared", "total_simulated_mb": 0}


@app.get("/api/v1/status", tags=["Status"])
def get_status() -> Dict[str, Any]:
    total_memory_bytes = sum(len(b) for b in memory_buffer)
    return {
        "service": settings.APP_NAME,
        "uptime_status": "operational",
        "active_allocated_chunks": len(memory_buffer),
        "total_allocated_mb": total_memory_bytes / (1024 * 1024)
    }
