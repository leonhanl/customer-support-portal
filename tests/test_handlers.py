import os
from pathlib import Path

import pytest
import pytest_asyncio
from aiohttp import FormData

from support_portal.app import create_app


@pytest_asyncio.fixture()
async def client(lab_base: Path, aiohttp_client):
    os.environ["SUPPORT_PORTAL_BASE"] = str(lab_base)
    from support_portal.config import load_config
    cfg = load_config()
    app = await create_app(config=cfg)
    return await aiohttp_client(app)


@pytest.mark.asyncio
async def test_index_page(client):
    resp = await client.get("/")
    assert resp.status == 200
    text = await resp.text()
    assert "Customer Support Portal" in text
    assert "LAB DEMO" in text


@pytest.mark.asyncio
async def test_admin_page(client):
    resp = await client.get("/admin")
    assert resp.status == 200
    text = await resp.text()
    assert "App Owner" in text or "profile" in text.lower()


@pytest.mark.asyncio
async def test_upload_returns_ticket(client, sample_bundle):
    data = FormData()
    data.add_field("bundle", sample_bundle.read_bytes(),
                   filename="bundle.zip", content_type="application/zip")
    resp = await client.post("/support/upload", data=data)
    assert resp.status == 200
    body = await resp.json()
    assert "ticket_id" in body


@pytest.mark.asyncio
async def test_report_page(client, sample_bundle, lab_base):
    data = FormData()
    data.add_field("bundle", sample_bundle.read_bytes(),
                   filename="bundle.zip", content_type="application/zip")
    resp = await client.post("/support/upload", data=data)
    ticket_id = (await resp.json())["ticket_id"]

    resp = await client.get(f"/support/report/{ticket_id}")
    assert resp.status == 200
    text = await resp.text()
    assert ticket_id in text


@pytest.mark.asyncio
async def test_report_json(client, sample_bundle):
    data = FormData()
    data.add_field("bundle", sample_bundle.read_bytes(),
                   filename="bundle.zip", content_type="application/zip")
    resp = await client.post("/support/upload", data=data)
    ticket_id = (await resp.json())["ticket_id"]

    resp = await client.get(f"/support/report/{ticket_id}",
                             headers={"Accept": "application/json"})
    assert resp.status == 200
    body = await resp.json()
    assert body["ticket_id"] == ticket_id


@pytest.mark.asyncio
async def test_profile_upload_wrong_token(client):
    resp = await client.post(
        "/internal/app-owner/profile/upload",
        headers={"Authorization": "Bearer wrong-token"},
        data=b"profile_name: test\n",
    )
    assert resp.status == 401


@pytest.mark.asyncio
async def test_profile_upload_correct_token(client, lab_base):
    resp = await client.post(
        "/internal/app-owner/profile/upload",
        headers={"Authorization": "Bearer test-token-abc"},
        data=b"profile_name: updated\nversion: '2.0'\nrules: []\nreport: {title: T}\n",
    )
    assert resp.status == 200
    body = await resp.json()
    assert body["status"] == "ok"
    content = (lab_base / "profiles" / "active.yaml").read_text()
    assert "updated" in content


@pytest.mark.asyncio
async def test_report_not_found(client):
    resp = await client.get("/support/report/nonexistent")
    assert resp.status == 404
