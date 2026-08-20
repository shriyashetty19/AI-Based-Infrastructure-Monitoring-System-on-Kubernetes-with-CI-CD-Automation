# Security Policy

## Overview
Security is a core requirement for this infrastructure monitoring platform. This repository enforces zero-trust secret management, non-root container isolation, and least-privilege role-based access control (RBAC).

## Secret Management Policy
- **No Hardcoded Credentials**: API keys, AWS credentials, database passwords, or kubeconfig secrets are strictly prohibited from being committed to source control.
- **Environment & Kubernetes Secrets**: All sensitive variables are injected runtime via environment variables, Kubernetes Secrets, or AWS Secrets Manager.
- **CI/CD Binding**: Jenkins declarative pipelines retrieve AWS and registry authentication tokens using the Jenkins Credential Store (`withCredentials` binding).

## Container Security
- Docker images run as unprivileged users (`appuser:10001` and `mluser:10002`).
- Base images are built on `python:3.11-slim` to reduce the CVE attack surface.
- Container security scanning is executed during the CI build process using `pip-audit`, `bandit`, and `trivy`.

## Reporting Vulnerabilities
If you discover a potential security vulnerability in this project:
1. Do **not** open a public GitHub issue.
2. Send a private report describing the flaw, steps to reproduce, and potential impact.
3. We will acknowledge receipt within 48 hours and coordinate a fix release.
