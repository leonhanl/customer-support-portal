# Customer Support Portal

A lightweight web portal that lets customers upload diagnostic log bundles and
receive an automated analysis report. Support engineers manage the diagnostic
rules that drive the analysis through an admin page.

## 功能特性

- **日志包上传** — 客户上传 `.zip` 日志包，系统自动解析并生成诊断报告
- **诊断报告** — 根据可配置的规则匹配日志内容，输出问题列表与建议处理动作
- **诊断规则管理** — Admin 页面查看与更新当前生效的诊断 profile
- **报告查询** — 通过 ticket ID 以网页或 JSON 形式获取报告

## 技术栈

- Python 3.10
- [aiohttp](https://docs.aiohttp.org/) — 异步 Web 框架
- [aiohttp-jinja2](https://github.com/aio-libs/aiohttp-jinja2) — 模板渲染
- [PyYAML](https://pyyaml.org/) — 配置与诊断 profile 解析

## 快速开始

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
- **`/admin`** — 诊断规则管理

## 路由

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/` | 客户上传页面 |
| GET | `/admin` | 诊断规则管理页面 |
| POST | `/support/upload` | 上传日志包，返回 ticket ID |
| GET | `/support/report/{ticket_id}` | 查询诊断报告（网页 / JSON） |

## 目录结构

```text
src/support_portal/    应用源码
src/support_portal/handlers/    路由处理逻辑
src/support_portal/templates/   Jinja2 模板
data/                  运行时数据（配置、上传、报告、profile）
tests/                 单元 + 端到端测试
```

## 配置

应用配置位于 `data/config/app_config.yaml`。运行时数据根目录默认为仓库内的
`data/`，可通过环境变量 `SUPPORT_PORTAL_BASE` 覆盖。

## 运行测试

```bash
pip install pytest pytest-asyncio
pytest tests/ -v
```
