"""Tests for GDSN codelist import & runtime validation (Track D, v0.20.0).

Covers: workbook parsing, deterministic registry structure, validation
status logic, and converter integration. The converter integration tests
are the most important ones here: codelist validation must be fully
opt-in and never change ``jsonld_data`` or any pre-v0.20.0 field.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from gdsn_to_gs1_jsonld.codelist_importer import (
    CODELIST_SOURCE_VERSION,
    build_codelist_registry,
    write_codelist_registry,
)
from gdsn_to_gs1_jsonld.codelist_registry import (
    CODELIST_DEPENDENCIES,
    CodelistRegistryError,
    VALIDATION_STATUSES,
    load_codelist_registry,
    validate_canonical_product_codelists,
    validate_code_value,
)
from gdsn_to_gs1_jsonld.converter import convert_xml_to_jsonld

ROOT = Path(__file__).resolve().parents[1]
CODELIST_XLSX = (
    ROOT
    / "reference_data"
    / "raw_public"
    / "GDSN_and_Shared_Code_Lists_r3p1p36_i6_8May2026.xlsx"
)
CODELIST_REGISTRY_JSON = (
    ROOT / "reference_data" / "normalized" / "gdsn_codelists_r3_1_36.json"
)
MAPPING_REGISTRY = ROOT / "mapping" / "mapping_registry.yaml"
MAPPING_V0_3 = ROOT / "mapping" / "mapping_v0_3.yaml"
EXAMPLE_XML = ROOT / "examples" / "input" / "example_product.xml"


# ---------------------------------------------------------------------------
# Importer
# ---------------------------------------------------------------------------


def test_build_codelist_registry_from_real_workbook():
    result = build_codelist_registry(CODELIST_XLSX)
    assert result.codelist_count > 500
    assert result.value_count > 10000
    assert result.deprecated_value_count > 0


def test_registry_contains_all_codelists_our_mapping_uses():
    result = build_codelist_registry(CODELIST_XLSX)
    for codelist_name in CODELIST_DEPENDENCIES.values():
        assert codelist_name in result.codelists, codelist_name


def test_registry_values_are_deterministically_sorted():
    result = build_codelist_registry(CODELIST_XLSX)
    for entry in result.codelists.values():
        values = [item["value"] for item in entry["values"]]
        assert values == sorted(values)


def test_write_codelist_registry_is_valid_json(tmp_path):
    result = build_codelist_registry(CODELIST_XLSX)
    paths = write_codelist_registry(
        result, source_path=CODELIST_XLSX, output_dir=tmp_path
    )
    payload = json.loads(Path(paths["registry"]).read_text(encoding="utf-8"))
    assert payload["source_version"] == CODELIST_SOURCE_VERSION
    assert len(payload["source_sha256"]) == 64
    assert "AllergenTypeCode" in payload["codelists"]

    summary = json.loads(Path(paths["summary"]).read_text(encoding="utf-8"))
    assert summary["codelist_count"] == result.codelist_count


# ---------------------------------------------------------------------------
# Validation status logic
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def real_registry():
    return load_codelist_registry(CODELIST_REGISTRY_JSON)


def test_load_codelist_registry_missing_file_raises(tmp_path):
    with pytest.raises(CodelistRegistryError):
        load_codelist_registry(tmp_path / "does_not_exist.json")


def test_validate_code_value_valid(real_registry):
    status, detail = validate_code_value(real_registry, "AllergenTypeCode", "AM")
    assert status == "valid"
    assert "AM" in detail


def test_validate_code_value_case_insensitive(real_registry):
    status, _ = validate_code_value(real_registry, "AllergenTypeCode", "am")
    assert status == "valid"


def test_validate_code_value_missing(real_registry):
    status, _ = validate_code_value(real_registry, "AllergenTypeCode", "")
    assert status == "missing"
    status, _ = validate_code_value(real_registry, "AllergenTypeCode", None)
    assert status == "missing"


def test_validate_code_value_source_unavailable(real_registry):
    status, _ = validate_code_value(real_registry, "NotARealCodelist", "X")
    assert status == "source_unavailable"


def test_validate_code_value_unknown(real_registry):
    status, _ = validate_code_value(
        real_registry, "AllergenTypeCode", "NOT_A_REAL_ALLERGEN_CODE"
    )
    assert status == "unknown"


def test_validate_code_value_deprecated(real_registry):
    deprecated_entries = [
        (name, entry["deprecated_values"][0]["value"])
        for name, entry in real_registry["codelists"].items()
        if entry["deprecated_values"]
    ]
    assert deprecated_entries, "expected at least one deprecated value on real data"
    codelist_name, value = deprecated_entries[0]
    status, detail = validate_code_value(real_registry, codelist_name, value)
    assert status == "deprecated"
    assert "sunset" in detail.lower()


def test_all_validation_statuses_are_in_fixed_vocabulary(real_registry):
    cases = [
        ("AllergenTypeCode", "AM"),
        ("AllergenTypeCode", ""),
        ("AllergenTypeCode", "NOT_REAL"),
        ("NotARealCodelist", "X"),
    ]
    for codelist_name, value in cases:
        status, _ = validate_code_value(real_registry, codelist_name, value)
        assert status in VALIDATION_STATUSES


def test_validate_canonical_product_codelists_top_level_and_nested(real_registry):
    product_dump = {
        "net_content_unit": "LTR",
        "allergens": [
            {"allergen_type": "AM", "level_of_containment": "FREE_FROM"},
            {"allergen_type": "NOT_REAL", "level_of_containment": "CONTAINS"},
        ],
    }
    results = validate_canonical_product_codelists(
        product_dump, CODELIST_DEPENDENCIES, real_registry
    )
    by_field = {r["canonical_field"]: r for r in results}
    assert by_field["net_content_unit"]["status"] == "valid"
    assert by_field["allergens[0].allergen_type"]["status"] == "valid"
    assert by_field["allergens[1].allergen_type"]["status"] == "unknown"


# ---------------------------------------------------------------------------
# Converter integration — must be fully opt-in
# ---------------------------------------------------------------------------


def test_converter_without_codelist_registry_is_unchanged():
    """Default behavior (no codelist_registry arg) must be byte-identical
    to pre-v0.20.0: empty codelist_validation, nothing else affected."""
    xml_bytes = EXAMPLE_XML.read_bytes()
    result = convert_xml_to_jsonld(xml_bytes, MAPPING_REGISTRY, write_files=False)
    assert result.codelist_validation == []


def test_converter_output_identical_with_and_without_codelist_registry():
    """Passing a codelist_registry must never change jsonld_data, mapping
    report rows, validation_report, or unmapped_fields — only the new
    codelist_validation field differs."""
    xml_bytes = EXAMPLE_XML.read_bytes()
    without = convert_xml_to_jsonld(xml_bytes, MAPPING_REGISTRY, write_files=False)
    registry = load_codelist_registry(CODELIST_REGISTRY_JSON)
    with_registry = convert_xml_to_jsonld(
        xml_bytes, MAPPING_REGISTRY, write_files=False, codelist_registry=registry
    )

    dump = lambda data: json.dumps(data, sort_keys=True, ensure_ascii=False, default=str)
    assert dump(without.jsonld_data) == dump(with_registry.jsonld_data)
    assert without.mapping_report_rows == with_registry.mapping_report_rows
    assert without.validation_report == with_registry.validation_report
    assert without.unmapped_fields == with_registry.unmapped_fields
    assert without.codelist_validation == []
    assert with_registry.codelist_validation != []


def test_converter_codelist_validation_never_blocks_conversion():
    """Even with clearly-unknown codelist values present, conversion still
    succeeds — codelist validation is a diagnostic, never a hard failure,
    unless a caller separately decides to treat it as one."""
    xml_bytes = EXAMPLE_XML.read_bytes()
    registry = load_codelist_registry(CODELIST_REGISTRY_JSON)
    result = convert_xml_to_jsonld(
        xml_bytes, MAPPING_REGISTRY, write_files=False, codelist_registry=registry
    )
    assert result.jsonld_data
    statuses = {entry["status"] for entry in result.codelist_validation}
    assert statuses <= set(VALIDATION_STATUSES)


def test_converter_codelist_validation_identical_across_mapping_v0_3_and_registry():
    """The registry's fields are structurally identical to mapping_v0_3.yaml
    (v0.15.0), so codelist validation results must match too."""
    xml_bytes = EXAMPLE_XML.read_bytes()
    registry = load_codelist_registry(CODELIST_REGISTRY_JSON)
    from_registry_mapping = convert_xml_to_jsonld(
        xml_bytes, MAPPING_REGISTRY, write_files=False, codelist_registry=registry
    )
    from_v0_3_mapping = convert_xml_to_jsonld(
        xml_bytes, MAPPING_V0_3, write_files=False, codelist_registry=registry
    )
    assert from_registry_mapping.codelist_validation == from_v0_3_mapping.codelist_validation
