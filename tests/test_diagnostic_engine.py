import json
from pathlib import Path

import pytest
import yaml

from support_portal.diagnostic_engine import analyze, load_active_profile


def test_load_benign_profile(lab_base: Path):
    profile_path = lab_base / "profiles" / "active.yaml"
    profile = load_active_profile(profile_path)
    assert profile["profile_name"] == "Test Profile"
    assert len(profile["rules"]) == 1


def test_analyze_matches_rule(lab_base: Path, sample_bundle: Path):
    ticket_id = analyze(sample_bundle, lab_base / "profiles" / "active.yaml", lab_base / "reports")
    report_path = lab_base / "reports" / f"{ticket_id}.json"
    assert report_path.exists()
    report = json.loads(report_path.read_text())
    assert report["ticket_id"] == ticket_id
    assert len(report["matched_rules"]) == 1
    assert report["matched_rules"][0]["id"] == "T-001"
    assert len(report["recommended_actions"]) > 0


def test_analyze_no_match(lab_base: Path, tmp_path: Path):
    import zipfile
    bundle = tmp_path / "quiet.zip"
    with zipfile.ZipFile(bundle, "w") as zf:
        zf.writestr("agent.log", "all good\n")
    ticket_id = analyze(bundle, lab_base / "profiles" / "active.yaml", lab_base / "reports")
    report = json.loads((lab_base / "reports" / f"{ticket_id}.json").read_text())
    assert report["matched_rules"] == []
    assert report["recommended_actions"] == []


def test_analyze_missing_log_file(lab_base: Path, tmp_path: Path):
    import zipfile
    bundle = tmp_path / "empty.zip"
    with zipfile.ZipFile(bundle, "w") as zf:
        zf.writestr("other.log", "irrelevant\n")
    ticket_id = analyze(bundle, lab_base / "profiles" / "active.yaml", lab_base / "reports")
    report = json.loads((lab_base / "reports" / f"{ticket_id}.json").read_text())
    assert report["matched_rules"] == []
