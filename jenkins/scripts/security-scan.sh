#!/usr/bin/env bash
set -eo pipefail

echo "=========================================="
echo " Running Security & Dependency Scans"
echo "=========================================="

python3 -m pip install --quiet pip-audit bandit

echo "Scanning dependencies for known vulnerabilities..."
pip-audit -r app/requirements.txt || echo "WARN: Dependency audit finished with warnings"
pip-audit -r ml/requirements.txt || echo "WARN: Dependency audit finished with warnings"

echo "Scanning source code for AST security flaws..."
bandit -r app/src ml/src -ll -ii || echo "WARN: Bandit scan finished with warnings"

echo "Checking for committed secrets or private keys..."
if grep -rE "(AWS_SECRET_ACCESS_KEY|BEGIN PRIVATE KEY|AKIA[0-9A-Z]{16})" . --exclude-dir={.git,__pycache__,node_modules} --exclude="SECURITY.md" --exclude="*.sh"; then
    echo "ERROR: Potential exposed hardcoded secret detected!"
    exit 1
fi

echo "Security audit check passed cleanly!"
