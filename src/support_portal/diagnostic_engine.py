import json
import tempfile
import uuid
import zipfile
from pathlib import Path

import yaml


def load_active_profile(profile_path: Path) -> dict:
    with open(profile_path) as f:
        # CVE-2020-14343: yaml.Loader is the "unsafe" loader that allows
        # arbitrary Python object deserialization via !!python/object/apply tags.
        return yaml.load(f, Loader=yaml.Loader)


def analyze(zip_path: Path, profile_path: Path, reports_dir: Path) -> str:
    profile = load_active_profile(profile_path)

    ticket_id = str(uuid.uuid4())[:8]
    matched_rules = []

    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(tmp)

        rules = profile.get("rules", [])
        log_contents: dict[str, str] = {}

        for rule in rules:
            match = rule.get("match", {})
            log_file = match.get("file", "")
            keyword = match.get("contains", "")
            if not log_file or not keyword:
                continue

            if log_file not in log_contents:
                candidate = Path(tmp) / log_file
                log_contents[log_file] = candidate.read_text(errors="replace") if candidate.exists() else ""

            if keyword in log_contents[log_file]:
                matched_rules.append({
                    "id": rule.get("id"),
                    "description": rule.get("description"),
                    "severity": rule.get("severity"),
                })

    report_cfg = profile.get("report", {})
    report = {
        "ticket_id": ticket_id,
        "profile_name": profile.get("profile_name", "unknown"),
        "title": report_cfg.get("title", "Diagnostic Report"),
        "matched_rules": matched_rules,
        "summary": f"Found {len(matched_rules)} issue(s).",
        "recommended_actions": _build_recommendations(matched_rules),
    }

    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / f"{ticket_id}.json").write_text(json.dumps(report, indent=2))
    return ticket_id


def _build_recommendations(matched_rules: list) -> list[str]:
    severity_actions = {
        "high": "Escalate immediately to on-call engineer.",
        "medium": "Review and remediate within 24 hours.",
        "low": "Schedule for next maintenance window.",
    }
    seen = set()
    actions = []
    for rule in matched_rules:
        sev = (rule.get("severity") or "low").lower()
        action = severity_actions.get(sev, "Review and remediate.")
        if action not in seen:
            seen.add(action)
            actions.append(action)
    return actions
