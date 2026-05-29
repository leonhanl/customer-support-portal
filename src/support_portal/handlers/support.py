import tempfile
import uuid
from pathlib import Path

from aiohttp import web

from ..diagnostic_engine import analyze


async def upload_bundle(request: web.Request) -> web.Response:
    cfg = request.app["config"]
    base_dir = cfg["base_dir"]
    uploads_dir = base_dir / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    reader = await request.multipart()
    field = await reader.next()

    if field is None or field.name != "bundle":
        raise web.HTTPBadRequest(text="Missing 'bundle' field")

    filename = f"{uuid.uuid4()}.zip"
    zip_path = uploads_dir / filename
    with open(zip_path, "wb") as f:
        while True:
            chunk = await field.read_chunk()
            if not chunk:
                break
            f.write(chunk)

    profile_path = base_dir / "profiles" / "active.yaml"
    reports_dir = base_dir / "reports"

    ticket_id = analyze(zip_path, profile_path, reports_dir)
    return web.json_response({"ticket_id": ticket_id})
