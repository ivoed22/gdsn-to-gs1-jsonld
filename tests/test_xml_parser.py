from lxml import etree

from gdsn_to_gs1_jsonld.converter import convert_xml_to_jsonld
from gdsn_to_gs1_jsonld.xml_parser import parse_xml


def test_xml_parser_reads_example_xml(example_xml_path):
    root = parse_xml(example_xml_path)
    assert etree.QName(root).localname == "catalogueItemNotificationMessage"


def test_gtin_is_extracted(example_xml_path, mapping_path):
    result = convert_xml_to_jsonld(example_xml_path, mapping_path)
    assert result.canonical_product.gtin == "08712345678906"


def test_product_names_are_extracted(example_xml_path, mapping_path):
    result = convert_xml_to_jsonld(example_xml_path, mapping_path)
    names = {
        item.language: item.value for item in result.canonical_product.product_name
    }
    assert names == {
        "en": "Organic Apple Juice 500 ml",
        "nl": "Biologisch Appelsap 500 ml",
    }


def test_unmapped_fields_include_out_of_scope_elements(
    example_xml_path,
    mapping_path,
):
    result = convert_xml_to_jsonld(example_xml_path, mapping_path)
    names = {
        item["element"] for item in result.unmapped_fields["unmapped_elements"]
    }
    assert {
        "ingredientStatement",
        "allergenRelatedInformation",
        "allergenTypeCode",
        "levelOfContainmentCode",
        "nutrientHeader",
        "nutrientTypeCode",
        "preparationStateCode",
    } <= names
    assert {
        "netContent",
    }.isdisjoint(names)

    nutrient_measurements = [
        item
        for item in result.unmapped_fields["unmapped_elements"]
        if item["element"] in {"measurementValue", "measurementUnitCode"}
    ]
    assert {item["element"] for item in nutrient_measurements} == {
        "measurementValue",
        "measurementUnitCode",
    }
    assert all(item["parent"] == "quantityContained" for item in nutrient_measurements)
    assert all(
        "/nutrientHeader/nutrientDetail/quantityContained/" in item["path"]
        for item in nutrient_measurements
    )

    assert all(
        {"element", "parent", "path", "count"} <= item.keys()
        for item in result.unmapped_fields["unmapped_elements"]
    )


def test_v0_2_unmapped_fields_exclude_food_mappings(
    example_xml_path,
    mapping_v0_2_path,
):
    result = convert_xml_to_jsonld(example_xml_path, mapping_v0_2_path)
    names = {
        item["element"] for item in result.unmapped_fields["unmapped_elements"]
    }
    assert {
        "ingredientStatement",
        "allergenRelatedInformation",
        "allergen",
        "allergenTypeCode",
        "levelOfContainmentCode",
        "nutrientHeader",
        "nutrientDetail",
        "nutrientTypeCode",
        "preparationStateCode",
        "quantityContained",
        "measurementValue",
        "measurementUnitCode",
    }.isdisjoint(names)
    assert {"gln", "partyName", "fileName", "fileFormatName"} <= names


def test_v0_3_unmapped_fields_exclude_certification_and_documents(
    example_xml_path,
    mapping_v0_3_path,
):
    result = convert_xml_to_jsonld(example_xml_path, mapping_v0_3_path)
    items = result.unmapped_fields["unmapped_elements"]
    mapped_names = {
        "certificationInformation",
        "certification",
        "certificationStandard",
        "certificationIdentification",
        "certificationValue",
        "certificateIssuanceDateTime",
        "certificationAssessmentDateTime",
        "certificationEffectiveStartDateTime",
        "certificationEffectiveEndDateTime",
        "certificationOrganisationIdentifier",
    }
    assert mapped_names.isdisjoint({item["element"] for item in items})
    assert not any("/certificationInformation/" in item["path"] for item in items)
    referenced_file_items = [
        item
        for item in items
        if item["element"]
        in {"fileName", "fileFormatName", "referencedFileTypeCode"}
    ]
    assert len(referenced_file_items) == 6
    assert all(item["count"] == 1 for item in referenced_file_items)
    assert {
        item["context"]["referencedFileTypeCode"]
        for item in referenced_file_items
    } == {"PRODUCT_IMAGE"}
    assert {
        item["context"]["fileName"] for item in referenced_file_items
    } == {"front-packshot.jpg", "back-label.jpg"}
    assert all(
        item["context"]["uniformResourceIdentifier"].startswith(
            "https://example.com/images/"
        )
        for item in referenced_file_items
    )
    assert not any(
        item.get("context", {}).get("referencedFileTypeCode")
        in {"DPP_DOCUMENT", "CERTIFICATION_DOCUMENT"}
        for item in items
    )
    assert not any(
        item["element"] == "uniformResourceIdentifier" for item in items
    )
