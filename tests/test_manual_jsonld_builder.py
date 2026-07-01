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
    object_subfield_key,
    serialize_builder_state_to_jsonld,
    update_builder_value,
    validate_builder_state,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "builder_manifest" / "product_builder_v0_10.yaml"


def test_manifest_breadth_expansion_groups_and_fields():
    """v0.13.x breadth expansion: new simple-range Product groups are present,
    wired into categories, and their fields serialize safely."""
    manifest = load_builder_manifest(str(MANIFEST))
    group_keys = {group["key"] for group in manifest["groups"]}
    for key in (
        "product_descriptions",
        "consumer_information",
        "dates_lifecycle",
        "consumer_dpp_links",
    ):
        assert key in group_keys, f"missing new group: {key}"

    general_group_keys = [g["key"] for g in get_builder_groups(manifest, "General Product")]
    # Existing first three groups keep their order (builder test contract).
    assert general_group_keys[:3] == [
        "core_product_information",
        "classification_links",
        "physical_dimensions",
    ]
    assert "product_descriptions" in general_group_keys
    assert "consumer_dpp_links" in general_group_keys

    # Every new field is flagged supported and carries an input_type_override.
    new_fields = [
        field
        for group in manifest["groups"]
        if group["key"] in {
            "product_descriptions",
            "consumer_information",
            "dates_lifecycle",
            "consumer_dpp_links",
        }
        for field in group["properties"]
    ]
    assert len(new_fields) >= 40
    for field in new_fields:
        assert field.get("supported_in_v0_10") is True
        assert field.get("input_type_override")

    # A representative subset serializes to safe prototype JSON-LD.
    metadata = {
        "gs1:gtin": {"term_id": "gs1:gtin", "range": ["xsd:string"], "input_type_override": "text"},
        "gs1:productDescription": {"term_id": "gs1:productDescription", "range": ["rdf:langString"], "input_type_override": "language_text"},
        "gs1:bestBeforeDate": {"term_id": "gs1:bestBeforeDate", "range": ["xsd:date"], "input_type_override": "date"},
        "gs1:isProductRecalled": {"term_id": "gs1:isProductRecalled", "range": ["xsd:boolean"], "input_type_override": "checkbox"},
        "gs1:eifu": {"term_id": "gs1:eifu", "range": ["xsd:anyURI"], "input_type_override": "url"},
    }
    state = build_empty_builder_state()
    state = update_builder_value(state, "gs1:gtin", "09501234567890")
    state = update_builder_value(state, "gs1:productDescription", "Apple juice 1L", language="en")
    state = update_builder_value(state, "gs1:bestBeforeDate", "2026-12-31")
    state = update_builder_value(state, "gs1:isProductRecalled", True)
    state = update_builder_value(state, "gs1:eifu", "https://example.com/eifu/1")

    data = serialize_builder_state_to_jsonld(state, metadata)
    assert data["productDescription"] == [{"@language": "en", "@value": "Apple juice 1L"}]
    assert data["bestBeforeDate"] == "2026-12-31"
    assert data["isProductRecalled"] is True
    assert data["eifu"] == "https://example.com/eifu/1"


def test_manifest_nested_object_fields_present():
    """Depth track: brand, image, certification, packaging material, and
    referenced-file are now nested-object fields with safe sub-fields."""
    manifest = load_builder_manifest(str(MANIFEST))
    objects = {
        field["property_id"]: field
        for group in manifest["groups"]
        for field in group["properties"]
        if field.get("input_type_override") == "object"
    }
    for pid, otype in [
        ("gs1:brand", "gs1:Brand"),
        ("gs1:image", "gs1:ReferencedFileDetails"),
        ("gs1:certification", "gs1:CertificationDetails"),
        ("gs1:packagingMaterial", "gs1:PackagingMaterial"),
        ("gs1:referencedFile", "gs1:ReferencedFileDetails"),
    ]:
        assert pid in objects, f"missing object field: {pid}"
        field = objects[pid]
        assert field["object_type"] == otype
        assert field.get("supported_in_v0_10") is True
        assert field.get("object_fields")
        for sub in field["object_fields"]:
            assert sub.get("property_id")
            assert sub.get("input_type_override")


