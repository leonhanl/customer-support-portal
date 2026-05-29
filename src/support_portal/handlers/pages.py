import json

import aiohttp_jinja2
from aiohttp import web


@aiohttp_jinja2.template("index.html")
async def index(request: web.Request) -> dict:
    return {}


@aiohttp_jinja2.template("admin.html")
async def admin(request: web.Request) -> dict:
    cfg = request.app["config"]
    profile_path = cfg["base_dir"] / "profiles" / "active.yaml"
    profile_content = profile_path.read_text() if profile_path.exists() else ""
    return {"profile_content": profile_content}


@aiohttp_jinja2.template("report.html")
async def report_html(request: web.Request) -> dict:
    ticket_id = request.match_info["ticket_id"]
    cfg = request.app["config"]
    report_path = cfg["base_dir"] / "reports" / f"{ticket_id}.json"

    if not report_path.exists():
        raise web.HTTPNotFound(text=f"Ticket {ticket_id} not found")

    report_data = json.loads(report_path.read_text())

    accept = request.headers.get("Accept", "")
    if "application/json" in accept:
        raise web.HTTPOk(
            text=json.dumps(report_data),
            content_type="application/json",
        )

    return {"report": report_data, "ticket_id": ticket_id}
