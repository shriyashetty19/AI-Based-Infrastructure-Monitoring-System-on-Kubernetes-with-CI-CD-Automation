# System Architecture & Design

This platform provides end-to-end cloud-native monitoring, AI-driven anomaly detection, and automated CI/CD deployment on Kubernetes.

## Component Overview

```
+-----------------------------------------------------------------------------------+
|                               Kubernetes Cluster                                  |
|                               (minikube / AWS EKS)                                |
|                                                                                   |
|  +-----------------------+     Metrics      +----------------------------------+  |
|  |     Demo Service      | ---------------> |            Prometheus            |  |
|  |   (FastAPI App)       |     Scrape       |        (Metrics Engine)          |  |
|  +-----------------------+                  +----------------------------------+  |
|              ^                                               |                    |
|              | Workload                                      | Metrics Query      |
|              | Trigger                                       v                    |
|  +-----------------------+   Anomaly Flag   +----------------------------------+  |
|  |     Simulated Load    | <--------------- |   AI Anomaly Detection Service   |  |
|  |     / Work API        |                  |  (Isolation Forest + Z-Score)    |  |
|  +-----------------------+                  +----------------------------------+  |
|                                                              |                    |
|                                                              v                    |
|                                             +----------------------------------+  |
|                                             |        Grafana Dashboards        |  |
|                                             |       (Visual Monitoring)        |  |
|                                             +----------------------------------+  |
+-----------------------------------------------------------------------------------+
                                       ^
                                       | kubectl apply -k
                                       |
                   +---------------------------------------+
                   |          Jenkins CI/CD Pipeline       |
                   | (Lint -> Test -> Security -> Build)   |
                   +---------------------------------------+
```

## Data Flow
1. **Workload Ingestion**: The `demo-service` processes incoming API traffic and exports standard Prometheus metrics (`http_requests_total`, `simulated_cpu_usage_percent`, `simulated_memory_usage_bytes`).
2. **Telemetry Collection**: Prometheus scrapes metric endpoints across the namespace at 15-second intervals.
3. **AI Anomaly Detection**: The `ml-anomaly-detector` queries Prometheus metrics vectors `[CPU %, Memory MB, Latency ms]`. The Isolation Forest model evaluates decision boundaries while a Z-score engine checks statistical deviations.
4. **Alerting & Visualization**: Detected anomalies trigger Prometheus alerts and update live Grafana dashboards.
