import json
from pathlib import Path

from gdsn_to_gs1_jsonld.jsonld_builder import (
    PROTOTYPE_GOVERNANCE_WARNING,
    build_empty_builder_state,
    get_builder_fields,
    get_builder_groups,
    infer_input_type,
    jsonld_bytes,
    load_builder_manifest,
    serialize_builder_state_to_jsonld,
    update_builder_value,
    validate_builder_state,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "builder_manifest" / "product_builder_v0_10.yaml"


def _metadata() -> dict:
    return {
        "gs1:gtin": {
            "term_id": "gs1:gtin",
            "range": ["xsd:string"],
            "supported_in_v0_10": True,
        },
        "gs1:productName": {
            "term_id": "gs1:productName",
            "range": ["rdf:langString"],
            "supported_in_v0_10": True,
        },
        "gs1:productID": {
            "term_id": "gs1:productID",
            "range": ["xsd:string"],
            "supported_in_v0_10": True,
        },
        "gs1:relatedImage": {
            "term_id": "gs1:relatedImage",
            "range": ["xsd:anyURI"],
            "supported_in_v0_10": True,
        },
        "gs1:netContent": {
            "term_id": "gs1:netContent",
            "range": ["gs1:QuantitativeValue"],
            "supported_in_v0_10": True,
        },
        "gs1:isVariantOf": {
            "term_id": "gs1:isVariantOf",
            "range": ["xsd:boolean"],
            "supported_in_v0_10": True,
        },
        "gs1:certification": {
            "term_id": "gs1:certification",
            "range": ["gs1:CertificationDetails"],
            "supported_in_v0_10": False,
        },
    }


def test_load_builder_manifest_and_group_ordering():
    manifest = load_builder_manifest(MANIFEST)

    assert manifest["manifest_version"] == "0.10.0"
    assert manifest["root_classes"][0]["key"] == "Product"

    groups = get_builder_groups(manifest, "General Product")
    assert [group["key"] for group in groups][:3] == [
        "core_product_information",
        "classification_links",
        "physical_dimensions",
    ]

    fields = get_builder_fields(manifest, "core_product_information")
    assert [field["property_id"] for field in fields[:4]] == [
        "gs1:gtin",
        "gs1:productID",
        "gs1:productName",
        "gs1:additionalProductDescription",
    ]
    assert all("appears_because" in field for field in fields)


def test_empty_builder_state_defaults_to_product_root():
    state = build_empty_builder_state()

    assert state["root_class"] == "Product"
    assert state["product_category"] == "General Product"
    assert state["default_language"] == "en"
    assert state["selected_groups"] == ["core_product_information"]
    assert state["values"] == {}


def test_input_type_inference_from_ranges():
    assert infer_input_type({"term_id": "gs1:name", "range": ["xsd:string"]}) == "text"
    assert (
        infer_input_type({"term_id": "gs1:name", "range": ["rdf:langString"]})
        == "language_text"
    )
    assert infer_input_type({"term_id": "gs1:flag", "range": ["xsd:boolean"]}) == "checkbox"
    assert infer_input_type({"term_id": "gs1:count", "range": ["xsd:integer"]}) == "integer"
    assert infer_input_type({"term_id": "gs1:weight", "range": ["xsd:decimal"]}) == "quantity"
    assert infer_input_type({"term_id": "gs1:date", "range": ["xsd:date"]}) == "date"
    assert infer_input_type({"term_id": "gs1:url", "range": ["xsd:anyURI"]}) == "url"
    assert (
        infer_input_type({"term_id": "gs1:certification", "range": ["gs1:CertificationDetails"]})
        == "unsupported"
    )


def test_gtin_id_compact_properties_and_language_text_are_serialized():
    state = build_empty_builder_state()
    state = update_builder_value(state, "gs1:gtin", "09501234567890")
    state = update_builder_value(
        state,
        "gs1:productName",
        "Example apple juice",
        language="en",
    )
    state = update_builder_value(state, "gs1:productID", "SKU-123")

    data = serialize_builder_state_to_jsonld(state, _metadata())

    assert data["@context"][0] == "https://ref.gs1.org/voc/data/gs1Voc.jsonld"
    assert data["@type"] == "Product"
    assert data["@id"] == "https://id.gs1.org/01/09501234567890"
    assert data["gtin"] == "09501234567890"
    assert data["productID"] == "SKU-123"
    assert data["productName"] == [
        {"@language": "en", "@value": "Example apple juice"}
    ]
    assert "gs1:gtin" not in data


def test_boolean_url_quantity_empty_and_unsupported_behaviour():
    state = build_empty_builder_state()
    state = update_builder_value(state, "gs1:gtin", "09501234567890")
    state = update_builder_value(state, "gs1:relatedImage", "https://example.com/p.jpg")
    state = update_builder_value(
        state,
        "gs1:netContent",
        "1.5",
        unit_code="LTR",
    )
    state = update_builder_value(state, "gs1:isVariantOf", True)
    state = update_builder_value(state, "gs1:productID", "")
    state = update_builder_value(state, "gs1:certification", "EU Organic")

    data = serialize_builder_state_to_jsonld(state, _metadata())

    assert data["relatedImage"] == "https://example.com/p.jpg"
    assert data["netContent"] == {"value": 1.5, "unitCode": "LTR"}
    assert data["isVariantOf"] is True
    assert "productID" not in data
    assert "certification" not in data


def test_validation_warnings_cover_prototype_url_language_quantity_and_unsupported():
    state = build_empty_builder_state()
    state = update_builder_value(state, "gs1:relatedImage", "not-a-url")
    state = update_builder_value(state, "gs1:productName", "No language")
    state = update_builder_value(state, "gs1:netContent", "1.5")
    state = update_builder_value(state, "gs1:certification", "EU Organic")

    warnings = validate_builder_state(state, _metadata())

    assert PROTOTYPE_GOVERNANCE_WARNING in warnings
    assert any("Missing GTIN" in warning for warning in warnings)
    assert any("not a valid HTTP(S) URL" in warning for warning in warnings)
    assert any("needs a language tag" in warning for warning in warnings)
    assert any("quantity value without unitCode" in warning for warning in warnings)
    assert any("not supported in v0.10" in warning for warning in warnings)
    assert any("unsupported nested or complex range" in warning for warning in warnings)

    unit_only_state = update_builder_value(
        build_empty_builder_state(),
        "gs1:netContent",
        "",
        unit_code="LTR",
    )
    unit_only_warnings = validate_builder_state(unit_only_state, _metadata())
    assert any("unitCode without a quantity value" in warning for warning in unit_only_warnings)


def test_invalid_gtin_and_deterministic_jsonld_bytes():
    state = update_builder_value(
        build_empty_builder_state(),
        "gs1:gtin",
        "09501234567892",
    )
    data = serialize_builder_state_to_jsonld(state, _metadata())
    warnings = validate_builder_state(state, _metadata())
    encoded = jsonld_bytes(data)

    assert any("Invalid GTIN" in warning for warning in warnings)
    assert encoded == json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8") + b"\n"
    assert jsonld_bytes(data) == encoded
