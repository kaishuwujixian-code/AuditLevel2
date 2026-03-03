from __future__ import annotations

from core.project_store import report_filename_prefix_for_profile


def test_audit_report_prefix_for_level1() -> None:
    assert report_filename_prefix_for_profile("level1") == "Level 1 energy audit"


def test_audit_report_prefix_for_level2() -> None:
    assert report_filename_prefix_for_profile("level2") == "Level 2 energy audit"


def test_audit_report_prefix_defaults_to_level1() -> None:
    assert report_filename_prefix_for_profile("unknown") == "Level 1 energy audit"
