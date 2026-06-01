from pathlib import Path

import aiohttp_jinja2
import jinja2
from aiohttp import web

from .config import load_config
from .handlers.internal import upload_profile
from .handlers.pages import admin, index, report_html
from .handlers.support import upload_bundle


async def create_app(config: dict | None = None) -> web.Application:
    app = web.Application()

    if config is None:
        config = load_config()
    app["config"] = config

    templates_dir = Path(__file__).parent / "templates"
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(str(templates_dir)))

    app.router.add_get("/", index)
    app.router.add_get("/admin", admin)
    app.router.add_get("/support/report/{ticket_id}", report_html)
    app.router.add_post("/support/upload", upload_bundle)
    app.router.add_post("/internal/admin/profile/upload", upload_profile)

    static_dir = str(config["base_dir"] / "static")
    # CVE-2024-23334: aiohttp < 3.9.2 with follow_symlinks=True skips the
    # filepath.relative_to(directory) boundary check in StaticResource._handle,
    # allowing path traversal via GET /static/../../sensitive/file.
    app.router.add_static("/static/", static_dir, follow_symlinks=True)

    return app
