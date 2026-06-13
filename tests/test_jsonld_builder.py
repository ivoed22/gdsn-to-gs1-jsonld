import json

from gdsn_to_gs1_jsonld.converter import convert_xml_to_jsonld


def test_jsonld_contains_digital_link_id(example_xml_path, mapping_path):
    result = convert_xml_to_jsonld(example_xml_path, mapping_path)
    assert result.jsonld_data["@id"] == "https://id.gs1.org/01/08712345678906"


def test_jsonld_preserves_gtin_leading_zero(example_xml_path, mapping_path):
    result = convert_xml_to_jsonld(example_xml_path, mapping_path)
    assert result.jsonld_data["gs1:gtin"] == "08712345678906"
    serialized = json.dumps(result.jsonld_data)
    assert '"gs1:gtin": "08712345678906"' in serialized


def test_jsonld_matches_expected_example(example_xml_path, mapping_path):
    result = convert_xml_to_jsonld(example_xml_path, mapping_path)
    expected_path = example_xml_path.parents[1] / "output" / "expected_product.jsonld"
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    assert result.jsonld_data == expected
