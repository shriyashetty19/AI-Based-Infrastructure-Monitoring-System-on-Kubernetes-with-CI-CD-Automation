# Local Setup Guide (Minikube / Kind)

This guide walks through deploying and testing the AI Infrastructure Monitoring platform locally using Minikube.

## Prerequisites
- Docker Desktop or Containerd
- Minikube (`v1.32+`) or Kind
- `kubectl` (`v1.28+`)
- Python 3.11+ (optional for local pytest)

## Step 1: Start Minikube
```bash
minikube start --driver=docker --cpus=4 --memory=8192
minikube addons enable ingress
minikube addons enable metrics-server
```

## Step 2: Build Images inside Minikube Docker Daemon
```bash
eval $(minikube -p minikube docker-env)

# Build Demo App
docker build -f docker/Dockerfile.app -t demo-service:v1.0.0 .

# Build ML Anomaly Detector
docker build -f docker/Dockerfile.ml -t ml-anomaly-detector:v1.0.0 .
```

## Step 3: Deploy Manifests via Kustomize
```bash
kubectl apply -k k8s/overlays/minikube
```

Verify pod readiness:
```bash
kubectl get pods -n ai-monitoring -w
```

## Step 4: Access Services & Simulate Anomalies
Get NodePort URLs:
```bash
minikube service minikube-demo-service -n ai-monitoring --url
minikube service minikube-ml-anomaly-detector -n ai-monitoring --url
```

Trigger simulated CPU spike to test AI detector:
```bash
curl -X POST http://<MINIKUBE_IP>:30080/api/v1/work -H "Content-Type: application/json" -d '{"duration_seconds": 5.0, "intensity": 2000000}'
```

Query AI anomaly detection status:
```bash
curl http://<MINIKUBE_IP>:30081/api/v1/detect
```
