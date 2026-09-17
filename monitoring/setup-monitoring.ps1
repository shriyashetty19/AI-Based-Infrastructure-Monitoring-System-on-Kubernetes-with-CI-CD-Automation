# Deploys kube-prometheus-stack (Prometheus + Grafana + Alertmanager) into a
# `monitoring` namespace, wires it to the ai-monitoring app namespace, imports
# the repo's Grafana dashboards, and verifies scraping.
#
# Prerequisite: `kubectl cluster-info` must already succeed against a running
# minikube cluster with k8s/overlays/minikube applied (namespace ai-monitoring).
#
# Run from the repo root: .\monitoring\setup-monitoring.ps1

$ErrorActionPreference = "Stop"

Write-Host "==> 1. Verifying cluster reachability" -ForegroundColor Cyan
kubectl cluster-info

Write-Host "==> 2. Installing kube-prometheus-stack into namespace 'monitoring'" -ForegroundColor Cyan
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts 2>$null
helm repo update
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack `
    --namespace monitoring --create-namespace `
    -f monitoring/helm/kube-prometheus-stack-values.yaml `
    --wait --timeout 10m

Write-Host "==> 3. Applying ServiceMonitors + PrometheusRule for ai-monitoring" -ForegroundColor Cyan
kubectl apply -f monitoring/prometheus/servicemonitors.yaml
kubectl apply -f monitoring/prometheus/prometheus-rules.yaml

Write-Host "==> 4. Importing Grafana dashboards as ConfigMaps (grafana_dashboard=1 sidecar label)" -ForegroundColor Cyan
kubectl create configmap grafana-dashboard-cluster-overview `
    --from-file=cluster-overview.json=monitoring/grafana/dashboards/cluster-overview.json `
    -n monitoring --dry-run=client -o yaml | kubectl label -f - --local -o yaml grafana_dashboard="1" | kubectl apply -f -

kubectl create configmap grafana-dashboard-ai-anomaly-detection `
    --from-file=ai-anomaly-detection.json=monitoring/grafana/dashboards/ai-anomaly-detection.json `
    -n monitoring --dry-run=client -o yaml | kubectl label -f - --local -o yaml grafana_dashboard="1" | kubectl apply -f -

Write-Host "==> 5. Grafana admin password" -ForegroundColor Cyan
$pw = kubectl get secret kube-prometheus-stack-grafana -n monitoring -o jsonpath="{.data.admin-password}"
[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($pw))
Write-Host "(username: admin)"

Write-Host "==> 6. Checking Prometheus targets for demo-service / ml-anomaly-detector" -ForegroundColor Cyan
kubectl get servicemonitor -n ai-monitoring
Write-Host "Run this separately to browse Targets in-browser:"
Write-Host "  kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090"
Write-Host "  then open http://localhost:9090/targets"

Write-Host "==> 7. Port-forwarding Grafana on http://localhost:3000 (Ctrl+C to stop)" -ForegroundColor Cyan
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80
