# 移除 `deploy/`，改为命令行直接启动

日期：2026-06-01

## 背景

`customer-support-portal` 是一个受控安全靶场（lab demo）。当前通过
`deploy/install.sh` + `deploy/systemd/support-portal.service` 部署到 Linux VM 的
`/opt/support-portal`。这套部署机制对使用者来说过于复杂。

此外，`deploy/opt/support-portal/` 不只是部署脚手架，它同时是应用的**运行时数据根目录**
（config / secrets / profiles / static，以及运行时写入的 uploads / reports）。即便本地开发，
当前也要求把 `SUPPORT_PORTAL_BASE` 指向 `deploy/opt/support-portal`。

## 目标

让用户在自己的 server 上 clone 仓库后，直接命令行启动，无需 root、无需 install.sh、无需 systemd。

## 方案

### 1. 数据根目录迁移到仓库根的 `data/`

将 `deploy/opt/support-portal/` 下内容移到 `data/`：

```
data/
  config/app_config.yaml
  secrets/profile-upload-token
  profiles/active.yaml
  static/index.html
  uploads/      # 运行时写入，保留现有样例 zip
  reports/      # 运行时写入，保留现有 0d1c9d10.json
```

`deploy/` 整个目录删除（install.sh、systemd、opt/）。

### 2. 代码改动（仅 config.py）

[src/support_portal/config.py](../../../src/support_portal/config.py) 第 8 行：
默认 base 从绝对路径 `/opt/support-portal` 改为仓库内的 `data/`，**相对包/脚本定位**
（例如基于 `__file__` 向上推导仓库根再拼 `data`），而非依赖当前工作目录 —— 这样在任意目录
执行 `python -m support_portal` 都能找到数据根。`SUPPORT_PORTAL_BASE` 环境变量仍可覆盖默认值。

启动入口 `python -m support_portal` 保持不变。

### 3. 配置修正

`app_config.yaml` 中 `secrets.profile_upload_token_file` 当前硬编码
`/opt/support-portal/secrets/...`。该字段实际未被代码读取（config.py 用 `base_dir/secrets/...`
读取 token），但为避免误导，更新为指向 `data/secrets/...` 的路径。

### 4. README 更新

- 删除「完整 VM 部署」整节（VM-1 install.sh / systemd）。
- 简化「快速本地运行」：去掉 `export SUPPORT_PORTAL_BASE=...` 步骤（默认即 `data/`）。
- 目录结构表删除 `deploy/` 行。

### 5. 明确不改动

- `attack/` 脚本及其注释 —— 属于攻击演示叙事，保留。
- `tests/` —— 测试用 `tmp_path` 构造独立的 `lab_base`，已独立于 `deploy/`，无需改动。
- 两个 CVE 漏洞链（CVE-2024-23334 路径穿越、CVE-2020-14343 yaml RCE）行为完全不变。
  本项目仍是受控靶场。

## 验证

- `python -m support_portal` 从仓库根启动，`/` 与 `/admin` 正常。
- `pytest tests/ -v` 全部通过（不依赖 deploy）。
- `data/` 中样例 reports/uploads 仍在。
