#!/usr/bin/env bash
# Creates benign-bundle.zip containing sample log files for the demo.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TMP=$(mktemp -d)

cat > "$TMP/agent.log" <<'LOG'
2026-05-29 10:01:00 INFO  Agent started successfully
2026-05-29 10:02:15 ERROR connection refused to management.example.com:443
2026-05-29 10:05:00 WARN  token expired, attempting refresh
2026-05-29 10:05:01 INFO  Token refreshed successfully
LOG

cat > "$TMP/system.log" <<'LOG'
2026-05-29 10:00:01 kernel: EXT4-fs: mounted filesystem
2026-05-29 10:03:44 kernel: No space left on device
2026-05-29 10:04:00 systemd: Started support-portal.service
LOG

(cd "$TMP" && zip -q benign-bundle.zip agent.log system.log)
cp "$TMP/benign-bundle.zip" "$SCRIPT_DIR/benign-bundle.zip"
rm -rf "$TMP"
echo "[*] benign-bundle.zip created."
