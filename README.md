# AI-Based Infrastructure Monitoring System on Kubernetes with CI/CD Automation

A cloud-native monitoring and automation platform that deploys microservices to Kubernetes, collects real-time node and container metrics with Prometheus, detects operational anomalies using Isolation Forest ML models, and automates end-to-end container builds and deployments via a Jenkins CI/CD pipeline.

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

---

## Features

- **Microservice Workload (`/app`)**: Lightweight Python FastAPI service emitting Prometheus metrics (`http_requests_total`, `simulated_cpu_usage_percent`, `simulated_memory_usage_bytes`) and exposing synthetic workload endpoints for testing.
- **AI Anomaly Detection (`/ml`)**: Machine learning engine powered by `scikit-learn` Isolation Forest and Z-score statistical evaluation to identify CPU/Memory spikes and latency degradation in real-time.
- **Security-Hardened Docker Containers (`/docker`)**: Multi-stage, non-root container builds with explicit security contexts and minimal `python:3.11-slim` base images.
- **Kubernetes Architecture (`/k8s`)**: Kustomize base structure with tailored overlays for local `minikube` deployment (NodePort exposed) and cloud `AWS EKS` deployment (AWS ALB Ingress).
- **Declarative CI/CD (`/jenkins`)**: End-to-end Jenkinsfile enforcing static analysis, unit test coverage, dependency vulnerability scanning, image building, registry push, and automated deployment.
- **Infrastructure as Code (`/infra`)**: Production-ready Terraform modules and `eksctl` configuration files for automated AWS VPC, ECR, and EKS cluster provisioning.
- **Monitoring & Alerting (`/monitoring`)**: Pre-configured Prometheus scrape targets, Alertmanager rules for CPU/RAM/AI anomalies, and Grafana dashboard JSONs.

---

## Repository Structure

```
├── app/                        # Demo FastAPI microservice & unit tests
├── ml/                         # AI Anomaly Detector (Isolation Forest engine & API)
├── docker/                     # Multi-stage, non-root Dockerfiles
├── k8s/                        # Kubernetes Kustomize manifests (Base + Overlays)
├── jenkins/                    # Declarative Jenkinsfile & helper scripts
├── infra/                      # Terraform & eksctl IaC for AWS EKS provisioning
├── monitoring/                 # Prometheus alert rules & Grafana dashboard JSONs
├── docs/                       # Architectural design & step-by-step guides
├── .github/                    # GitHub issue and pull request templates
├── README.md                   # Project overview & operational guide
├── SECURITY.md                 # Security & vulnerability management policy
├── LICENSE                     # MIT License
├── .gitignore                  # Git exclusion rules
└── .env.example                # Non-sensitive environment variable template
```

---

## Prerequisites

- **Docker Desktop** (`v24.0+`)
- **kubectl** (`v1.28+`)
- **Minikube** (`v1.32+`) or **Kind** (for local execution)
- **Jenkins** (`v2.400+`) with Docker & Kubernetes plugins
- **AWS CLI** (`v2.x`) & **Terraform** (`v1.5+`) (for cloud deployment)
- **Python** (`3.11+`)

---

## Local Setup Instructions (Minikube)

Follow these exact commands to reproduce the entire environment locally without any cloud costs:

1. **Start Minikube Cluster**:
   ```bash
   minikube start --driver=docker --cpus=4 --memory=8192
   minikube addons enable ingress
   minikube addons enable metrics-server
   ```

2. **Build Docker Images inside Minikube Environment**:
   ```bash
   eval $(minikube -p minikube docker-env)
   docker build -f docker/Dockerfile.app -t demo-service:v1.0.0 .
   docker build -f docker/Dockerfile.ml -t ml-anomaly-detector:v1.0.0 .
   ```

3. **Deploy Kubernetes Manifests**:
   ```bash
   kubectl apply -k k8s/overlays/minikube
   ```

4. **Verify Deployment Health**:
   ```bash
   kubectl get pods -n ai-monitoring
   kubectl get svc -n ai-monitoring
   ```

