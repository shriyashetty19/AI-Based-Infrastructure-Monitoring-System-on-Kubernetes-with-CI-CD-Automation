#!/usr/bin/env bash
set -eo pipefail

echo "=========================================="
echo " Running Unit & Integration Tests"
echo "=========================================="

export PYTHONPATH=".:app:ml"

echo "Running App Tests..."
pytest app/tests/ -v --cov=app/src --cov-report=term-missing

echo "Running ML Detector Tests..."
pytest ml/tests/ -v --cov=ml/src --cov-report=term-missing

echo "All tests passed successfully!"
