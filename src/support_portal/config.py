import os
from pathlib import Path

import yaml


def load_config() -> dict:
    base_dir = Path(os.environ.get("SUPPORT_PORTAL_BASE", "/opt/support-portal"))
    config_path = base_dir / "config" / "app_config.yaml"
    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    token_file = base_dir / "secrets" / "profile-upload-token"
    cfg.setdefault("secrets", {})
    cfg["secrets"]["profile_upload_token_value"] = token_file.read_text().strip()

    cfg["base_dir"] = base_dir
    return cfg
