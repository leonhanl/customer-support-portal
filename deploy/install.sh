#!/usr/bin/env bash
# Deploy support-portal to /opt/support-portal on a Linux VM.
# Must be run as root.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
INSTALL_BASE="/opt/support-portal"
SERVICE_USER="support-portal"

echo "[install] Creating system user..."
id "$SERVICE_USER" &>/dev/null || useradd --system --no-create-home --shell /sbin/nologin "$SERVICE_USER"

echo "[install] Creating directories..."
mkdir -p "$INSTALL_BASE"/{config,secrets,profiles,static,uploads,reports,venv}

echo "[install] Copying config/secrets/profiles/static..."
rsync -a "$REPO_DIR/deploy/opt/support-portal/config/"   "$INSTALL_BASE/config/"
rsync -a "$REPO_DIR/deploy/opt/support-portal/secrets/"  "$INSTALL_BASE/secrets/"
rsync -a "$REPO_DIR/deploy/opt/support-portal/profiles/" "$INSTALL_BASE/profiles/"
rsync -a "$REPO_DIR/deploy/opt/support-portal/static/"   "$INSTALL_BASE/static/"

echo "[install] Setting permissions..."
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_BASE"
chmod 700 "$INSTALL_BASE/secrets"
chmod 600 "$INSTALL_BASE/secrets/profile-upload-token"

echo "[install] Installing Python venv..."
python3 -m venv "$INSTALL_BASE/venv"
"$INSTALL_BASE/venv/bin/pip" install --quiet --upgrade pip
"$INSTALL_BASE/venv/bin/pip" install --quiet -r "$REPO_DIR/requirements.txt"
"$INSTALL_BASE/venv/bin/pip" install --quiet -e "$REPO_DIR"

echo "[install] Installing systemd service..."
cp "$REPO_DIR/deploy/systemd/support-portal.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable support-portal

echo "[install] Done. Run: systemctl start support-portal"
