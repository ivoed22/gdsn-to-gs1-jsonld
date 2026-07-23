import json

from lxml import etree

from gdsn_to_gs1_jsonld.converter import convert_xml_to_jsonld
from gdsn_to_gs1_jsonld.mapping_loader import load_mapping


def test_v0_4_uses_only_review_safe_replacements():
    mapping = load_mapping("mapping/mapping_v0_4.yaml")
    objects = {item.id: item for item in mapping.object_mappings}

    assert "nutrients" not in objects
    assert objects["allergens"].fields[1].jsonld_property == (
        "gs1:allergenLevelOfContainmentCode"
    )
    assert objects["referenced_documents"].jsonld_property == "gs1:referencedFile"
    assert objects["referenced_documents"].object_type == "gs1:ReferencedFileDetails"


def test_unmapped_report_preserves_each_source_occurrence(tmp_path):
    xml = b"""<root>
      <gtin>08712345678906</gtin>
      <tradeItemDescription languageCode="en">Example</tradeItemDescription>
      <customField agency="GS1">first</customField>
      <customField agency="GS1">second</customField>
    </root>"""
    result = convert_xml_to_jsonld(xml, "mapping/mapping_v0_4.yaml")

    report = result.unmapped_fields
    assert report["report_version"] == "2.0"
    values = [
        item for item in report["unmapped_values"]
        if item["element"] == "customField"
    ]
    assert [item["value"] for item in values] == ["first", "second"]
    assert all(item["attributes"] == {"agency": "GS1"} for item in values)
    assert report["summary"]["unmapped_value_occurrences"] >= 2
    json.dumps(report)


def test_invalid_gtin_check_is_structured_and_value_is_not_emitted():
    xml = b"""<root>
      <gtin>08712345010326</gtin>
      <tradeItemDescription languageCode="nl">Test</tradeItemDescription>
    </root>"""
    result = convert_xml_to_jsonld(xml, "mapping/mapping_v0_4.yaml")

    assert "gs1:gtin" not in result.jsonld_data
    check = next(
        item for item in result.validation_report["checks"]
        if item["code"] == "GTIN_CHECK_DIGIT"
    )
    assert check["status"] == "error"
    assert check["source_value"] == "08712345010326"
    assert check["expected_check_digit"] == "4"
    assert check["candidate_corrected_gtin"] == "08712345010324"


def test_output_checks_cover_json_context_and_unmapped_evidence():
    xml = b"""<root>
      <gtin>08712345678906</gtin>
      <tradeItemDescription languageCode="en">Example</tradeItemDescription>
      <unknown>kept separately</unknown>
    </root>"""
    result = convert_xml_to_jsonld(xml, "mapping/mapping_v0_4.yaml")
    checks = {item["code"]: item for item in result.validation_report["checks"]}

    assert checks["JSON_SERIALIZATION"]["status"] == "passed"
    assert checks["GS1_CONTEXT"]["status"] == "passed"
    assert checks["UNMAPPED_SOURCE_EVIDENCE"]["count"] >= 1
    etree.fromstring(xml)