def test_nested_object_serialization_and_omission():
    metadata = {
        "gs1:gtin": {"term_id": "gs1:gtin", "range": ["xsd:string"], "input_type_override": "text", "supported_in_v0_10": True},
        "gs1:brand": {"term_id": "gs1:brand", "input_type_override": "object", "object_type": "gs1:Brand", "supported_in_v0_10": True,
            "object_fields": [{"property_id": "gs1:brandName", "input_type_override": "language_text"}]},
        "gs1:certification": {"term_id": "gs1:certification", "input_type_override": "object", "object_type": "gs1:CertificationDetails", "supported_in_v0_10": True,
            "object_fields": [
                {"property_id": "gs1:certificationStandard", "input_type_override": "language_text"},
                {"property_id": "gs1:certificationURI", "input_type_override": "url"},
                {"property_id": "gs1:certificationStartDate", "input_type_override": "date"},
            ]},
    }
    state = build_empty_builder_state()
    state = update_builder_value(state, "gs1:gtin", "09501234567890")
    state = update_builder_value(state, object_subfield_key("gs1:brand", "gs1:brandName"), "Example Brand", language="en")
    state = update_builder_value(state, object_subfield_key("gs1:certification", "gs1:certificationStandard"), "EU Organic", language="en")
    state = update_builder_value(state, object_subfield_key("gs1:certification", "gs1:certificationURI"), "https://example.com/cert/1")
    state = update_builder_value(state, object_subfield_key("gs1:certification", "gs1:certificationStartDate"), "2026-01-01")

    data = serialize_builder_state_to_jsonld(state, metadata)
    assert data["brand"] == {
        "@type": "gs1:Brand",
        "brandName": [{"@language": "en", "@value": "Example Brand"}],
    }
    cert = data["certification"]
    assert cert["@type"] == "gs1:CertificationDetails"
    assert cert["certificationStandard"] == [{"@language": "en", "@value": "EU Organic"}]
    assert cert["certificationURI"] == "https://example.com/cert/1"
    assert cert["certificationStartDate"] == "2026-01-01"

    # An object with no sub-values is omitted entirely.
    empty = build_empty_builder_state()
    empty = update_builder_value(empty, "gs1:gtin", "09501234567890")
    data2 = serialize_builder_state_to_jsonld(empty, metadata)
    assert "brand" not in data2
    assert "certification" not in data2

    # An invalid sub-field URL produces a targeted validation warning.
    bad = build_empty_builder_state()
    bad = update_builder_value(bad, object_subfield_key("gs1:certification", "gs1:certificationURI"), "not-a-url")
    warnings = validate_builder_state(bad, metadata)
    assert any("certificationURI" in warning for warning in warnings)