5. **Simulate Workload & Verify AI Detection**:
   Get service URLs:
   ```bash
   minikube service minikube-demo-service -n ai-monitoring --url
   minikube service minikube-ml-anomaly-detector -n ai-monitoring --url
   ```
   Trigger CPU load spike:
   ```bash
   curl -X POST http://<MINIKUBE_IP>:30080/api/v1/work -H "Content-Type: application/json" -d '{"duration_seconds": 5.0, "intensity": 2000000}'
   ```
   Inspect AI detection output:
   ```bash
   curl http://<MINIKUBE_IP>:30081/api/v1/detect
   ```

---

## AWS EKS Deployment Instructions

1. **Provision Infrastructure with Terraform**:
   ```bash
   cd infra/terraform
   terraform init
   terraform apply -auto-approve
   ```
   *(Or using `eksctl`: `eksctl create cluster -f infra/eksctl/cluster-config.yaml`)*

2. **Configure Kubeconfig**:
   ```bash
   aws eks update-kubeconfig --region us-east-1 --name ai-monitoring-eks-cluster
   ```

3. **Deploy EKS Manifests**:
   ```bash
   kubectl apply -k k8s/overlays/eks
   ```

---

## How the CI/CD Pipeline Works

The Jenkins pipeline defined in `jenkins/Jenkinsfile` automates software delivery through 8 distinct stages:

1. **Checkout & Environment Setup**: Clones repository, extracts short git SHA for image tagging.
2. **Lint & Code Format**: Runs `flake8` and `black` across `/app` and `/ml` modules.
3. **Unit & Integration Tests**: Executes `pytest` with coverage reporting.
4. **Security Audit**: Scans dependencies via `pip-audit` and static code via `bandit` to block vulnerabilities.
5. **Build Docker Images**: Constructs multi-stage container images using non-root users.
6. **Push Registry**: Authenticates with AWS ECR via Jenkins credentials store (`credentials('aws-ecr-credentials')`) and pushes tagged images.
7. **Deploy to Kubernetes**: Applies Kustomize manifests (`kubectl apply -k`) to the target cluster environment.
8. **Post-Deploy Smoke Test**: Runs `kubectl rollout status` and verifies workload health.

---

## Monitoring & Grafana Dashboards

- **Prometheus Scrape Configuration**: Configured in `monitoring/prometheus/prometheus-config.yaml` to scrape metrics at 15-second intervals.
- **Alert Rules**: `monitoring/prometheus/alerts.yaml` defines rules for `HighCpuUsage`, `HighMemoryUsage`, `ServiceDown`, and `AIInfrastructureAnomalyFlagged`.
- **Grafana Dashboards**:
  - `monitoring/grafana/dashboards/cluster-overview.json`: Visualizes CPU usage, Memory allocation, Request throughput, and P95 latency.
  - `monitoring/grafana/dashboards/ai-anomaly-detection.json`: Tracks real-time Isolation Forest decision scores and active anomaly status flags.

---

## How the AI Anomaly Detector Works & Trade-Offs

### Model Architecture
The anomaly detection component (`/ml`) uses **Isolation Forest** from `scikit-learn` augmented with statistical Z-score baseline evaluation:
- **Feature Vector**: `[CPU %, Memory MB, Request Latency ms]`
- **Isolation Forest**: Builds an ensemble of isolation trees to isolate anomalous data points (returns score < 0 for anomalies).
- **Z-Score Thresholding**: Evaluates standard deviations from baseline mean ($Z = \frac{x - \mu}{\sigma}$) to catch single-metric spikes even during cold starts.

### Technical Trade-Off Explanation
> **Why Isolation Forest instead of a Deep Learning model?**  
> We deliberately chose Isolation Forest and Z-score statistical modeling over complex deep neural networks (like LSTM autoencoders) to ensure the system is extremely lightweight, fast to train (<100ms), and fully reproducible on local developer laptops or minikube clusters without requiring specialized GPU runtimes or high memory overhead.

---

## Security

This repository follows strict security principles:
- **Zero Secrets Committed**: All credentials, tokens, and keys are managed exclusively via environment variables, Kubernetes Secrets, or Jenkins credential store bindings.
- **Non-Root Containers**: Container images run as unprivileged user UIDs (`10001` and `10002`).
- **Least-Privilege RBAC**: Kubernetes ServiceAccounts are granted read-only namespace scopes.
- For complete security policies and vulnerability disclosure guidelines, see [SECURITY.md](SECURITY.md).

---

## License & Contributing

Licensed under the [MIT License](LICENSE). Contributions, bug reports, and enhancements are welcome via Pull Requests.
