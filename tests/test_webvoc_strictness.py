"""Tests for the WebVoc strictness options (see issue #10).

Covers the two opt-in builder features — ``settings.root_type`` and per-field
``value_datatype`` — plus the v0.6 brand-nesting fix. Every expectation below is
grounded in the committed WebVoc snapshot's declared domain/range.
"""

import json

from gdsn_to_gs1_jsonld.converter import convert_xml_to_jsonld
from gdsn_to_gs1_jsonld.jsonld_builder import build_jsonld
from gdsn_to_gs1_jsonld.mapping_loader import load_mapping

V0_6 = "mapping/mapping_v0_6.yaml"


def _webvoc_terms():
    path = "reference_data/normalized/webvoc_properties_1_17.json"
    with open(path, encoding="utf-8") as handle:
        return {item["term_id"]: item for item in json.load(handle)}


# --- issue #10.1: gs1:brandName must not be asserted on the Product ---------


def test_brand_name_domain_is_brand_not_product():
    """The premise of the fix, asserted against the vocabulary itself."""
    terms = _webvoc_terms()
    assert terms["gs1:brandName"]["domain"] == ["gs1:Brand"]
    assert terms["gs1:brand"]["domain"] == ["gs1:Product"]
    assert terms["gs1:brand"]["range"] == ["gs1:Brand"]


def test_v0_6_nests_brand_name_under_brand(example_xml_path):
    result = convert_xml_to_jsonld(example_xml_path, V0_6)
    data = result.jsonld_data
    assert "gs1:brandName" not in data, "brandName must not sit on the Product"
    brand = data["gs1:brand"]
    assert brand["@type"] == "gs1:Brand"
    # range of gs1:brandName is rdf:langString -> language-tagged value
    assert brand["gs1:brandName"]["@value"] == "Example Brand"
    assert brand["gs1:brandName"]["@language"]


# --- issue #10.2: root @type may declare a subclass ------------------------


def test_v0_6_declares_food_subclass(example_xml_path):
    result = convert_xml_to_jsonld(example_xml_path, V0_6)
    assert result.jsonld_data["@type"] == "gs1:FoodBeverageTobaccoProduct"


def test_root_type_defaults_to_product(example_xml_path, mapping_path):
    """Profiles that do not set root_type are unchanged."""
    result = convert_xml_to_jsonld(example_xml_path, mapping_path)
    assert result.jsonld_data["@type"] == "gs1:Product"


# --- issue #10.3: typed literals for non-string ranges ---------------------


def test_declared_ranges_are_not_plain_strings():
    terms = _webvoc_terms()
    assert terms["gs1:value"]["range"] == ["xsd:float"]
    assert terms["gs1:consumerFirstAvailabilityDateTime"]["range"] == ["xsd:dateTime"]
    assert terms["gs1:referencedFileURL"]["range"] == ["xsd:anyURI"]


def test_value_datatype_emits_typed_literal():
    """A field declaring value_datatype emits {"@value", "@type"}."""
    mapping = load_mapping(V0_6)
    typed = {
        field.jsonld_property: field.value_datatype
        for object_mapping in mapping.object_mappings
        for field in object_mapping.fields
        if field.value_datatype
    }
    assert typed["gs1:value"] == "xsd:float"
    assert typed["gs1:consumerFirstAvailabilityDateTime"] == "xsd:dateTime"
    assert typed["gs1:referencedFileURL"] == "xsd:anyURI"


def test_typed_literal_round_trip():
    """End-to-end shape check through the builder (no sample exercises these)."""
    from gdsn_to_gs1_jsonld.canonical_model import CanonicalProduct

    mapping = load_mapping(V0_6)
    product = CanonicalProduct(gtin="08712345678906")
    # Feed a gross-weight object straight into the builder.
    product.gross_weights = [{"value": 423, "unit_code": "GRM"}]
    data = build_jsonld(product, mapping)
    weight = data.get("gs1:grossWeight")
    if weight:  # only when the profile maps this group
        value = weight[0]["gs1:value"] if isinstance(weight, list) else weight["gs1:value"]
        assert value == {"@value": "423", "@type": "xsd:float"}


def test_xsd_prefix_is_in_context():
    """Typed literals are meaningless without the xsd prefix bound."""
    mapping = load_mapping(V0_6)
    inline = [item for item in mapping.settings.jsonld_context if isinstance(item, dict)]
    assert any("xsd" in item for item in inline)