def test_allergen_code_object_serialization():
    """Allergen is a nested AllergenDetails object with GS1 code-list values
    emitted as JSON-LD node references."""
    manifest = load_builder_manifest(str(MANIFEST))
    allergen = next(
        field
        for group in manifest["groups"]
        for field in group["properties"]
        if field["property_id"] == "gs1:hasAllergen"
    )
    assert allergen["input_type_override"] == "object"
    assert allergen["object_type"] == "gs1:AllergenDetails"
    subs = {sub["property_id"]: sub for sub in allergen["object_fields"]}
    assert subs["gs1:allergenType"]["input_type_override"] == "code"
    assert any(
        opt["value"] == "gs1:AllergenTypeCode-AM"
        for opt in subs["gs1:allergenType"]["options"]
    )
    assert subs["gs1:allergenLevelOfContainmentCode"]["input_type_override"] == "code"

    metadata = {
        "gs1:hasAllergen": {"term_id": "gs1:hasAllergen", "input_type_override": "object", "object_type": "gs1:AllergenDetails", "supported_in_v0_10": True,
            "object_fields": [
                {"property_id": "gs1:allergenType", "input_type_override": "code"},
                {"property_id": "gs1:allergenLevelOfContainmentCode", "input_type_override": "code"},
            ]},
    }
    state = build_empty_builder_state()
    state = update_builder_value(state, object_subfield_key("gs1:hasAllergen", "gs1:allergenType"), "gs1:AllergenTypeCode-AM")
    state = update_builder_value(state, object_subfield_key("gs1:hasAllergen", "gs1:allergenLevelOfContainmentCode"), "gs1:LevelOfContainmentCode-CONTAINS")

    data = serialize_builder_state_to_jsonld(state, metadata)
    assert data["hasAllergen"] == {
        "@type": "gs1:AllergenDetails",
        "allergenType": {"@id": "gs1:AllergenTypeCode-AM"},
        "allergenLevelOfContainmentCode": {"@id": "gs1:LevelOfContainmentCode-CONTAINS"},
    }

    empty = build_empty_builder_state()
    assert "hasAllergen" not in serialize_builder_state_to_jsonld(empty, metadata)


def test_nutrition_group_and_nutrient_serialization():
    """Per-nutrient values are mapped as quantity fields (value + unitCode) in a
    Nutrition group wired into the Food/Beverage/Tobacco category."""
    manifest = load_builder_manifest(str(MANIFEST))
    nutrition = next((g for g in manifest["groups"] if g["key"] == "nutrition"), None)
    assert nutrition is not None
    pids = {p["property_id"] for p in nutrition["properties"]}
    for pid in (
        "gs1:nutrientBasisQuantity",
        "gs1:energyPerNutrientBasis",
        "gs1:fatPerNutrientBasis",
        "gs1:saturatedFatPerNutrientBasis",
        "gs1:sugarsPerNutrientBasis",
        "gs1:proteinPerNutrientBasis",
        "gs1:saltPerNutrientBasis",
    ):
        assert pid in pids, f"missing nutrient field: {pid}"
    assert len([p for p in nutrition["properties"] if p["property_id"].endswith("PerNutrientBasis")]) >= 40

    food_groups = [g["key"] for g in get_builder_groups(manifest, "Food / Beverage / Tobacco")]
    assert "nutrition" in food_groups

    metadata = {
        "gs1:fatPerNutrientBasis": {"term_id": "gs1:fatPerNutrientBasis", "input_type_override": "quantity", "supported_in_v0_10": True},
    }
    state = build_empty_builder_state()
    state = update_builder_value(state, "gs1:fatPerNutrientBasis", "3.5", unit_code="GRM")
    data = serialize_builder_state_to_jsonld(state, metadata)
    assert data["fatPerNutrientBasis"]["unitCode"] == "GRM"
    assert "value" in data["fatPerNutrientBasis"]


def test_food_coding_code_lists_and_serialization():
    """Food controlled-code attributes are code-list fields sourced from the
    snapshot and emitted as node references."""
    manifest = load_builder_manifest(str(MANIFEST))
    food_coding = next((g for g in manifest["groups"] if g["key"] == "food_coding"), None)
    assert food_coding is not None
    fields = {p["property_id"]: p for p in food_coding["properties"]}
    for pid in (
        "gs1:nutritionalClaim",
        "gs1:preservationTechnique",
        "gs1:growingMethod",
        "gs1:sourceAnimal",
        "gs1:foodBeverageTargetUse",
    ):
        assert pid in fields, f"missing code field: {pid}"
        assert fields[pid]["input_type_override"] == "code"
        assert fields[pid]["options"]
        for opt in fields[pid]["options"]:
            assert opt["value"].startswith("gs1:")
            assert opt["label"]

    food_groups = [g["key"] for g in get_builder_groups(manifest, "Food / Beverage / Tobacco")]
    assert "food_coding" in food_groups

    code = fields["gs1:nutritionalClaim"]["options"][0]["value"]
    metadata = {
        "gs1:nutritionalClaim": {"term_id": "gs1:nutritionalClaim", "input_type_override": "code", "supported_in_v0_10": True},
    }
    state = build_empty_builder_state()
    state = update_builder_value(state, "gs1:nutritionalClaim", code)
    data = serialize_builder_state_to_jsonld(state, metadata)
    assert data["nutritionalClaim"] == {"@id": code}


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


