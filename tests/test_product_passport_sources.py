"""Tests for product_passport_sources module (v0.12.0 Product Passport Bridge).

All tests are deterministic and offline. No network access is performed.
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from unittest import mock

import tempfile

import pytest

ROOT = Path(__file__).resolve().parents[1]

# Use a dedicated temp directory that avoids Windows permission issues
# with pytest's default temp path location.
_TEST_TMPDIR = Path(tempfile.gettempdir()) / "gdsn_pp_tests"
MANIFEST_PATH = ROOT / "product_passport" / "reference_sources" / "source_manifest.json"
EXAMPLE_PATH = ROOT / "product_passport" / "examples" / "minimal_product_passport.json"
SCHEMA_PATH = (
    ROOT
    / "product_passport"
    / "reference_sources"
    / "raw_public"
    / "schemas"
    / "dpp_minimal.schema.json"
)


@pytest.fixture
def valid_manifest() -> dict:
    return {
        "schema_version": "1.0",
        "sources": [
            {
                "source_id": "test_source_a",
                "title": "Test Source A",
                "source_url": "PLACEHOLDER",
                "source_type": "json_schema",
                "version": "1.0",
                "sector": "core",
                "local_path": "product_passport/examples/minimal_product_passport.json",
                "sha256": "PLACEHOLDER_SHA256_AFTER_DOWNLOAD",
                "retrieved_at": "2026-06-30",
                "public_accessible": True,
                "license_or_rights_note": "Test license note",
                "proof_of_concept_note": "Test POC note",
                "usage_note": "Test usage note",
                "used_by": ["test"],
                "normalized_output": None,
            }
        ],
    }


@pytest.fixture
def minimal_instance() -> dict:
    return {
        "@context": "https://gs1.org/voc/",
        "@type": "gs1:Product",
        "gs1:gtin": "09521234543213",
    }


@pytest.fixture
def minimal_schema() -> dict:
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["@context", "@type"],
        "properties": {
            "@context": {"oneOf": [{"type": "string"}, {"type": "array"}, {"type": "object"}]},
            "@type": {"oneOf": [{"type": "string"}, {"type": "array"}]},
        },
        "additionalProperties": True,
    }


# ---------------------------------------------------------------------------
# test_load_manifest_returns_dict
# ---------------------------------------------------------------------------

def test_load_manifest_returns_dict():
    from gdsn_to_gs1_jsonld.product_passport_sources import (
        load_product_passport_source_manifest,
    )
    result = load_product_passport_source_manifest(str(MANIFEST_PATH))
    assert isinstance(result, dict)
    assert "sources" in result
    assert isinstance(result["sources"], list)


# ---------------------------------------------------------------------------
# test_validate_manifest_no_errors_for_valid_manifest
# ---------------------------------------------------------------------------

def test_validate_manifest_no_errors_for_valid_manifest(valid_manifest):
    from gdsn_to_gs1_jsonld.product_passport_sources import (
        validate_product_passport_source_manifest,
    )
    errors = validate_product_passport_source_manifest(valid_manifest)
    assert errors == [], f"Expected no errors, got: {errors}"


def test_validate_manifest_detects_missing_source_id():
    from gdsn_to_gs1_jsonld.product_passport_sources import (
        validate_product_passport_source_manifest,
    )
    manifest = {
        "schema_version": "1.0",
        "sources": [
            {
                # source_id is missing
                "title": "Missing source_id",
                "source_url": "PLACEHOLDER",
                "source_type": "context",
                "sector": "core",
                "local_path": "some/path",
            }
        ],
    }
    errors = validate_product_passport_source_manifest(manifest)
    assert any("source_id" in e for e in errors)


def test_validate_manifest_detects_invalid_source_type():
    from gdsn_to_gs1_jsonld.product_passport_sources import (
        validate_product_passport_source_manifest,
    )
    manifest = {
        "schema_version": "1.0",
        "sources": [
            {
                "source_id": "bad_type_source",
                "title": "Bad source type",
                "source_url": "PLACEHOLDER",
                "source_type": "unknown_type_xyz",
                "sector": "core",
                "local_path": "some/path",
            }
        ],
    }
    errors = validate_product_passport_source_manifest(manifest)
    assert any("source_type" in e.lower() or "unknown_type_xyz" in e for e in errors)


# ---------------------------------------------------------------------------
# test_sha256_file_deterministic
# ---------------------------------------------------------------------------

def test_sha256_file_deterministic():
    from gdsn_to_gs1_jsonld.product_passport_sources import sha256_file
    tmp_dir = _TEST_TMPDIR / "sha256_test"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    test_file = tmp_dir / "test.txt"
    test_file.write_bytes(b"hello world")
    try:
        h1 = sha256_file(str(test_file))
        h2 = sha256_file(str(test_file))
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex digest is 64 chars
    finally:
        test_file.unlink(missing_ok=True)


def test_sha256_file_raises_for_missing_file():
    from gdsn_to_gs1_jsonld.product_passport_sources import sha256_file
    with pytest.raises(FileNotFoundError):
        sha256_file(str(_TEST_TMPDIR / "definitely_nonexistent_file_xyzxyz.txt"))


# ---------------------------------------------------------------------------
# test_build_inventory_counts_sources_by_type
# ---------------------------------------------------------------------------

def test_build_inventory_counts_sources_by_type(valid_manifest):
    from gdsn_to_gs1_jsonld.product_passport_sources import (
        build_product_passport_source_inventory,
    )
    inventory = build_product_passport_source_inventory(valid_manifest, base_dir=str(ROOT))
    assert "sources_by_type" in inventory
    assert "json_schema" in inventory["sources_by_type"]
    assert inventory["sources_by_type"]["json_schema"] == 1


# ---------------------------------------------------------------------------
# test_build_inventory_counts_sources_by_sector
# ---------------------------------------------------------------------------

def test_build_inventory_counts_sources_by_sector(valid_manifest):
    from gdsn_to_gs1_jsonld.product_passport_sources import (
        build_product_passport_source_inventory,
    )
    inventory = build_product_passport_source_inventory(valid_manifest, base_dir=str(ROOT))
    assert "sources_by_sector" in inventory
    assert "core" in inventory["sources_by_sector"]


# ---------------------------------------------------------------------------
# test_missing_local_file_warning_in_inventory
# ---------------------------------------------------------------------------

def test_missing_local_file_warning_in_inventory():
    from gdsn_to_gs1_jsonld.product_passport_sources import (
        build_product_passport_source_inventory,
    )
    manifest = {
        "sources": [
            {
                "source_id": "missing_file_source",
                "title": "Missing File",
                "source_url": "PLACEHOLDER",
                "source_type": "context",
                "sector": "core",
                "local_path": "nonexistent/path/file.json",
                "sha256": None,
            }
        ]
    }
    inventory = build_product_passport_source_inventory(manifest, base_dir=str(ROOT))
    assert "missing_file_source" in inventory["missing_local_files"]


# ---------------------------------------------------------------------------
# test_json_report_is_valid_json
# ---------------------------------------------------------------------------

def test_json_report_is_valid_json(valid_manifest):
    from gdsn_to_gs1_jsonld.product_passport_sources import (
        build_product_passport_source_inventory,
        inventory_report_bytes_json,
    )
    inventory = build_product_passport_source_inventory(valid_manifest, base_dir=str(ROOT))
    report_bytes = inventory_report_bytes_json(inventory)
    parsed = json.loads(report_bytes.decode("utf-8"))
    assert isinstance(parsed, dict)
    assert "total_sources" in parsed


# ---------------------------------------------------------------------------
# test_csv_report_has_expected_columns
# ---------------------------------------------------------------------------

def test_csv_report_has_expected_columns(valid_manifest):
    from gdsn_to_gs1_jsonld.product_passport_sources import (
        build_product_passport_source_inventory,
        inventory_report_bytes_csv,
    )
    import csv
    import io

    inventory = build_product_passport_source_inventory(valid_manifest, base_dir=str(ROOT))
    csv_bytes = inventory_report_bytes_csv(inventory)
    reader = csv.DictReader(io.StringIO(csv_bytes.decode("utf-8")))
    columns = set(reader.fieldnames or [])
    assert "source_id" in columns
    assert "source_type" in columns
    assert "sector" in columns
    assert "_checksum_status" in columns


# ---------------------------------------------------------------------------
# test_validate_valid_minimal_product_passport
# ---------------------------------------------------------------------------

def test_validate_valid_minimal_product_passport(minimal_instance, minimal_schema):
    from gdsn_to_gs1_jsonld.product_passport_sources import validate_product_passport_json
    report = validate_product_passport_json(minimal_instance, minimal_schema)
    assert report["validation_status"] == "valid"
    assert report["errors"] == []


def test_validate_valid_from_file():
    from gdsn_to_gs1_jsonld.product_passport_sources import validate_product_passport_file
    report = validate_product_passport_file(str(EXAMPLE_PATH), str(SCHEMA_PATH))
    assert report["validation_status"] == "valid"
    assert isinstance(report["errors"], list)


# ---------------------------------------------------------------------------
# test_validate_invalid_product_passport_produces_errors
# ---------------------------------------------------------------------------

def test_validate_invalid_product_passport_produces_errors(minimal_schema):
    from gdsn_to_gs1_jsonld.product_passport_sources import validate_product_passport_json
    # Instance missing both @context and @type
    instance = {"gs1:gtin": "09521234543213"}
    report = validate_product_passport_json(instance, minimal_schema)
    assert report["validation_status"] == "invalid"
    assert len(report["errors"]) > 0


# ---------------------------------------------------------------------------
# test_validation_report_has_required_fields
# ---------------------------------------------------------------------------

def test_validation_report_has_required_fields(minimal_instance, minimal_schema):
    from gdsn_to_gs1_jsonld.product_passport_sources import validate_product_passport_json
    report = validate_product_passport_json(minimal_instance, minimal_schema)
    required_keys = {
        "validation_status",
        "errors",
        "warnings",
        "validator_version",
        "prototype_warning",
    }
    for key in required_keys:
        assert key in report, f"Missing required key: {key}"


def test_validate_product_passport_file_report_has_required_fields():
    from gdsn_to_gs1_jsonld.product_passport_sources import validate_product_passport_file
    report = validate_product_passport_file(str(EXAMPLE_PATH), str(SCHEMA_PATH))
    required_keys = {
        "validation_status",
        "schema_id",
        "schema_title",
        "instance_file",
        "schema_file",
        "errors",
        "warnings",
        "validator_version",
        "source_manifest_entry",
        "prototype_warning",
    }
    for key in required_keys:
        assert key in report, f"Missing required key: {key}"


# ---------------------------------------------------------------------------
# test_no_network_required
# ---------------------------------------------------------------------------

def test_no_network_required(minimal_instance, minimal_schema):
    """Validate that no network calls are made during validation."""
    import urllib.request

    from gdsn_to_gs1_jsonld.product_passport_sources import (
        validate_product_passport_json,
        build_product_passport_source_inventory,
        load_product_passport_source_manifest,
    )

    with mock.patch("urllib.request.urlopen", side_effect=AssertionError("Network call made")):
        manifest = load_product_passport_source_manifest(str(MANIFEST_PATH))
        _ = build_product_passport_source_inventory(manifest, base_dir=str(ROOT))
        report = validate_product_passport_json(minimal_instance, minimal_schema)

    assert report["validation_status"] in ("valid", "invalid")


# ---------------------------------------------------------------------------
# test_cli_inventory_command_runs
# ---------------------------------------------------------------------------

def test_cli_inventory_command_runs():
    from typer.testing import CliRunner
    from gdsn_to_gs1_jsonld.cli import app

    inv_output = _TEST_TMPDIR / "inv_output"
    inv_output.mkdir(parents=True, exist_ok=True)

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "inventory-product-passport-sources",
            "--manifest",
            str(MANIFEST_PATH),
            "--output-dir",
            str(inv_output),
        ],
    )
    # Exit 0 on success
    assert result.exit_code == 0, f"CLI failed: {result.output}\n{result.exception}"
    assert "source inventory" in result.output.lower() or "sources" in result.output.lower()


# ---------------------------------------------------------------------------
# test_cli_validate_command_runs
# ---------------------------------------------------------------------------

def test_cli_validate_command_runs():
    from typer.testing import CliRunner
    from gdsn_to_gs1_jsonld.cli import app

    val_output = _TEST_TMPDIR / "val_output"
    val_output.mkdir(parents=True, exist_ok=True)

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "validate-product-passport",
            "--input",
            str(EXAMPLE_PATH),
            "--schema",
            str(SCHEMA_PATH),
            "--output-dir",
            str(val_output),
        ],
    )
    # Exit 0 on success (even if validation fails, only tool error is non-zero)
    assert result.exit_code == 0, f"CLI failed: {result.output}\n{result.exception}"
    assert "status" in result.output.lower() or "valid" in result.output.lower()
