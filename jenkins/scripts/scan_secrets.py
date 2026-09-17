#!/usr/bin/env python3
import os
import re
import sys

# High confidence secret detection patterns
SECRET_PATTERNS = [
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS Access Key ID"),
    (re.compile(r"(?i)aws_secret_access_key\s*=\s*['\"][A-Za-z0-9/\+=]{40}['\"]"), "AWS Secret Access Key"),
    (re.compile(r"-----BEGIN (RSA|EC|DSA|OPENSSH|PRIVATE) KEY-----"), "Private Key Header"),
    (re.compile(r"ghp_[A-Za-z0-9]{36}"), "GitHub Personal Access Token"),
    (re.compile(r"eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*"), "JWT Token"),
]

EXCLUDE_DIRS = {".git", ".venv", "__pycache__", "node_modules", ".pytest_cache"}
EXCLUDE_FILES = {"SECURITY.md", "scan_secrets.py"}


def scan_directory(root_dir):
    findings = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for filename in filenames:
            if filename in EXCLUDE_FILES:
                continue
            filepath = os.path.join(dirpath, filename)
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    for line_idx, line in enumerate(f, 1):
                        for pattern, label in SECRET_PATTERNS:
                            if pattern.search(line):
                                findings.append((filepath, line_idx, label, line.strip()))
            except Exception as err:
                print(f"Skipping file {filepath}: {err}")
    return findings


if __name__ == "__main__":
    target = os.getcwd()
    print(f"Scanning repository for sensitive secrets in: {target}")
    findings = scan_directory(target)
    if findings:
        print("\n[CRITICAL ERROR] Exposed hardcoded secret(s) found!")
        for file, line, label, content in findings:
            print(f"  - {file}:{line} [{label}] -> {content[:60]}")
        sys.exit(1)
    else:
        print("\n[SUCCESS] Zero hardcoded secrets detected across all files!")
        sys.exit(0)
