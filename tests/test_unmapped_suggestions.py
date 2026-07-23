from pathlib import Path

import pytest

from gdsn_to_gs1_jsonld.converter import convert_xml_to_jsonld
from gdsn_to_gs1_jsonld.unmapped_suggestions import (
    MappingSuggestionCatalogError,
    add_mapping_suggestions,
    load_mapping_suggestion_catalog,
)


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = (
    ROOT / "mapping_catalog" / "unmapped_gdsn_webvoc_suggestions_v0_1.csv"
)


def test_committed_suggestion_catalog_is_review_only_and_60_percent_plus():
    catalog = load_mapping_suggestion_catalog(CATALOG_PATH)

    assert len(catalog) == 288
    assert all(item["match_percentage"] >= 60 for item in catalog)
    assert all(item["auto_emit"] is False for item in catalog)
    assert all(item.get("review_consensus_status") for item in catalog)
    assert any(
        item["gdsn_attribute_name"] == "consumerStorageInstructions"
        and item["proposed_webvoc_property"]
        == "gs1:consumerStorageInstructions"
        and item["match_percentage"] == 100
        for item in catalog
    )


def test_catalog_refuses_auto_emit_rows(tmp_path):
    catalog_path = tmp_path / "unsafe.csv"
    catalog_path.write_text(
        "gdsn_attribute_name,proposed_webvoc_property,match_percentage,"
        "suggestion_status,auto_emit\n"
        "consumerStorageInstructions,gs1:consumerStorageInstructions,100,"
        "strong_candidate,true\n",
        encoding="utf-8",
    )

    with pytest.raises(MappingSuggestionCatalogError, match="auto_emit=false"):
        load_mapping_suggestion_catalog(catalog_path)


def test_add_mapping_suggestions_only_for_elements_present_in_upload():
    report = {
        "summary": {
            "unmapped_value_occurrences": 1,
            "unmapped_element_groups": 1,
        },
        "unmapped_elements": [
            {"element": "consumerStorageInstructions", "count": 1}
        ],
        "unmapped_values": [
            {
                "element": "consumerStorageInstructions",
                "value": "Keep cool",
            }
        ],
    }
    catalog = load_mapping_suggestion_catalog(CATALOG_PATH)

    enriched = add_mapping_suggestions(report, catalog)

    suggestions = enriched["mapping_suggestions"]
    assert suggestions
    assert {item["source_element"] for item in suggestions} == {
        "consumerStorageInstructions"
    }
    assert suggestions[0]["proposed_webvoc_property"] == (
        "gs1:consumerStorageInstructions"
    )
    assert suggestions[0]["auto_emitted"] is False
    assert enriched["summary"]["mapping_suggestion_source_elements"] == 1


def test_compound_gdsn_paths_are_not_matched_from_bare_terminal_name():
    report = {
        "summary": {},
        "unmapped_elements": [{"element": "measurementUnitCode", "count": 1}],
        "unmapped_values": [],
    }
    catalog = [
        {
            "source_local_name": "",
            "gdsn_attribute_name": "netContent/@measurementUnitCode",
            "proposed_webvoc_property": "gs1:unitCode",
            "match_percentage": 70.0,
            "suggestion_status": "review_candidate",
        }
    ]

    enriched = add_mapping_suggestions(report, catalog)

    assert enriched["mapping_suggestions"] == []


def test_converter_suggests_but_does_not_emit_candidate_property():
    xml = b"""<root>
      <gtin>08712345678906</gtin>
      <tradeItemDescription languageCode="en">Example</tradeItemDescription>
      <consumerStorageInstructions languageCode="en">Keep cool</consumerStorageInstructions>
    </root>"""
    catalog = load_mapping_suggestion_catalog(CATALOG_PATH)

    result = convert_xml_to_jsonld(
        xml,
        ROOT / "mapping" / "mapping_v0_4.yaml",
        mapping_suggestion_catalog=catalog,
    )

    assert "gs1:consumerStorageInstructions" not in result.jsonld_data
    suggestion = next(
        item
        for item in result.unmapped_fields["mapping_suggestions"]
        if item["source_element"] == "consumerStorageInstructions"
    )
    assert suggestion["match_percentage"] == 100
    assert suggestion["review_required"] is True
    assert suggestion["review_consensus_status"] in {
        "unanimous_accept",
        "strong_accept_consensus",
        "accept_consensus",
        "conflicted",
        "human_review",
    }