def test_context_is_present_in_all_serialized_states():
    """@context must be present in every Builder output, even empty state."""
    empty_state = build_empty_builder_state()
    data = serialize_builder_state_to_jsonld(empty_state, _metadata())
    assert "@context" in data
    assert data["@context"][0] == "https://ref.gs1.org/voc/data/gs1Voc.jsonld"

    # Also with a GTIN present.
    state = update_builder_value(empty_state, "gs1:gtin", "09501234567890")
    data = serialize_builder_state_to_jsonld(state, _metadata())
    assert "@context" in data
    assert data["@context"][0] == "https://ref.gs1.org/voc/data/gs1Voc.jsonld"


def test_field_persistence_across_group_switches():
    """Values from one group must survive when state is re-used across groups."""
    state = build_empty_builder_state()
    state = update_builder_value(state, "gs1:gtin", "09501234567890")
    state = update_builder_value(state, "gs1:productName", "Apple juice", language="en")

    # Simulate switching to Physical Dimensions group; add a quantity field.
    state["selected_groups"] = ["physical_dimensions"]
    state = update_builder_value(state, "gs1:netContent", "1.5", unit_code="LTR")

    # The GTIN and productName values from the core group must still be present.
    assert state["values"]["gs1:gtin"]["value"] == "09501234567890"
    assert state["values"]["gs1:productName"]["value"] == "Apple juice"
    assert state["values"]["gs1:netContent"]["value"] == "1.5"

    # Serialized JSON-LD must contain all three across group boundary.
    data = serialize_builder_state_to_jsonld(state, _metadata())
    assert data.get("gtin") == "09501234567890"
    assert "productName" in data
    assert "netContent" in data


def test_clearing_a_field_removes_it_from_jsonld():
    """Setting a value to empty must remove it from the serialized output."""
    state = build_empty_builder_state()
    state = update_builder_value(state, "gs1:gtin", "09501234567890")
    state = update_builder_value(state, "gs1:productID", "SKU-123")
    data = serialize_builder_state_to_jsonld(state, _metadata())
    assert data.get("productID") == "SKU-123"

    # Now clear the productID field.
    state = update_builder_value(state, "gs1:productID", "")
    data_after_clear = serialize_builder_state_to_jsonld(state, _metadata())
    assert "productID" not in data_after_clear
    # GTIN must still be present.
    assert data_after_clear.get("gtin") == "09501234567890"


def test_reset_clears_all_builder_values():
    """Empty builder state must have no values and reset validation warnings."""
    state = build_empty_builder_state()
    state = update_builder_value(state, "gs1:gtin", "09501234567890")
    state = update_builder_value(state, "gs1:productID", "SKU-123")
    assert state["values"]

    # Simulate a reset by reinitialising the state.
    reset_state = build_empty_builder_state()
    assert reset_state["values"] == {}
    assert reset_state["validation_warnings"] == []
    data = serialize_builder_state_to_jsonld(reset_state, _metadata())
    assert "gtin" not in data
    assert "productID" not in data


def test_prototype_governance_warning_is_always_first():
    """PROTOTYPE_GOVERNANCE_WARNING must appear first in every validation result."""
    empty_state = build_empty_builder_state()
    warnings = validate_builder_state(empty_state, _metadata())
    assert warnings[0] == PROTOTYPE_GOVERNANCE_WARNING

    state = update_builder_value(empty_state, "gs1:gtin", "09501234567890")
    warnings_with_gtin = validate_builder_state(state, _metadata())
    assert warnings_with_gtin[0] == PROTOTYPE_GOVERNANCE_WARNING
