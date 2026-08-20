# AWS EKS & Terraform Deployment Guide

This guide details how to provision an Amazon EKS cluster using Infrastructure as Code (Terraform or `eksctl`) and deploy the platform to AWS.

## Option A: Provisioning via Terraform

### 1. Configure AWS CLI
Ensure AWS CLI is authenticated with necessary IAM privileges:
```bash
aws configure
```

### 2. Initialize and Apply Terraform
```bash
cd infra/terraform
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

### 3. Update Kubeconfig
```bash
aws eks update-kubeconfig --region us-east-1 --name ai-monitoring-eks-cluster
```

---

## Option B: Provisioning via `eksctl`

```bash
eksctl create cluster -f infra/eksctl/cluster-config.yaml
```

---

## Deploying to EKS

Apply the AWS EKS overlay:
```bash
kubectl apply -k k8s/overlays/eks
```

Verify Ingress and AWS ALB provisioning:
```bash
kubectl get ingress -n ai-monitoring
```
