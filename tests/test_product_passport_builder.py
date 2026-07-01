"""Tests for the Product Passport Builder (v0.13.0, minimal-schema mode).

Deterministic and offline. Uses a dedicated temp directory to avoid the
Windows pytest tmp-path permission issue seen in this environment.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from gdsn_to_gs1_jsonld.cli import app
from gdsn_to_gs1_jsonld.product_passport_builder import (
    DEFAULT_SCHEMA_PATH,
    build_minimal_product_passport,
    build_product_passport_summary,
    extract_brand,
    extract_gtin,
    extract_product_name,
    load_gs1_jsonld,
    normalize_gs1_jsonld_input,
    product_passport_report_bytes_json,
    product_passport_to_json_bytes,
    validate_built_product_passport,
    write_product_passport_outputs,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / DEFAULT_SCHEMA_PATH
EXAMPLE_PATH = (
    ROOT / "product_passport" / "examples" / "gs1_product_for_passport_builder.jsonld"
)
_OUT_DIR = Path(tempfile.gettempdir()) / "gdsn_ppb_tests"


@pytest.fixture
def gs1_jsonld() -> dict:
    return {
        "@context": "https://ref.gs1.org/voc/data/gs1Voc.jsonld",
        "@type": "gs1:Product",
        "@id": "https://id.gs1.org/01/09521234543213",
        "gtin": "09521234543213",
        "productName": [{"@value": "Test Juice", "@language": "en"}],
        "brand": "Test Brand",
    }


# ---------------------------------------------------------------------------
# Input loading
# ---------------------------------------------------------------------------


def test_normalize_accepts_dict(gs1_jsonld) -> None:
    assert normalize_gs1_jsonld_input(gs1_jsonld) is gs1_jsonld


def test_normalize_parses_json_string(gs1_jsonld) -> None:
    text = json.dumps(gs1_jsonld)
    assert normalize_gs1_jsonld_input(text) == gs1_jsonld


def test_normalize_rejects_invalid_json() -> None:
    with pytest.raises(ValueError):
        normalize_gs1_jsonld_input("{not valid json")


def test_load_gs1_jsonld_from_file() -> None:
    data = load_gs1_jsonld(str(EXAMPLE_PATH))
    assert isinstance(data, dict)
    assert data.get("@type")


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------


def test_extract_gtin_from_direct_field(gs1_jsonld) -> None:
    assert extract_gtin(gs1_jsonld) == "09521234543213"


def test_extract_gtin_from_digital_link_id() -> None:
    data = {"@id": "https://id.gs1.org/01/09521234543213", "@type": "gs1:Product"}
    assert extract_gtin(data) == "09521234543213"


def test_extract_product_name_from_language_list(gs1_jsonld) -> None:
    assert extract_product_name(gs1_jsonld) == "Test Juice"


def test_extract_brand(gs1_jsonld) -> None:
    assert extract_brand(gs1_jsonld) == "Test Brand"


# ---------------------------------------------------------------------------
# Envelope building
# ---------------------------------------------------------------------------


def test_envelope_has_context_and_type(gs1_jsonld) -> None:
    passport = build_minimal_product_passport(gs1_jsonld)
    assert passport["@context"]
    assert passport["@type"] == "Product"


def test_envelope_includes_prototype_notice(gs1_jsonld) -> None:
    passport = build_minimal_product_passport(gs1_jsonld)
    notice = passport["prototypeNotice"].lower()
    assert "prototype" in notice
    assert "not official gs1 validation" in notice
    assert "not production-ready" in notice or "not production" in notice


def test_envelope_embeds_source_by_default(gs1_jsonld) -> None:
    passport = build_minimal_product_passport(gs1_jsonld)
    assert passport["product"] == gs1_jsonld


def test_envelope_can_exclude_source(gs1_jsonld) -> None:
    passport = build_minimal_product_passport(
        gs1_jsonld, {"include_source_gs1_jsonld": False}
    )
    assert "product" not in passport


def test_envelope_is_deterministic(gs1_jsonld) -> None:
    a = product_passport_to_json_bytes(build_minimal_product_passport(gs1_jsonld))
    b = product_passport_to_json_bytes(build_minimal_product_passport(gs1_jsonld))
    assert a == b


def test_generated_at_omitted_by_default(gs1_jsonld) -> None:
    passport = build_minimal_product_passport(gs1_jsonld)
    assert "generatedAt" not in passport


def test_generated_at_included_when_supplied(gs1_jsonld) -> None:
    passport = build_minimal_product_passport(
        gs1_jsonld, {"generated_at": "2026-07-01T00:00:00Z"}
    )
    assert passport["generatedAt"] == "2026-07-01T00:00:00Z"


# ---------------------------------------------------------------------------
# Validation and outputs
# ---------------------------------------------------------------------------


def test_built_passport_validates_against_minimal_schema(gs1_jsonld) -> None:
    passport = build_minimal_product_passport(gs1_jsonld)
    report = validate_built_product_passport(passport, str(SCHEMA_PATH))
    assert report["validation_status"] == "valid"
    assert report["validator_mode"] == "jsonschema"


def test_report_bytes_are_valid_json(gs1_jsonld) -> None:
    passport = build_minimal_product_passport(gs1_jsonld)
    report = validate_built_product_passport(passport, str(SCHEMA_PATH))
    parsed = json.loads(product_passport_report_bytes_json(report))
    assert parsed["validation_status"] == "valid"


def test_summary_includes_structural_validation_status(gs1_jsonld) -> None:
    passport = build_minimal_product_passport(gs1_jsonld)
    report = validate_built_product_passport(passport, str(SCHEMA_PATH))
    summary = build_product_passport_summary(passport, report)
    assert summary["structuralValidationStatus"] == "valid"
    assert summary["sourceGtin"] == "09521234543213"
    assert "not official gs1 validation" in summary["prototypeNotice"].lower()


def test_write_outputs_creates_three_files(gs1_jsonld) -> None:
    passport = build_minimal_product_passport(gs1_jsonld)
    report = validate_built_product_passport(passport, str(SCHEMA_PATH))
    out_dir = _OUT_DIR / "write_test"
    paths = write_product_passport_outputs(passport, report, str(out_dir))
    assert Path(paths["product_passport_jsonld"]).is_file()
    assert Path(paths["validation_report_json"]).is_file()
    assert Path(paths["summary_json"]).is_file()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def test_cli_build_product_passport() -> None:
    runner = CliRunner()
    out_dir = _OUT_DIR / "cli_test"
    result = runner.invoke(
        app,
        [
            "build-product-passport",
            "--input",
            str(EXAMPLE_PATH),
            "--schema",
            str(SCHEMA_PATH),
            "--output-dir",
            str(out_dir),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "prototype" in result.output.lower()
    assert "Structural validation status: valid" in result.output
    assert (out_dir / "product_passport.jsonld").is_file()
    assert (out_dir / "product_passport_validation_report.json").is_file()


def test_cli_output_has_no_positive_compliance_claim() -> None:
    runner = CliRunner()
    out_dir = _OUT_DIR / "cli_claim_test"
    result = runner.invoke(
        app,
        [
            "build-product-passport",
            "--input",
            str(EXAMPLE_PATH),
            "--schema",
            str(SCHEMA_PATH),
            "--output-dir",
            str(out_dir),
        ],
    )
    lowered = result.output.lower()
    # Compliance is only ever mentioned in the negative.
    assert "not official gs1 validation" in lowered
    assert "production compliance" in lowered  # appears only as "not ... compliance"
