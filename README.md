# Customer Support Portal — Lab Demo

> ⚠ **受控靶场（Lab Demo）**
>
> 本项目是一个专为**安全演示、漏洞验证和 XDR 检测能力展示**设计的靶场应用。
> 所有漏洞利用结果均为受控行为，目的是演示 AI 安全测试工具与 XDR 的能力。
> **禁止部署至生产环境。**

## 项目定位

| 属性 | 说明 |
|---|---|
| 业务场景 | Customer Support Portal — 客户上传日志包、系统分析并生成诊断报告 |
| CVE 1 | **CVE-2024-23334** — aiohttp 3.9.1 `add_static` 目录穿越，可读任意文件 |
| CVE 2 | **CVE-2020-14343** — PyYAML 5.3.1 `yaml.Loader` 不安全反序列化，可 RCE |
| 攻击链 | 读配置 → 读 token → 上传恶意 profile → 触发 yaml.load → 反弹 shell |
| C2 | 受控 TCP listener（`demo_attacker/listener.py`），固定端口 4444 |
| 演示角色 | Strix 等 AI 安全测试工具（发现链）、XDR（检测链） |

## 快速本地运行

> **环境要求：** Python 3.10

```bash
# 1. 激活 venv
source .venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt
pip install -e .

# 3. 启动应用
python -m support_portal
# → http://localhost:8080
```

打开浏览器：
- **`/`** — 客户上传页面
- **`/admin`** — Admin 诊断规则管理

## 目录结构

```
src/support_portal/    应用源码
demo_attacker/               C2 listener + 攻击演示脚本（demo-attacker 部署）
demo_attacker/attack/        攻击演示脚本（12 步 walkthrough）
tests/                 单元 + 端到端测试
```

## 运行测试

```bash
pip install pytest pytest-asyncio
pytest tests/ -v
```

## XDR 检测点

XDR 在主机侧可观察到的行为链：

1. 外部源对 8080 端口扫描 + `/static/../*` 异常路径访问
2. aiohttp 进程读取 `/opt/support-portal/config/*`（正常范围之外）
3. aiohttp 进程读取 `/opt/support-portal/secrets/*`
4. `/internal/admin/profile/upload` 被外部 IP 调用
5. `profiles/active.yaml` 被非预期覆盖
6. Python 进程执行 `yaml.load` 触发 `!!python/object/apply` 反序列化
7. `python` → `bash -i` 子进程 spawn
8. `bash` 进程到 `demo-c2.local:4444` 异常外连
9. 以上事件被关联为单一攻击链

## 安全声明

本项目**不包含**：

- 真实生产凭据或云账号密钥
- 可泛化的攻击工具（payload 固定目的地、固定内容）
- 真实数据库密码
- OS 层提权（LPE）演示
