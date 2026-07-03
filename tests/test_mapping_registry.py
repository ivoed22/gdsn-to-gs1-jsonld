"""Consolidated mapping registry tests (v0.15.0 Track A).

The registry must be behaviorally identical to mapping_v0_3.yaml for the
converter (equivalence), expose the governance/catalog view, and enforce the
fixed status vocabulary.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from gdsn_to_gs1_jsonld.converter import convert_xml_to_jsonld
from gdsn_to_gs1_jsonld.mapping_loader import load_mapping
from gdsn_to_gs1_jsonld.mapping_registry import (
    MappingRegistryError,
    STATUS_VOCABULARY,
    load_registry,
    registry_catalog_rows,
    registry_field_governance,
    registry_summary,
)

REGISTRY_PATH = ROOT / "mapping" / "mapping_registry.yaml"
V0_3_PATH = ROOT / "mapping" / "mapping_v0_3.yaml"
EXAMPLE_XML = ROOT / "examples" / "input" / "example_product.xml"


def test_registry_file_exists_and_loads() -> None:
    registry = load_registry(REGISTRY_PATH)
    assert registry["metadata"]["registry_version"] == "1.0.0"
    assert "review-only" in registry["metadata"]["description"].lower()


def test_registry_executable_sections_identical_to_v0_3() -> None:
    """The converter-visible sections are structurally identical to v0_3."""
    registry_config = load_mapping(REGISTRY_PATH)
    v0_3_config = load_mapping(V0_3_PATH)
    assert registry_config.settings == v0_3_config.settings
    assert registry_config.fields == v0_3_config.fields
    assert registry_config.object_mappings == v0_3_config.object_mappings


def test_registry_conversion_output_identical_to_v0_3() -> None:
    """Converting the example XML with the registry produces byte-identical
    output to mapping_v0_3.yaml (no converter behavior change)."""
    xml_bytes = EXAMPLE_XML.read_bytes()
    result_v0_3 = convert_xml_to_jsonld(xml_bytes, V0_3_PATH, write_files=False)
    result_registry = convert_xml_to_jsonld(
        xml_bytes, REGISTRY_PATH, write_files=False
    )

    dump = lambda data: json.dumps(data, sort_keys=True, ensure_ascii=False)
    assert dump(result_registry.jsonld_data) == dump(result_v0_3.jsonld_data)
    assert result_registry.mapping_report_rows == result_v0_3.mapping_report_rows
    assert result_registry.validation_report == result_v0_3.validation_report
    assert result_registry.unmapped_fields == result_v0_3.unmapped_fields


def test_registry_catalog_view() -> None:
    registry = load_registry(REGISTRY_PATH)
    rows = registry_catalog_rows(registry)
    assert len(rows) == 29
    for row in rows:
        assert row["status"] in STATUS_VOCABULARY
        assert row["catalog_status"], row["canonical_field"]
        assert row["implemented"] is True
    # Original catalog review provenance is preserved verbatim.
    assert any(
        row["catalog_status"] == "needs_semantic_review" for row in rows
    )


def test_registry_governance_blocks_cover_all_fields() -> None:
    registry = load_registry(REGISTRY_PATH)
    governance = registry_field_governance(registry)
    summary = registry_summary(registry)
    assert summary["executable_total_fields"] == 28
    assert summary["catalog_rows"] == 29
    assert summary["catalog_by_status"]["accepted"] == 29
    # Every top-level field carries a governance block.
    for field in registry["fields"]:
        assert isinstance(field.get("governance"), dict), field["id"]
        assert field["governance"]["status"] in STATUS_VOCABULARY
    # Every nested object-mapping field carries a governance block.
    for obj in registry["object_mappings"]:
        for sub in obj["fields"]:
            assert isinstance(sub.get("governance"), dict), sub["id"]
    # Fields without a catalog row are conservatively flagged for review.
    issuance = governance["certifications[].certificate_issuance_date_time"]
    assert issuance["review_required"] is True
    assert issuance["catalog_status"] is None


def test_registry_status_vocabulary_enforced(tmp_path) -> None:
    registry = load_registry(REGISTRY_PATH)
    registry["catalog"][0]["status"] = "hard_mapping_candidate"
    bad_path = tmp_path / "bad_registry.yaml"
    bad_path.write_text(
        yaml.safe_dump(registry, sort_keys=False), encoding="utf-8"
    )
    with pytest.raises(MappingRegistryError, match="outside the fixed"):
        load_registry(bad_path)


def test_no_hard_mapping_candidate_status_anywhere() -> None:
    """hard_mapping is a flag concept (Track B), never a status value."""
    assert "hard_mapping_candidate" not in STATUS_VOCABULARY
    registry_text = REGISTRY_PATH.read_text(encoding="utf-8")
    assert "hard_mapping_candidate" not in registry_text


def test_generation_script_is_deterministic() -> None:
    """Re-running the build script yields the committed registry content."""
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        import build_mapping_registry
    finally:
        sys.path.pop(0)
    rebuilt = build_mapping_registry.build_registry()
    committed = load_registry(REGISTRY_PATH)
    assert rebuilt == committed
