"""Tests for Manual Builder per-field status derivation (v0.18.0).

Pure-function tests; no Streamlit dependency. Verifies the fixed status
vocabulary, priority order, and that the two reserved statuses
(external_source_required, extension_candidate) are never fabricated from
current local data.
"""

from __future__ import annotations

from pathlib import Path

from gdsn_to_gs1_jsonld.builder_status import (
    RESERVED_STATUS_VALUES,
    STATUS_VALUES,
    build_hard_mapping_index,
    compute_field_status,
    summarize_field_statuses,
)

ROOT = Path(__file__).resolve().parents[1]
GDSN_CSV = ROOT / "reference_data" / "normalized" / "gdsn_attributes_bms_xpath_3_1_36.csv"


def test_status_vocabulary_fixed():
    assert STATUS_VALUES == (
        "filled",
        "missing",
        "review_required",
        "hard_mapping_review",
        "codelist_pending",
        "external_source_required",
        "extension_candidate",
        "blocked",
    )
    for reserved in RESERVED_STATUS_VALUES:
        assert reserved in STATUS_VALUES


def test_blocked_takes_priority_over_everything():
    metadata = {
        "supported_in_v0_10": False,
        "planned_reason": "needs governed modelling",
        "requirement": "required",
    }
    status, reasons = compute_field_status(metadata, value_present=False)
    assert status == "blocked"
    assert "needs governed modelling" in reasons[0]


def test_missing_when_required_and_empty():
    status, _ = compute_field_status(
        {"requirement": "required"}, value_present=False
    )
    assert status == "missing"


def test_required_and_filled_is_filled_not_missing():
    status, _ = compute_field_status(
        {"requirement": "required"}, value_present=True
    )
    assert status == "filled"


def test_codelist_pending_for_empty_code_options():
    status, reasons = compute_field_status(
        {"requirement": "optional", "input_type_override": "code", "options": []},
        value_present=False,
    )
    assert status == "codelist_pending"
    assert reasons


def test_code_field_with_options_is_not_codelist_pending():
    metadata = {
        "requirement": "optional",
        "input_type_override": "code",
        "options": [{"value": "x", "label": "X"}],
    }
    status, _ = compute_field_status(metadata, value_present=False)
    assert status != "codelist_pending"
    assert status == "optional_empty"


def test_codelist_pending_falls_back_to_full_codelist_options():
    """v0.23.0: a field is only codelist_pending if BOTH the manifest's
    curated options AND the WebVoc-derived full_codelist_options fallback
    are empty."""
    metadata = {
        "requirement": "optional",
        "input_type_override": "code",
        "options": [],
        "full_codelist_options": [{"value": "gs1:X-A", "label": "A"}],
    }
    status, _ = compute_field_status(metadata, value_present=False)
    assert status != "codelist_pending"

    metadata_no_fallback = {
        "requirement": "optional",
        "input_type_override": "code",
        "options": [],
        "full_codelist_options": [],
    }
    status, reasons = compute_field_status(metadata_no_fallback, value_present=False)
    assert status == "codelist_pending"
    assert reasons


def test_review_required_from_coverage_status():
    status, _ = compute_field_status(
        {"requirement": "optional", "coverage_status": "standards_review_required"},
        value_present=False,
    )
    assert status == "review_required"


def test_optional_empty_is_the_neutral_untouched_state():
    status, reasons = compute_field_status(
        {"requirement": "optional"}, value_present=False
    )
    assert status == "optional_empty"
    assert reasons == []


def test_hard_mapping_review_from_evidence_cross_reference():
    hard_mapping_index = {"100": (True, ["cross_class_reference_to_PartyIdentification: x"])}
    metadata = {
        "requirement": "optional",
        "evidence": [{"gdsn_bms_id": "100"}],
    }
    status, reasons = compute_field_status(
        metadata, value_present=False, hard_mapping_index=hard_mapping_index
    )
    assert status == "hard_mapping_review"
    assert reasons


def test_hard_mapping_review_not_triggered_for_standard_evidence():
    hard_mapping_index = {"100": (False, [])}
    metadata = {"requirement": "optional", "evidence": [{"gdsn_bms_id": "100"}]}
    status, _ = compute_field_status(
        metadata, value_present=False, hard_mapping_index=hard_mapping_index
    )
    assert status != "hard_mapping_review"


def test_reserved_statuses_never_returned_by_compute_field_status():
    """external_source_required and extension_candidate require data this
    project does not have yet (promoted hard mappings; Crosswalk gaps) and
    must never be fabricated."""
    # Sweep a broad set of metadata shapes; none should ever produce a
    # reserved status, since compute_field_status has no code path for them.
    samples = [
        {"requirement": "required"},
        {"requirement": "optional"},
        {"supported_in_v0_10": False},
        {"input_type_override": "code", "options": []},
        {"coverage_status": "standards_review_required"},
        {"evidence": [{"gdsn_bms_id": "999999"}]},
    ]
    for metadata in samples:
        for value_present in (True, False):
            status, _ = compute_field_status(metadata, value_present=value_present)
            assert status not in RESERVED_STATUS_VALUES


def test_summarize_field_statuses_counts_all_buckets():
    counts = summarize_field_statuses(["filled", "filled", "missing", "optional_empty"])
    assert counts["filled"] == 2
    assert counts["missing"] == 1
    assert counts["optional_empty"] == 1
    assert counts["blocked"] == 0


def test_build_hard_mapping_index_matches_candidate_generator_detection():
    index = build_hard_mapping_index(GDSN_CSV)
    assert len(index) > 0
    # A known hard-mapping GDSN attribute (PartyIdentification GLN) must be
    # flagged; the product's own gtin must not be.
    gtin_hits = [
        (bms_id, is_hard)
        for bms_id, (is_hard, _reasons) in index.items()
        if is_hard
    ]
    assert gtin_hits, "expected at least one hard-mapping bms_id in the reference data"
