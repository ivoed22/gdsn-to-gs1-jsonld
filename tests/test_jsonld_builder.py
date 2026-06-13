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


def test_v0_2_jsonld_matches_expected_example(
    example_xml_path,
    mapping_v0_2_path,
):
    result = convert_xml_to_jsonld(example_xml_path, mapping_v0_2_path)
    expected_path = (
        example_xml_path.parents[1] / "output" / "expected_product_v0_2.jsonld"
    )
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    assert result.jsonld_data == expected


def test_v0_2_ingredient_statements_are_multilingual(
    example_xml_path,
    mapping_v0_2_path,
):
    result = convert_xml_to_jsonld(example_xml_path, mapping_v0_2_path)
    assert result.jsonld_data["gs1:ingredientStatement"] == [
        {"@value": "Apple juice from concentrate.", "@language": "en"},
        {"@value": "Appelsap uit concentraat.", "@language": "nl"},
    ]


def test_v0_2_allergen_details_are_mapped(
    example_xml_path,
    mapping_v0_2_path,
):
    result = convert_xml_to_jsonld(example_xml_path, mapping_v0_2_path)
    assert result.jsonld_data["gs1:hasAllergen"] == [
        {
            "@type": "gs1:AllergenDetails",
            "gs1:allergenType": "AM",
            "gs1:levelOfContainment": "FREE_FROM",
        }
    ]


def test_v0_2_nutrient_details_are_mapped(
    example_xml_path,
    mapping_v0_2_path,
):
    result = convert_xml_to_jsonld(example_xml_path, mapping_v0_2_path)
    assert result.jsonld_data["gs1:nutrientDetail"] == [
        {
            "gs1:preparationStateCode": "UNPREPARED",
            "gs1:nutrientTypeCode": "ENER-",
            "gs1:quantityContained": {"value": 190, "unitCode": "KJO"},
        }
    ]


def test_v0_3_jsonld_matches_expected_example(
    example_xml_path,
    mapping_v0_3_path,
):
    result = convert_xml_to_jsonld(example_xml_path, mapping_v0_3_path)
    expected_path = (
        example_xml_path.parents[1] / "output" / "expected_product_v0_3.jsonld"
    )
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    assert result.jsonld_data == expected


def test_v0_3_certification_is_mapped(
    example_xml_path,
    mapping_v0_3_path,
):
    result = convert_xml_to_jsonld(example_xml_path, mapping_v0_3_path)
    certification = result.jsonld_data["gs1:certification"][0]
    assert certification["@type"] == "gs1:CertificationDetails"
    assert certification["gs1:certificationStandard"] == "EU Organic"
    assert certification["schema:identifier"] == "CERT-08712345678906-ORG"
    assert certification["gs1:certificationValue"] == "Certified organic product"


def test_v0_3_referenced_documents_are_mapped(
    example_xml_path,
    mapping_v0_3_path,
):
    result = convert_xml_to_jsonld(example_xml_path, mapping_v0_3_path)
    documents = result.jsonld_data["gs1:referencedDocument"]
    assert {item["schema:additionalType"] for item in documents} == {
        "DPP_DOCUMENT",
        "CERTIFICATION_DOCUMENT",
    }
    assert {item["schema:url"] for item in documents} == {
        "https://example.com/documents/08712345678906-dpp.pdf",
        "https://example.com/documents/08712345678906-organic-certificate.pdf",
    }
