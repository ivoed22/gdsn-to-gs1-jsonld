import csv
import json
from pathlib import Path

from typer.testing import CliRunner

from gdsn_to_gs1_jsonld.catalog_quality import check_mapping
from gdsn_to_gs1_jsonld.cli import app
from gdsn_to_gs1_jsonld.standards_backlog import (
    CSV_COLUMNS,
    VALID_DECISION_STATUSES,
)

ROOT = Path(__file__).resolve().parents[1]
DECISIONS = ROOT / "docs" / "standards-decisions"
runner = CliRunner()


def test_committed_standards_backlog_is_valid():
    backlog = json.loads(
        (DECISIONS / "standards_review_backlog.json").read_text(
            encoding="utf-8"
        )
    )

    assert len(backlog) == 6
    assert len({item["id"] for item in backlog}) == len(backlog)
    assert sum(item["warning_count"] for item in backlog) == 12
    assert all(item["status"] in VALID_DECISION_STATUSES for item in backlog)
    assert all(item["blocks_release"] is False for item in backlog)
    assert all(item["standards_review_required"] is True for item in backlog)
    assert all((DECISIONS / item["decision_file"]).is_file() for item in backlog)
    for item in backlog:
        decision = (DECISIONS / item["decision_file"]).read_text(encoding="utf-8")
        for heading in (
            "## Status",
            "## Summary",
            "## Affected mappings",
            "## Current behaviour",
            "## Why this needs review",
            "## Options",
            "## Recommended direction",
            "## Decision needed from",
            "## Follow-up actions",
            "## Links",
        ):
            assert heading in decision


def test_backlog_covers_every_current_mapping_warning_once():
    backlog = json.loads(
        (DECISIONS / "standards_review_backlog.json").read_text(
            encoding="utf-8"
        )
    )
    report = check_mapping(
        ROOT / "mapping" / "mapping_v0_3.yaml",
        ROOT
        / "mapping_catalog"
        / "gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_3_webvoc_validated.csv",
    )
    warning_fields = [
        item["affected_field_property"] for item in report["warnings"]
    ]
    backlog_fields = [
        field
        for decision in backlog
        for field in decision["affected_fields"]
    ]

    assert len(warning_fields) == 12
    assert sorted(backlog_fields) == sorted(warning_fields)


def test_committed_standards_backlog_csv_has_expected_columns():
    with (DECISIONS / "standards_review_backlog.csv").open(
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    assert tuple(reader.fieldnames or ()) == CSV_COLUMNS
    assert len(rows) == 6


def test_export_standards_backlog_cli_is_offline_and_preserves_sdr(
    tmp_path,
):
    decision = tmp_path / "SDR-001-nutrient-modelling.md"
    decision.write_text("human-maintained", encoding="utf-8")
    result = runner.invoke(
        app,
        [
            "export-standards-backlog",
            "--warning-review",
            "docs/warning-cleanup-v0.6.1.md",
            "--output",
            str(tmp_path),
            "--format",
            "all",
            "--overwrite",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "6 open topic(s), 12 warning(s)" in result.output
    assert (tmp_path / "standards_review_backlog.json").is_file()
    assert (tmp_path / "standards_review_backlog.csv").is_file()
    assert decision.read_text(encoding="utf-8") == "human-maintained"
