import os
import shutil
import tempfile
import zipfile
from pathlib import Path

import pytest
import yaml


@pytest.fixture()
def lab_base(tmp_path: Path) -> Path:
    """Create a minimal /opt/support-portal-like directory tree for testing."""
    base = tmp_path / "support-portal"
    for d in ("config", "secrets", "profiles", "static", "uploads", "reports"):
        (base / d).mkdir(parents=True)

    # app_config.yaml
    config = {
        "app": {"name": "Customer Support Portal", "mode": "demo"},
        "public_routes": {"support_bundle_upload": "/support/upload"},
        "internal_routes": {"diagnostic_profile_upload": "/internal/admin/profile/upload"},
        "secrets": {"profile_upload_token_file": str(base / "secrets" / "profile-upload-token")},
    }
    (base / "config" / "app_config.yaml").write_text(yaml.dump(config))

    # token
    (base / "secrets" / "profile-upload-token").write_text("test-token-abc\n")

    # benign active profile
    profile = {
        "profile_name": "Test Profile",
        "version": "1.0",
        "rules": [
            {"id": "T-001", "description": "Test error", "severity": "high",
             "match": {"file": "agent.log", "contains": "test error"}},
        ],
        "report": {"title": "Test Report"},
    }
    (base / "profiles" / "active.yaml").write_text(yaml.dump(profile))

    return base


@pytest.fixture()
def sample_bundle(tmp_path: Path) -> Path:
    bundle_path = tmp_path / "bundle.zip"
    with zipfile.ZipFile(bundle_path, "w") as zf:
        zf.writestr("agent.log", "2026-01-01 INFO test error in agent\n")
        zf.writestr("system.log", "2026-01-01 INFO system ok\n")
    return bundle_path


@pytest.fixture()
def app_config(lab_base: Path) -> dict:
    from support_portal.config import load_config
    os.environ["SUPPORT_PORTAL_BASE"] = str(lab_base)
    cfg = load_config()
    return cfg
