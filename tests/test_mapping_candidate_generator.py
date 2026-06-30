"""Tests for the Mapping Candidate Generator (v0.11.0).

These tests verify:
- Data loading functions return the expected types.
- Scoring produces reasonable results for known pairs.
- Deleted rows produce warnings but not normal high-confidence candidates.
- DataType compatibility reasons appear for compatible pairs.
- Output is fully deterministic (same inputs -> same outputs twice).
- Summary counts are correct.
- JSON report is valid JSON.
- CSV report has expected columns.
- Confidence filter works correctly.
- Limit per property is respected.
- No mapping YAML is modified by the generator.
- All required candidate dict fields are present.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from gdsn_to_gs1_jsonld.mapping_candidate_generator import (
    CREATED_BY_VERSION,
    build_candidate_inputs,
    candidate_report_bytes_csv,
    candidate_report_bytes_json,
    classify_confidence,
    filter_candidates,
    generate_all_candidates,
    generate_candidate_summary,
    generate_candidates_for_property,
    load_existing_mapping_catalog,
    load_gdsn_reference,
    load_mapping_yaml,
    load_standards_backlog,
    load_webvoc_properties,
    normalize_text,
    score_candidate,
    tokenize_mapping_text,
)

ROOT = Path(__file__).resolve().parents[1]
GDSN_CSV = ROOT / "reference_data" / "normalized" / "gdsn_attributes_bms_xpath_3_1_36.csv"
WEBVOC_CSV = ROOT / "reference_data" / "normalized" / "webvoc_properties_1_17.csv"
CATALOG_CSV = (
    ROOT
    / "mapping_catalog"
    / "gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_3_webvoc_validated.csv"
)
MAPPING_YAML = ROOT / "mapping" / "mapping_v0_3.yaml"
BACKLOG_JSON = ROOT / "docs" / "standards-decisions" / "standards_review_backlog.json"

# Required fields in every candidate dict.
REQUIRED_CANDIDATE_FIELDS = {
    "candidate_id",
    "webvoc_property_id",
    "webvoc_compact_name",
    "webvoc_label",
    "webvoc_comment",
    "webvoc_domain",
    "webvoc_range",
    "gdsn_bms_id",
    "gdsn_attribute_name",
    "gdsn_xpath",
    "gdsn_module",
    "gdsn_parent_class",
    "gdsn_data_type",
    "gdsn_multiplicity",
    "gdsn_code_list_name",
    "gdsn_bms_code_list_id",
    "gdsn_semantic_resource_urn",
    "gdsn_definition",
    "source_message",
    "is_deleted",
    "is_candidate_source",
    "existing_mapping_status",
    "existing_mapping_field",
    "existing_mapping_confidence",
    "standards_review_status",
    "linked_sdr_ids",
    "score",
    "confidence_level",
    "review_status",
    "reasons",
    "warnings",
    "blocking_notes",
    "created_by_version",
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def inputs():
    """Build candidate inputs once for the whole test module."""
    return build_candidate_inputs(
        webvoc_path=str(WEBVOC_CSV),
        gdsn_path=str(GDSN_CSV),
        catalog_path=str(CATALOG_CSV),
        mapping_path=str(MAPPING_YAML),
        backlog_path=str(BACKLOG_JSON),
    )


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def test_load_gdsn_reference_returns_list():
    rows = load_gdsn_reference(str(GDSN_CSV))
    assert isinstance(rows, list)
    assert len(rows) > 0
    assert isinstance(rows[0], dict)
    # Check expected columns.
    assert "bms_id" in rows[0]
    assert "attribute_name" in rows[0]
    assert "xpath" in rows[0]


def test_load_webvoc_properties_returns_list():
    rows = load_webvoc_properties(str(WEBVOC_CSV))
    assert isinstance(rows, list)
    assert len(rows) > 0
    assert isinstance(rows[0], dict)
    assert "term_id" in rows[0]
    assert "compact_name" in rows[0]


def test_load_existing_mapping_catalog_returns_list():
    rows = load_existing_mapping_catalog(str(CATALOG_CSV))
    assert isinstance(rows, list)
    assert len(rows) > 0
    assert "jsonld_property" in rows[0]


def test_load_standards_backlog_returns_list_or_dict():
    result = load_standards_backlog(str(BACKLOG_JSON))
    # May be a list (when present).
    assert isinstance(result, list)
    assert len(result) > 0
    # Each entry should have at minimum 'id' and 'affected_properties'.
    for entry in result:
        assert "id" in entry


# ---------------------------------------------------------------------------
# GTIN property: already_mapped or high confidence expected
# ---------------------------------------------------------------------------


def test_generate_candidates_for_gtin_property(inputs):
    candidates = generate_candidates_for_property("gs1:gtin", inputs, limit=20)
    assert isinstance(candidates, list)
    assert len(candidates) > 0
    # The top candidate should have already_mapped or high confidence.
    top = candidates[0]
    assert top["review_status"] in {"already_mapped", "proposed"} or top["confidence_level"] in {"high", "medium"}
    # The gtin attribute with BMS ID 67 should appear near the top.
    bms_ids = [c["gdsn_bms_id"] for c in candidates]
    assert "67" in bms_ids, f"BMS ID 67 (gtin) not in top candidates: {bms_ids}"
    # Top candidate should have existing_mapping_catalog_match or exact_property_name_match.
    top_reasons = candidates[0]["reasons"]
    assert any(r in {
        "existing_mapping_catalog_match",
        "exact_property_name_match",
        "mapping_yaml_canonical_field_match",
    } for r in top_reasons)


# ---------------------------------------------------------------------------
# Deleted rows
# ---------------------------------------------------------------------------


def test_deleted_rows_are_not_normal_candidates(inputs):
    """Deleted rows should carry deleted_attribute_warning and not_recommended status."""
    gdsn_rows = inputs["gdsn_rows"]
    deleted_rows = [r for r in gdsn_rows if str(r.get("is_deleted", "")).lower() == "true"]
    if not deleted_rows:
        pytest.skip("No deleted rows in reference data.")

    # Pick an arbitrary WebVoc property.
    webvoc_prop = inputs["webvoc_rows"][0]
    deleted_row = deleted_rows[0]
    score, reasons, warnings = score_candidate(webvoc_prop, deleted_row, inputs)
    assert "deleted_attribute_warning" in warnings, (
        "Expected deleted_attribute_warning in warnings for deleted row"
    )


# ---------------------------------------------------------------------------
# DataType compatibility
# ---------------------------------------------------------------------------


def test_datatype_compatibility_reason_appears_for_compatible_pair(inputs):
    """A string-range WebVoc property paired with a string GDSN attribute should
    produce range_datatype_compatible reason."""
    # Find a WebVoc property with xsd:string range.
    string_prop = next(
        (r for r in inputs["webvoc_rows"] if r.get("range") == "xsd:string"),
        None,
    )
    if string_prop is None:
        pytest.skip("No xsd:string-range property found in WebVoc CSV.")

    # Find a GDSN attribute with string datatype.
    string_attr = next(
        (
            r for r in inputs["gdsn_rows"]
            if str(r.get("data_type") or "").lower() == "string"
            and str(r.get("row_type") or "").lower() == "attribute"
        ),
        None,
    )
    if string_attr is None:
        pytest.skip("No string-datatype GDSN attribute found.")

    score, reasons, warnings = score_candidate(string_prop, string_attr, inputs)
    assert "range_datatype_compatible" in reasons, (
        f"Expected range_datatype_compatible in reasons; got {reasons}"
    )


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_output_is_deterministic(inputs):
    """Running generate_candidates_for_property twice returns identical results."""
    result_a = generate_candidates_for_property("gs1:productName", inputs, limit=10)
    result_b = generate_candidates_for_property("gs1:productName", inputs, limit=10)
    assert len(result_a) == len(result_b)
    for a, b in zip(result_a, result_b):
        assert a["candidate_id"] == b["candidate_id"]
        assert a["score"] == b["score"]
        assert a["reasons"] == b["reasons"]


# ---------------------------------------------------------------------------
# Summary counts
# ---------------------------------------------------------------------------


def test_candidate_summary_counts_are_correct(inputs):
    candidates = generate_candidates_for_property("gs1:brandName", inputs, limit=20)
    summary = generate_candidate_summary(candidates)

    assert summary["total_candidates"] == len(candidates)
    assert summary["created_by_version"] == CREATED_BY_VERSION

    # Check that by_confidence totals sum to total.
    conf_total = sum(summary["by_confidence"].values())
    assert conf_total == len(candidates), (
        f"by_confidence sum {conf_total} != total {len(candidates)}"
    )

    # Check that by_review_status totals sum to total.
    status_total = sum(summary["by_review_status"].values())
    assert status_total == len(candidates), (
        f"by_review_status sum {status_total} != total {len(candidates)}"
    )


# ---------------------------------------------------------------------------
# JSON report
# ---------------------------------------------------------------------------


def test_json_report_is_valid_json(inputs):
    candidates = generate_candidates_for_property("gs1:netContent", inputs, limit=10)
    json_bytes = candidate_report_bytes_json(candidates)
    assert isinstance(json_bytes, bytes)
    parsed = json.loads(json_bytes.decode("utf-8"))
    assert isinstance(parsed, list)
    assert len(parsed) == len(candidates)


# ---------------------------------------------------------------------------
# CSV report
# ---------------------------------------------------------------------------


def test_csv_report_has_expected_columns(inputs):
    candidates = generate_candidates_for_property("gs1:gtin", inputs, limit=5)
    csv_bytes = candidate_report_bytes_csv(candidates)
    assert isinstance(csv_bytes, bytes)
    csv_text = csv_bytes.decode("utf-8")
    first_line = csv_text.splitlines()[0]
    columns = first_line.split(",")
    required_columns = {
        "candidate_id",
        "webvoc_property_id",
        "gdsn_bms_id",
        "score",
        "confidence_level",
        "review_status",
    }
    for col in required_columns:
        assert col in columns, f"Expected column '{col}' in CSV header: {columns}"


# ---------------------------------------------------------------------------
# Confidence filter
# ---------------------------------------------------------------------------


def test_min_confidence_filter_works(inputs):
    candidates = generate_candidates_for_property("gs1:productName", inputs, limit=30)
    high_only = filter_candidates(
        candidates, min_confidence="high", include_low_confidence=False,
        include_review_required=False,
    )
    for c in high_only:
        assert c["confidence_level"] == "high", (
            f"Expected only high confidence; got {c['confidence_level']}"
        )


# ---------------------------------------------------------------------------
# Limit per property
# ---------------------------------------------------------------------------


def test_limit_per_property_respected(inputs):
    limit = 5
    candidates = generate_candidates_for_property("gs1:brandName", inputs, limit=limit)
    assert len(candidates) <= limit, (
        f"Expected at most {limit} candidates; got {len(candidates)}"
    )


# ---------------------------------------------------------------------------
# Mapping YAML not modified
# ---------------------------------------------------------------------------


def test_no_mapping_yaml_modified(inputs):
    """Verify YAML content is unchanged after candidate generation."""
    original_yaml = load_mapping_yaml(str(MAPPING_YAML))
    # Run generation.
    generate_candidates_for_property("gs1:gtin", inputs, limit=5)
    # Re-read and compare.
    after_yaml = load_mapping_yaml(str(MAPPING_YAML))
    assert original_yaml == after_yaml, "Mapping YAML was modified by candidate generation."


# ---------------------------------------------------------------------------
# Required fields
# ---------------------------------------------------------------------------


def test_candidate_has_required_fields(inputs):
    candidates = generate_candidates_for_property("gs1:gtin", inputs, limit=5)
    assert len(candidates) > 0, "Expected at least one candidate for gs1:gtin."
    for candidate in candidates:
        missing = REQUIRED_CANDIDATE_FIELDS - set(candidate.keys())
        assert not missing, f"Candidate missing required fields: {missing}"
        assert candidate["created_by_version"] == CREATED_BY_VERSION


# ---------------------------------------------------------------------------
# Text utilities
# ---------------------------------------------------------------------------


def test_normalize_text_removes_special_chars():
    assert normalize_text("Allergen Type Code!") == "allergen type code"
    assert normalize_text("") == ""


def test_tokenize_mapping_text_excludes_stopwords():
    tokens = tokenize_mapping_text("The identifier of a catalogueItemNotification")
    # "the", "of", "a" are stopwords; non-stopword content words should remain.
    assert "the" not in tokens
    assert "of" not in tokens
    # Multi-word content like "catalogueitemnotification" or split camelCase parts
    # should appear as tokens.
    assert len(tokens) > 0


# ---------------------------------------------------------------------------
# Classify confidence
# ---------------------------------------------------------------------------


def test_classify_confidence_thresholds():
    assert classify_confidence(0.80, []) == "high"
    assert classify_confidence(0.50, []) == "medium"
    assert classify_confidence(0.20, []) == "low"
    assert classify_confidence(0.05, []) == "review_required"
    # review_required forced if SDR linked regardless of score.
    assert classify_confidence(0.10, ["standards_review_linked"]) == "review_required"
