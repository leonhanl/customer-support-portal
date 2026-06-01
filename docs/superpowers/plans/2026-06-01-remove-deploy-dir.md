# Remove `deploy/` Directory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the `deploy/` directory (install.sh + systemd + VM scaffolding) and relocate the app's runtime data root to a repo-root `data/` dir so users can launch directly with `python -m support_portal`.

**Architecture:** The app reads its data root from `SUPPORT_PORTAL_BASE` env var, defaulting to a hardcoded `/opt/support-portal`. We move the data files (`config`, `secrets`, `profiles`, `static`, `uploads`, `reports`) into `data/` at the repo root, and change the default in `config.py` to derive the repo-root `data/` path from `__file__` (independent of the current working directory). The env var still overrides. No other code changes — the CVE attack chain and tests are unaffected.

**Tech Stack:** Python 3.10+, aiohttp, PyYAML, pytest.

---

### Task 1: Move data root from `deploy/opt/support-portal/` to repo-root `data/`

**Files:**
- Move: `deploy/opt/support-portal/{config,secrets,profiles,static,uploads,reports}` → `data/`
- Delete: `deploy/` (entire directory, including `install.sh`, `systemd/`, `opt/`)

- [ ] **Step 1: Move the data directories with git**

```bash
git mv deploy/opt/support-portal data
git rm -r deploy
```

Note: `git mv deploy/opt/support-portal data` moves the directory to a new top-level `data/`. After this, `deploy/opt/` is empty and `git rm -r deploy` removes the remaining `install.sh` and `systemd/` files plus the now-empty dirs.

- [ ] **Step 2: Verify the new layout**

Run: `ls -R data && echo "---" && ls deploy 2>&1`
Expected: `data/` contains `config/ secrets/ profiles/ static/ uploads/ reports/` with all original files (app_config.yaml, profile-upload-token, active.yaml, index.html, the two upload zips, 0d1c9d10.json). `ls deploy` reports "No such file or directory".

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "Move runtime data root from deploy/opt/support-portal to data/"
```

---

### Task 2: Default `base_dir` to repo-root `data/` in config.py

**Files:**
- Modify: `src/support_portal/config.py:8`

The app file lives at `src/support_portal/config.py`, so the repo root is `Path(__file__).resolve().parents[2]` (config.py → support_portal → src → repo root). The data root is that path `/ "data"`. This is derived from `__file__`, NOT the current working directory, so `python -m support_portal` works from any directory.

- [ ] **Step 1: Edit the default base_dir**

Change line 8 from:

```python
    base_dir = Path(os.environ.get("SUPPORT_PORTAL_BASE", "/opt/support-portal"))
```

to:

```python
    default_base = Path(__file__).resolve().parents[2] / "data"
    base_dir = Path(os.environ.get("SUPPORT_PORTAL_BASE", default_base))
```

- [ ] **Step 2: Verify config loads with the new default (no env var)**

Run: `unset SUPPORT_PORTAL_BASE; python -c "from support_portal.config import load_config; c = load_config(); print(c['base_dir']); print(c['secrets']['profile_upload_token_value'])"`
Expected: prints a path ending in `/customer-support-portal/data` and the token string (`demo-profile-admin-token-2026` or whatever is in `data/secrets/profile-upload-token`). No FileNotFoundError.

- [ ] **Step 3: Verify it still works from a different working directory**

Run: `cd /tmp && unset SUPPORT_PORTAL_BASE; python -c "from support_portal.config import load_config; print(load_config()['base_dir'])"; cd -`
Expected: still prints the repo's `.../data` path (proves it does not depend on cwd). Note: requires `pip install -e .` so the package is importable from `/tmp`.

- [ ] **Step 4: Commit**

```bash
git add src/support_portal/config.py
git commit -m "Default base_dir to repo-root data/ instead of /opt/support-portal"
```

---

### Task 3: Fix the token path in app_config.yaml

**Files:**
- Modify: `data/config/app_config.yaml`

The `secrets.profile_upload_token_file` field hardcodes `/opt/support-portal/secrets/...`. This field is NOT read by the code (config.py reads the token via `base_dir / "secrets" / "profile-upload-token"`), but the stale absolute path is misleading. Update it to a relative `data/`-based path for documentation accuracy.

- [ ] **Step 1: Edit the token path**

In `data/config/app_config.yaml`, change:

```yaml
secrets:
  profile_upload_token_file: "/opt/support-portal/secrets/profile-upload-token"
