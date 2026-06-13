from lxml import etree

from gdsn_to_gs1_jsonld.converter import convert_xml_to_jsonld


def test_required_missing_field_creates_error(example_xml_path, mapping_path):
    root = etree.parse(str(example_xml_path)).getroot()
    gtin = root.xpath(".//*[local-name()='gtin']")[0]
    gtin.getparent().remove(gtin)
    xml_without_gtin = etree.tostring(root)

    result = convert_xml_to_jsonld(xml_without_gtin, mapping_path)

    assert result.validation_report["valid"] is False
    assert result.validation_report["errors"] == [
        "Required field 'gtin' was not found. Cannot construct product @id."
    ]
    assert "@id" not in result.jsonld_data
