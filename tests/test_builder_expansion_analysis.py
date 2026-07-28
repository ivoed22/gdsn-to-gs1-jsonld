"""Tests for the Builder Manifest Expansion Analysis (Track C, v0.19.0).

Read-only analysis: must never write to the builder manifest, must never
fabricate a "not_yet_assessed" DPP relevance verdict, and must classify
properties deterministically from the mapping registry's governance catalog
plus Track B's hard-mapping detection.
"""

from __future__ import annotations

from pathlib import Path

from gdsn_to_gs1_jsonld.builder_expansion_analysis import (
    DPP_RELEVANCE_NOT_ASSESSED,
    READINESS_PHASES,
    authored_property_ids,
    build_expansion_analysis,
    load_catalog_rows_from_registry,
    write_expansion_analysis,
)
from gdsn_to_gs1_jsonld.jsonld_builder import load_builder_manifest
from gdsn_to_gs1_jsonld.mapping_candidate_generator import load_webvoc_properties

ROOT = Path(__file__).resolve().parents[1]
WEBVOC_CSV = ROOT / "reference_data" / "normalized" / "webvoc_properties_1_18.csv"
GDSN_CSV = ROOT / "reference_data" / "normalized" / "gdsn_attributes_bms_xpath_3_1_36.csv"
BUILDER_MANIFEST = ROOT / "builder_manifest" / "product_builder_v0_10.yaml"
MAPPING_REGISTRY = ROOT / "mapping" / "mapping_registry.yaml"


def _real_analysis():
    webvoc_rows = load_webvoc_properties(str(WEBVOC_CSV))
    manifest = load_builder_manifest(str(BUILDER_MANIFEST))
    catalog_rows = load_catalog_rows_from_registry(str(MAPPING_REGISTRY))
    return build_expansion_analysis(webvoc_rows, manifest, catalog_rows, str(GDSN_CSV))


def test_authored_property_ids_matches_known_manifest_size():
    manifest = load_builder_manifest(str(BUILDER_MANIFEST))
    authored = authored_property_ids(manifest)
    assert len(authored) == 183


def test_readiness_phase_vocabulary_fixed():
    assert READINESS_PHASES == (
        "ready_now",
        "needs_codelist_curation",
        "needs_hard_mapping_review",
        "not_ready_no_evidence",
    )


def test_analysis_excludes_already_authored_properties():
    analysis = _real_analysis()
    manifest = load_builder_manifest(str(BUILDER_MANIFEST))
    authored = authored_property_ids(manifest)
    candidate_ids = {c["term_id"] for c in analysis["candidates"]}
    assert candidate_ids.isdisjoint(authored)


def test_analysis_counts_are_internally_consistent():
    analysis = _real_analysis()
    # One authored manifest field (gs1:nutrientDetail) is a documented
    # placeholder not present in the current WebVoc snapshot (supported_in_
    # v0_10: false; see docs/manual-jsonld-builder.md), so authored + not-yet
    # sums to one more than the WebVoc total rather than matching exactly.
    manifest = load_builder_manifest(str(BUILDER_MANIFEST))
    authored = authored_property_ids(manifest)
    webvoc_rows = load_webvoc_properties(str(WEBVOC_CSV))
    webvoc_ids = {row["term_id"] for row in webvoc_rows if row.get("term_id")}
    authored_outside_webvoc = authored - webvoc_ids
    assert (
        analysis["authored_property_count"]
        + analysis["not_yet_authorable_count"]
        - len(authored_outside_webvoc)
        == analysis["total_webvoc_property_count"]
    )
    assert len(analysis["candidates"]) == analysis["not_yet_authorable_count"]
    assert sum(analysis["by_readiness_phase"].values()) == analysis["not_yet_authorable_count"]


def test_no_evidence_properties_are_not_ready():
    analysis = _real_analysis()
    for candidate in analysis["candidates"]:
        if not candidate["source_mapping_status"]:
            assert candidate["readiness_phase"] == "not_ready_no_evidence"


def test_ready_now_candidates_have_evidence_and_no_flags():
    analysis = _real_analysis()
    ready_now = [c for c in analysis["candidates"] if c["readiness_phase"] == "ready_now"]
    assert ready_now, "expected at least one ready_now candidate on real data"
    for candidate in ready_now:
        assert candidate["source_mapping_status"]
        assert candidate["codelist_dependency"] is False
        assert candidate["hard_mapping_dependency"] is False


def test_dpp_relevance_never_fabricated():
    """Every candidate reports the same not-yet-assessed marker: DPP
    relevance is the Crosswalk's job (not built), never invented here."""
    analysis = _real_analysis()
    assert analysis["candidates"], "expected at least one candidate"
    for candidate in analysis["candidates"]:
        assert candidate["dpp_relevance"] == DPP_RELEVANCE_NOT_ASSESSED


def test_candidates_sorted_ready_now_first():
    analysis = _real_analysis()
    phases = [c["readiness_phase"] for c in analysis["candidates"]]
    first_non_ready = next(
        (i for i, phase in enumerate(phases) if phase != "ready_now"), len(phases)
    )
    assert all(phase == "ready_now" for phase in phases[:first_non_ready])
    assert all(phase != "ready_now" for phase in phases[first_non_ready:])


def test_write_expansion_analysis_never_touches_builder_manifest(tmp_path):
    analysis = _real_analysis()
    before = BUILDER_MANIFEST.read_bytes()
    paths = write_expansion_analysis(analysis, tmp_path)
    after = BUILDER_MANIFEST.read_bytes()
    assert before == after
    assert Path(paths["json"]).is_file()
