#!/usr/bin/env bash
set -eo pipefail

echo "=========================================="
echo " Running Code Linting & Syntax Checks"
echo "=========================================="

python3 -m pip install --quiet flake8 black

echo "Linting Demo App..."
flake8 app/src app/tests --max-line-length=120 --ignore=E203,W503

echo "Linting ML Anomaly Detector..."
flake8 ml/src ml/tests --max-line-length=120 --ignore=E203,W503

echo "Checking formatting with Black..."
black --check app/src ml/src

echo "Linting completed successfully!"
