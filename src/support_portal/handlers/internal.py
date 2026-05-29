from pathlib import Path

from aiohttp import web


async def upload_profile(request: web.Request) -> web.Response:
    cfg = request.app["config"]
    expected_token = cfg["secrets"]["profile_upload_token_value"]

    auth = request.headers.get("Authorization", "")
    if auth != f"Bearer {expected_token}":
        return web.Response(status=401, text="Unauthorized")

    body = await request.read()
    if not body:
        raise web.HTTPBadRequest(text="Empty body")

    profile_path = cfg["base_dir"] / "profiles" / "active.yaml"
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_bytes(body)

    return web.json_response({"status": "ok", "message": "Profile updated."})
