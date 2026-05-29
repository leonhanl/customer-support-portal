#!/usr/bin/env bash
# Step 1+2: Port scan and HTTP fingerprinting
# Usage: TARGET=<host:port> ./01-fingerprint.sh
TARGET="${TARGET:-localhost:8080}"

echo "=== [Step 1] TCP scan ==="
if command -v nmap &>/dev/null; then
  nmap -p "${TARGET##*:}" "${TARGET%%:*}"
else
  echo "[!] nmap not found, skipping port scan"
fi

echo ""
echo "=== [Step 2] HTTP fingerprinting ==="
curl -si "http://${TARGET}/" | head -20