```

to:

```yaml
secrets:
  profile_upload_token_file: "data/secrets/profile-upload-token"
```

- [ ] **Step 2: Verify config still loads**

Run: `unset SUPPORT_PORTAL_BASE; python -c "from support_portal.config import load_config; print(load_config()['secrets']['profile_upload_token_value'])"`
Expected: prints the token string, no error (confirms the YAML is still valid and the field change is harmless).

- [ ] **Step 3: Commit**

```bash
git add data/config/app_config.yaml
git commit -m "Update token path in app_config.yaml to data/ location"
```

---

### Task 4: Update README

**Files:**
- Modify: `README.md` (lines 30-31, 46, 52-67)

Three edits: remove the `SUPPORT_PORTAL_BASE` export step from quickstart, remove the `deploy/` line from the directory tree, and delete the entire "完整 VM 部署" section.

- [ ] **Step 1: Remove the SUPPORT_PORTAL_BASE export step**

In the "快速本地运行" code block, remove these two lines (currently lines 30-31) and the blank line after step 2's renumbering. Change:

```bash
# 2. 安装依赖
pip install -r requirements.txt
pip install -e .

# 3. 准备本地 demo 文件目录
export SUPPORT_PORTAL_BASE="$(pwd)/deploy/opt/support-portal"

# 4. 启动应用
python -m support_portal
# → http://localhost:8080
```

to:

```bash
# 2. 安装依赖
pip install -r requirements.txt
pip install -e .

# 3. 启动应用
python -m support_portal
# → http://localhost:8080
```

- [ ] **Step 2: Remove the deploy/ line from the directory tree**

In the "目录结构" block, delete this line:

```
deploy/                Linux VM 部署文件（systemd + install.sh）
```

- [ ] **Step 3: Delete the "完整 VM 部署" section**

Remove the entire block from the `## 完整 VM 部署` heading through the end of the VM-2 sub-section, i.e. delete these lines:

````
## 完整 VM 部署

### VM-1（support-portal）

```bash
# 需要 root
sudo bash deploy/install.sh
sudo systemctl start support-portal
```

### VM-2（demo-c2）

```bash
# 确保 demo-c2.local 在 VM-1 的 /etc/hosts 中指向 VM-2
python3 demo_c2/listener.py
```
````

Note: keep the `## 运行测试` section and everything after it intact. The demo-c2 listener launch instruction (`python3 demo_c2/listener.py`) is now only documented in the attack walkthrough; that is acceptable per scope (attack/ docs untouched).

- [ ] **Step 4: Verify no stale deploy references remain in README**

Run: `grep -n "deploy\|SUPPORT_PORTAL_BASE\|完整 VM\|install.sh" README.md`
Expected: no output (all references removed).

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "Update README: remove VM deploy section and SUPPORT_PORTAL_BASE step"
```

---

### Task 5: Full verification

**Files:** none (verification only)

- [ ] **Step 1: Run the test suite**

Run: `pytest tests/ -v`
Expected: all tests PASS. Tests use `tmp_path`-based `lab_base` and set `SUPPORT_PORTAL_BASE` themselves, so they are independent of the data root move.

- [ ] **Step 2: Smoke-test the app starts and serves**

Run:
```bash
unset SUPPORT_PORTAL_BASE
python -m support_portal &
SERVER_PID=$!
sleep 2
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/admin
kill $SERVER_PID
```
Expected: both curls print `200`. The startup log shows `[support-portal] listening on http://0.0.0.0:8080`.

- [ ] **Step 3: Confirm deploy/ is gone and data/ is present**

Run: `ls deploy 2>&1; ls data/config data/secrets`
Expected: `ls deploy` → "No such file or directory"; `data/config` shows `app_config.yaml`; `data/secrets` shows `profile-upload-token`.
