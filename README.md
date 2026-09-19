# AI-Based Infrastructure Monitoring System on Kubernetes with CI/CD Automation

![Kubernetes](https://img.shields.io/badge/Kubernetes-Kustomize-326CE5?style=for-the-badge&logo=kubernetes)
![Docker](https://img.shields.io/badge/Docker-Non--Root_Multi--Stage-2496ED?style=for-the-badge&logo=docker)
![Jenkins](https://img.shields.io/badge/Jenkins-Declarative_Pipeline-D24939?style=for-the-badge&logo=jenkins)
![Terraform](https://img.shields.io/badge/Terraform-AWS_EKS-7B42BC?style=for-the-badge&logo=terraform)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=for-the-badge&logo=fastapi)
![scikit-learn](https://img.shields.io/badge/scikit--learn-IsolationForest-F7931E?style=for-the-badge&logo=scikitlearn)
![Prometheus](https://img.shields.io/badge/Prometheus-Config_Only-E6522C?style=for-the-badge&logo=prometheus)

**AI-Based Infrastructure Monitoring System** is a Kubernetes-native platform pairing a metrics-emitting FastAPI microservice with a second FastAPI microservice that runs a **self-trained scikit-learn Isolation Forest** model, combined with Z-score statistical analysis, to flag abnormal CPU/memory/latency patterns. It is packaged with non-root multi-stage Docker builds, Kustomize-based Kubernetes manifests for both local (Minikube) and cloud (AWS EKS) targets, an 8-stage declarative Jenkins CI/CD pipeline, and two parallel infrastructure-as-code paths (Terraform and eksctl) for provisioning AWS.

> **Status:** Built and ready to run. Not yet deployed to a live environment (local Minikube or AWS EKS) as of this writing.

---

## 🌟 Key Application Features

1. **Demo Workload Microservice (`/app`, FastAPI)** — exposes real Prometheus-format metrics (`http_requests_total`, `http_request_duration_seconds`, `simulated_cpu_usage_percent`, `simulated_memory_usage_bytes`) and synthetic workload endpoints to simulate CPU load and memory growth for testing.
2. **AI Anomaly Detection Engine (`/ml`, FastAPI)** — a self-trained scikit-learn `IsolationForest` model combined with a Z-score statistical check over a `[CPU%, Memory MB, Latency ms]` vector, evaluated on demand via `GET /api/v1/detect` or a direct custom payload via `POST /api/v1/evaluate-custom`.
3. **Three-Level Metric Fallback** — the anomaly detector tries a live Prometheus query first, falls back to scraping the demo-service directly, and falls back once more to synthetic values, so the endpoint never hard-fails with no data.
4. **Kubernetes-Native Deployment (Kustomize)** — one shared base manifest set (`k8s/base`), with a Minikube overlay (NodePort) and an AWS EKS overlay (ALB Ingress) layered on top.
5. **Least-Privilege RBAC & Non-Root Containers** — a namespace-scoped `ServiceAccount`/`Role`/`RoleBinding` limited to read-only verbs, and dedicated non-root UIDs (`10001`, `10002`) via multi-stage Docker builds.
6. **Declarative Jenkins CI/CD Pipeline** — 8 stages: checkout, lint (flake8/black), test (pytest with coverage), security scan (pip-audit, bandit, secret-pattern grep), Docker build, conditional ECR push (EKS target only), Kubernetes deploy, and a post-deploy status check.
7. **Infrastructure as Code** — two independent, complete paths to the same AWS target (VPC, EKS cluster, managed node group, 2 ECR repositories): Terraform and eksctl.
8. **Observability Configuration** — Prometheus scrape config and 5 alert rules (`HighCpuUsage`, `HighMemoryUsage`, `ServiceDown`, `AIInfrastructureAnomalyFlagged`, `AIAnomalyScoreCritical`), plus 2 Grafana dashboard JSON definitions, ready to hand to an externally-installed monitoring stack.
9. **Automated Testing** — 8 real pytest unit/integration tests across both services (FastAPI `TestClient`), run in CI with coverage reporting.

---

## 🏗️ System Architecture

```
┌───────────────────────────────────────────────────────────────────────┐
│                          Kubernetes Cluster                           │
│                        (Minikube / AWS EKS)                           │
│                                                                         │
│   ┌─────────────────────┐      /metrics       ┌─────────────────────┐ │
│   │    demo-service      │ ──────────────────▶ │      Prometheus      │ │
│   │  (FastAPI, :8000)    │      (scrape)        │  external — config   │ │
│   │  metrics + workload   │                      │  only, not deployed  │ │
│   │  simulation endpoints │                      │  by this repo's k8s  │ │
│   └─────────────────────┘                      └──────────┬──────────┘ │
│            ▲                                                │ query     │
│            │ simulate load                                  ▼           │
│   ┌─────────────────────┐   GET /api/v1/detect   ┌─────────────────────┐ │
│   │   External caller    │ ─────────────────────▶ │  ml-anomaly-detector │ │
│   │  (curl / script)      │                        │  (FastAPI, :8001)    │ │
│   └─────────────────────┘                        │  IsolationForest +    │ │
│                                                    │  Z-score check        │ │
│                                                    └──────────┬──────────┘ │
│                                                                │ updates    │
│                                                                ▼           │
│                                                     ┌─────────────────────┐│
│                                                     │      Grafana         ││
│                                                     │  external — config    ││
│                                                     │  only, not deployed    ││
│                                                     │  by this repo's k8s    ││
│                                                     └─────────────────────┘│
└───────────────────────────────────────────────────────────────────────┘
                                    ▲
                                    │ kubectl apply -k
                                    │
                ┌─────────────────────────────────────────┐
                │           Jenkins CI/CD Pipeline          │
                │ Lint → Test → Security Scan → Build →     │
                │ (Push ECR, EKS only) → Deploy → Smoke Check│
                └─────────────────────────────────────────┘
```

---

## 🚀 Quick Start Guide

### Prerequisites
- **Docker Desktop** (v24.0+)
- **kubectl** (v1.28+)
- **Minikube** (v1.32+) or Kind
- **Jenkins** (v2.400+) with Docker & Kubernetes plugins — only needed to run the CI/CD pipeline itself
- **AWS CLI** (v2.x) & **Terraform** (v1.5+) — only needed for the AWS EKS path
- **Python** (3.11+) — only needed to run tests locally outside Docker

### 1. Local Setup (Minikube)

```bash
minikube start --driver=docker --cpus=4 --memory=8192
minikube addons enable ingress
minikube addons enable metrics-server
```

```bash
eval $(minikube -p minikube docker-env)
docker build -f docker/Dockerfile.app -t demo-service:v1.0.0 .
docker build -f docker/Dockerfile.ml -t ml-anomaly-detector:v1.0.0 .
```

```bash
kubectl apply -k k8s/overlays/minikube
kubectl get pods -n ai-monitoring
kubectl get svc -n ai-monitoring
```

Trigger a simulated CPU load, then check the anomaly detector:

```bash
minikube service minikube-demo-service -n ai-monitoring --url
minikube service minikube-ml-anomaly-detector -n ai-monitoring --url

curl -X POST http://<MINIKUBE_IP>:30080/api/v1/work \
  -H "Content-Type: application/json" \
  -d '{"duration_seconds": 5.0, "intensity": 2000000}'

curl http://<MINIKUBE_IP>:30081/api/v1/detect
```

### 2. AWS EKS Deployment

```bash
cd infra/terraform
terraform init
terraform apply -auto-approve
# or: eksctl create cluster -f infra/eksctl/cluster-config.yaml

aws eks update-kubeconfig --region us-east-1 --name ai-monitoring-eks-cluster
kubectl apply -k k8s/overlays/eks
```

> Note: the EKS overlay's `Ingress` assumes the AWS Load Balancer Controller is already installed in the cluster — this repo grants the IAM policy for it (via eksctl) but does not install the controller itself.

### 3. Running Tests Locally

```bash
export PYTHONPATH=".:app:ml"
pytest app/tests/ -v --cov=app/src --cov-report=term-missing
pytest ml/tests/ -v --cov=ml/src --cov-report=term-missing
```

---

## 📁 Repository Structure

```
├── app/                      # Demo FastAPI microservice & pytest tests
│   ├── src/                  # main.py, config.py
│   └── tests/
├── ml/                       # AI Anomaly Detector (Isolation Forest engine & API)
│   ├── src/                  # main.py, detector.py, prometheus_client.py, config.py
│   └── tests/
├── docker/                   # Multi-stage, non-root Dockerfiles for both services
├── k8s/
│   ├── base/                 # Namespace, RBAC, ConfigMaps, Deployments, Services
│   └── overlays/
│       ├── minikube/         # NodePort patch
│       └── eks/               # ALB Ingress patch
├── jenkins/
│   ├── Jenkinsfile           # 8-stage declarative pipeline
│   └── scripts/              # lint.sh, test.sh, security-scan.sh, scan_secrets.py
├── infra/
│   ├── terraform/            # VPC, EKS, ECR as code
│   └── eksctl/                # Alternative EKS cluster config
├── monitoring/
│   ├── prometheus/           # Scrape config + alert rules (external Prometheus target)
│   └── grafana/dashboards/   # 2 dashboard JSON definitions (external Grafana target)
├── docs/                     # architecture.md, local-setup.md, aws-deployment.md
├── .github/                  # Issue and pull request templates
├── README.md
├── SECURITY.md
├── LICENSE
└── .env.example
```

---

## 🔒 Security & Secrets Management

- **No hardcoded credentials**: AWS keys, registry tokens, and any other secrets are managed via environment variables (`.env`, never committed) and the Jenkins credential store (`withCredentials`), not hardcoded in source.
- **Automated secret scanning**: `jenkins/scripts/security-scan.sh` scans the repository for common credential patterns (AWS keys, private-key headers) and fails the build on a match.
- **Non-root containers**: both images run as dedicated unprivileged users (`appuser:10001`, `mluser:10002`).
- **Least-privilege RBAC**: the Kubernetes `ServiceAccount` used by both Deployments is scoped to read-only verbs on a small set of resources, in a single namespace.
- For the full policy and known gaps, see [SECURITY.md](SECURITY.md).

---

## 🛣️ Future Improvements

These are honest, identified gaps from a close read of the current implementation — not yet built, listed here deliberately instead of glossed over:

- **Add authentication/authorization** — every endpoint on both services is currently open; add an API key or JWT check via FastAPI's `Depends()`.
- **Add a scheduled anomaly-detection loop** — `ANALYSIS_INTERVAL_SECONDS` is already defined in `ml/src/config.py` but unused; wire up a background task so detection runs continuously instead of only on explicit request.
- **Actually deploy Prometheus and Grafana** — currently only their configuration and dashboard JSON exist in this repo; install both (e.g. via the `kube-prometheus-stack` Helm chart) so the monitoring half of the architecture is live, not config-only.
- **Make security scanning block the build** — `pip-audit` and `bandit` findings currently only print a warning; make them fail the pipeline above a defined severity threshold.
- **Add image-layer scanning** (e.g. `trivy`) to the Jenkins pipeline, in addition to the existing dependency and static-code scans.
- **Adopt Kubernetes Secrets** (or a managed secrets service) for any future sensitive configuration, rather than relying only on environment variables and ConfigMaps.
- **Add private subnets and a NAT gateway** to the Terraform VPC module, matching the network posture the eksctl path already configures by default.
- **Install the AWS Load Balancer Controller** so the EKS overlay's `Ingress` actually provisions a working ALB.
- **Add a second `ml-anomaly-detector` replica and a HorizontalPodAutoscaler** for both services, removing the current single point of failure and enabling load-based scaling.
- **Persist anomaly history** (currently an in-memory, 100-item deque that resets on every pod restart) to a lightweight store so it survives restarts.
- **Add infrastructure-level testing** — a CI step validating the Kustomize manifests and Jenkinsfile logic itself, alongside the existing application-level pytest suite.
- **Deploy the project** — first to Minikube for local verification, then to AWS EKS, closing the gap between "written and ready" and "actually running."

---

## 📄 License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.
