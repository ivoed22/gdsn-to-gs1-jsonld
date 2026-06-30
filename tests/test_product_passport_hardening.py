"""Hardening tests for v0.12.1 Product Passport Bridge.

Covers the jsonschema dependency path, fallback visibility, manifest schema
enforcement, and CSV formula-injection neutralization. Deterministic, offline.
"""

from __future__ import annotations

import builtins
from pathlib import Path

from gdsn_to_gs1_jsonld.product_passport_sources import (
    inventory_report_bytes_csv,
    load_json_schema,
    load_product_passport_source_manifest,
    validate_product_passport_json,
    validate_product_passport_source_manifest,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = (
    ROOT / "product_passport" / "reference_sources" / "source_manifest.json"
)
MANIFEST_SCHEMA_PATH = (
    ROOT / "product_passport" / "reference_sources" / "source_manifest.schema.json"
)

MINIMAL_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["@context", "@type"],
    "properties": {"@type": {"type": "string"}},
}


# ---------------------------------------------------------------------------
# DEP-1: jsonschema dependency and fallback visibility
# ---------------------------------------------------------------------------


def test_jsonschema_is_importable() -> None:
    import jsonschema  # noqa: F401


def test_validator_uses_jsonschema_when_available() -> None:
    instance = {"@context": "https://gs1.org/voc/", "@type": "gs1:Product"}
    report = validate_product_passport_json(instance, MINIMAL_SCHEMA)
    assert report["validator_mode"] == "jsonschema"
    assert report["validation_status"] == "valid"


def test_jsonschema_catches_type_violation_fallback_would_miss() -> None:
    # @type must be a string. A non-string is only caught by full Draft7
    # validation, not by the required-field fallback.
    instance = {"@context": "x", "@type": 123}
    report = validate_product_passport_json(instance, MINIMAL_SCHEMA)
    assert report["validator_mode"] == "jsonschema"
    assert report["validation_status"] == "invalid"
    assert report["errors"]


def test_fallback_used_and_warns_when_jsonschema_unavailable(monkeypatch) -> None:
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "jsonschema" or name.startswith("jsonschema."):
            raise ImportError("forced unavailable for test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    instance = {"@context": "x", "@type": "gs1:Product"}
    report = validate_product_passport_json(instance, MINIMAL_SCHEMA)
    assert report["validator_mode"] == "minimal_fallback"
    assert any("FALLBACK MODE" in w for w in report["warnings"])
    # Required fields present, so still "valid" — but the warning makes the
    # weaker check explicit.
    assert report["validation_status"] == "valid"


# ---------------------------------------------------------------------------
# ARCH-1: manifest schema enforcement
# ---------------------------------------------------------------------------


def test_committed_manifest_passes_schema_enforcement() -> None:
    manifest = load_product_passport_source_manifest(str(MANIFEST_PATH))
    schema = load_json_schema(str(MANIFEST_SCHEMA_PATH))
    errors = validate_product_passport_source_manifest(manifest, schema=schema)
    assert errors == [], f"committed manifest must pass schema enforcement: {errors}"


def test_manifest_schema_rejects_bad_source_id_pattern() -> None:
    schema = load_json_schema(str(MANIFEST_SCHEMA_PATH))
    bad = {
        "schema_version": "1.0",
        "sources": [
            {
                "source_id": "Bad-ID With Spaces",
                "title": "x",
                "source_url": "PLACEHOLDER",
                "source_type": "json_schema",
                "sector": "core",
                "local_path": "x",
            }
        ],
    }
    errors = validate_product_passport_source_manifest(bad, schema=schema)
    assert any("schema:" in e for e in errors)


def test_manifest_schema_rejects_additional_properties() -> None:
    schema = load_json_schema(str(MANIFEST_SCHEMA_PATH))
    bad = {
        "schema_version": "1.0",
        "sources": [
            {
                "source_id": "ok_id",
                "title": "x",
                "source_url": "PLACEHOLDER",
                "source_type": "json_schema",
                "sector": "core",
                "local_path": "x",
                "unexpected_field": "boom",
            }
        ],
    }
    errors = validate_product_passport_source_manifest(bad, schema=schema)
    assert any("schema:" in e for e in errors)


def test_custom_checks_still_run_without_schema() -> None:
    # Backward compatibility: calling without a schema still runs domain checks.
    bad = {"sources": [{"source_id": "x"}]}  # missing required fields
    errors = validate_product_passport_source_manifest(bad)
    assert errors  # custom checks report the missing fields


# ---------------------------------------------------------------------------
# SEC: CSV formula-injection neutralization
# ---------------------------------------------------------------------------


def test_csv_report_neutralizes_formula_injection() -> None:
    inventory = {
        "entries": [
            {
                "source_id": "=cmd()",
                "title": "+SUM(A1)",
                "source_type": "@evil",
                "sector": "-danger",
                "version": "1.0",
                "local_path": "x",
                "_file_exists": True,
                "_checksum_status": "ok",
                "_actual_sha256": None,
            }
        ]
    }
    csv_text = inventory_report_bytes_csv(inventory).decode("utf-8")
    assert "'=cmd()" in csv_text
    assert "'+SUM(A1)" in csv_text
    assert "'@evil" in csv_text
    assert "'-danger" in csv_text
