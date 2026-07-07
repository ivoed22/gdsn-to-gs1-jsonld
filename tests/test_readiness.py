"""Tests for the per-product DPP readiness assessment (v0.31.0).

Pure-function tests plus a real-fixture cross-check. The honesty rules are
the important part: no invented score, DPP relevance always
not-yet-assessed pending the Crosswalk, codelist dimension reports
not_evaluated (never a fake clean result) when no registry was used, and
the scope note negates every restricted claim phrase.
"""

from __future__ import annotations

from pathlib import Path

from gdsn_to_gs1_jsonld.codelist_registry import load_codelist_registry
from gdsn_to_gs1_jsonld.converter import convert_xml_to_jsonld
from gdsn_to_gs1_jsonld.readiness import (
    DPP_RELEVANCE_NOT_ASSESSED,
    READINESS_LEVELS,
    SCOPE_NOTE,
    assess_readiness,
)

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_XML = ROOT / "examples" / "input" / "example_product.xml"
MAPPING_REGISTRY = ROOT / "mapping" / "mapping_registry.yaml"
CODELIST_REGISTRY_JSON = (
    ROOT / "reference_data" / "normalized" / "gdsn_codelists_r3_1_36.json"
)


def _clean_inputs() -> dict:
    return {
        "validation_report": {"valid": True, "errors": [], "warnings": []},
        "mapping_report_rows": [{"found": True}, {"found": True}],
        "unmapped_fields": {"unmapped_elements": []},
        "codelist_validation": [
            {"canonical_field": "net_content_unit", "status": "valid"}
        ],
    }


def test_clean_conversion_is_structurally_ready():
    assessment = assess_readiness(**_clean_inputs())

    assert assessment["readiness_level"] == "structurally_ready"
    dims = assessment["dimensions"]
    assert dims["structural_validation"]["status"] == "passed"
    assert dims["mapping_coverage"]["status"] == "full_profile_coverage"
    assert dims["codelist_conformance"]["status"] == "all_valid"


def test_validation_errors_mean_review_required():
    inputs = _clean_inputs()
    inputs["validation_report"] = {
        "valid": False,
        "errors": ["gtin missing"],
        "warnings": [],
    }

    assessment = assess_readiness(**inputs)

    assert assessment["readiness_level"] == "review_required"
    assert assessment["dimensions"]["structural_validation"]["status"] == "errors"


def test_warnings_partial_coverage_or_codelist_issues_mean_attention_points():
    warn_inputs = _clean_inputs()
    warn_inputs["validation_report"]["warnings"] = ["deprecated term"]
    assert assess_readiness(**warn_inputs)["readiness_level"] == "attention_points"

    coverage_inputs = _clean_inputs()
    coverage_inputs["mapping_report_rows"] = [{"found": True}, {"found": False}]
    assert assess_readiness(**coverage_inputs)["readiness_level"] == "attention_points"

    codelist_inputs = _clean_inputs()
    codelist_inputs["codelist_validation"] = [
        {"canonical_field": "x", "status": "unknown"}
    ]
    assert assess_readiness(**codelist_inputs)["readiness_level"] == "attention_points"


def test_dpp_relevance_is_always_not_yet_assessed():
    """No fabricated DPP judgment: that dimension waits for the Crosswalk
    (v0.36.0+) and never affects the overall level."""
    clean = assess_readiness(**_clean_inputs())
    assert clean["dimensions"]["dpp_relevance"]["status"] == (
        DPP_RELEVANCE_NOT_ASSESSED
    )
    assert clean["readiness_level"] == "structurally_ready"


def test_no_codelist_registry_reports_not_evaluated_not_clean():
    inputs = _clean_inputs()
    inputs["codelist_validation"] = []

    assessment = assess_readiness(**inputs)

    assert assessment["dimensions"]["codelist_conformance"]["status"] == (
        "not_evaluated"
    )
    # not_evaluated is not an issue -- a clean rest still reads as ready.
    assert assessment["readiness_level"] == "structurally_ready"


def test_readiness_level_always_in_fixed_vocabulary_and_no_numeric_score():
    assessment = assess_readiness(**_clean_inputs())
    assert assessment["readiness_level"] in READINESS_LEVELS
    # Deliberately no single invented score anywhere in the payload.
    assert "score" not in assessment
    assert assessment["scope_note"] == SCOPE_NOTE


def test_scope_note_negates_every_restricted_claim_phrase():
    lowered = SCOPE_NOTE.lower()
    assert "not official gs1 validation" in lowered
    assert "no production compliance" in lowered


def test_real_fixture_assessment_matches_known_conversion_signals():
    """Cross-check against the example fixture's known values: 5 valid /
    2 unknown codelist entries (v0.20.0 baseline), so the level must be
    attention_points and every count must line up with the conversion."""
    registry = load_codelist_registry(CODELIST_REGISTRY_JSON)
    result = convert_xml_to_jsonld(
        EXAMPLE_XML.read_bytes(),
        MAPPING_REGISTRY,
        write_files=False,
        codelist_registry=registry,
    )

    assessment = assess_readiness(
        validation_report=result.validation_report,
        mapping_report_rows=result.mapping_report_rows,
        unmapped_fields=result.unmapped_fields,
        codelist_validation=result.codelist_validation,
    )

    codelist = assessment["dimensions"]["codelist_conformance"]
    assert codelist["counts"].get("valid") == 5
    assert codelist["counts"].get("unknown") == 2
    assert codelist["status"] == "issues_found"
    assert assessment["readiness_level"] == "attention_points"

    coverage = assessment["dimensions"]["mapping_coverage"]
    assert coverage["mapped_count"] == sum(
        1 for row in result.mapping_report_rows if row.get("found")
    )
    assert coverage["profile_row_count"] == len(result.mapping_report_rows)
    assert coverage["unmapped_source_element_count"] == len(
        result.unmapped_fields.get("unmapped_elements", [])
    )
