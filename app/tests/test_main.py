import pytest
from fastapi.testclient import TestClient
from app.src.main import app

client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "UP"}


def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text


def test_execute_workload():
    response = client.post("/api/v1/work", json={"duration_seconds": 0.2, "intensity": 5000})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["iterations"] > 0


def test_simulate_memory_and_clear():
    # Allocate memory
    alloc_res = client.post("/api/v1/simulate-memory", json={"size_mb": 2})
    assert alloc_res.status_code == 200
    assert alloc_res.json()["status"] == "memory_allocated"
    
    # Check status
    status_res = client.get("/api/v1/status")
    assert status_res.status_code == 200
    assert status_res.json()["total_allocated_mb"] >= 2.0
    
    # Clear memory
    clear_res = client.delete("/api/v1/clear-memory")
    assert clear_res.status_code == 200
    assert clear_res.json()["status"] == "memory_cleared"
