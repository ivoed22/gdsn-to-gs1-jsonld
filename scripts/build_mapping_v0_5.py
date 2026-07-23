"""Build v0.5 from review-safe v0.4 with structurally reviewed additions."""

from __future__ import annotations

from pathlib import Path

import yaml

from build_mapping_v0_4 import build as build_v0_4


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "mapping" / "mapping_v0_5.yaml"


def scalar_field(
    field_id: str,
    description: str,
    source_name: str,
    canonical: str,
    target: str,
    *,
    datatype: str = "string",
    language: bool = False,
    fallback_language: str | None = None,
) -> dict:
    field = {
        "id": field_id,
        "description": description,
        "xpath": f".//*[local-name()='{source_name}']",
        "value_xpath": "text()",
        "canonical_field": canonical,
        "jsonld_property": target,
        "required": False,
        "datatype": "language_string" if language else datatype,
        "multiple": language,
        "transform": ["trim", "normalize_whitespace"] if language else ["trim"],
    }
    if language:
        field["language_xpath"] = "./@languageCode"
        field["fallback_language"] = fallback_language or "und"
    return field


def build() -> dict:
    data = build_v0_4()
    data["metadata"] = {
        "name": "GDSN to GS1 JSON-LD Structured Review Profile",
        "version": "0.5.0",
        "description": (
            "Review-safe v0.5 adds structurally verified product, packaging, "
            "origin, target-market, organization and image metadata. Ambiguous "
            "AI candidates remain in review evidence and are not emitted."
        ),
        "derived_from": "mapping/mapping_v0_4.yaml",
        "webvoc_snapshot": "webvoc/current/gs1Voc.jsonld",
    }
    data["fields"].extend(
        [
            scalar_field("functional_name", "Functional name", "functionalName", "functional_name", "gs1:functionalName", language=True),
            scalar_field("regulated_product_name", "Regulated product name", "regulatedProductName", "regulated_product_name", "gs1:regulatedProductName", language=True),
            scalar_field("gpc_category_description", "GPC category description", "gpcCategoryName", "gpc_category_description", "gs1:gpcCategoryDescription", language=True),
        ]
    )
    data["object_mappings"].extend(
        [
            {
                "id": "gross_weights",
                "description": "Gross weight with unit",
                "parent_xpath": ".//*[local-name()='grossWeight']",
                "canonical_field": "gross_weights",
                "jsonld_property": "gs1:grossWeight",
                "object_type": "gs1:QuantitativeValue",
                "multiple": False,
                "fields": [
                    {"id": "gross_weight_value", "xpath": ".", "value_xpath": "text()", "canonical_field": "value", "jsonld_property": "gs1:value", "datatype": "decimal", "required": True, "multiple": False, "transform": ["trim", "to_decimal"]},
                    {"id": "gross_weight_unit", "xpath": ".", "value_xpath": "./@measurementUnitCode", "canonical_field": "unit_code", "jsonld_property": "gs1:unitCode", "datatype": "string", "required": True, "multiple": False, "transform": ["trim", "uppercase"]},
                ],
            },
            {
                "id": "packaging_details",
                "description": "Packaging details",
                "parent_xpath": ".//*[local-name()='packaging'][./*[local-name()='packagingTypeCode']]",
                "canonical_field": "packaging_details",
                "jsonld_property": "gs1:packaging",
                "object_type": "gs1:PackagingDetails",
                "multiple": True,
                "fields": [
                    {"id": "packaging_type", "xpath": "./*[local-name()='packagingTypeCode']", "value_xpath": "text()", "canonical_field": "packaging_type", "jsonld_property": "gs1:packagingType", "datatype": "string", "required": True, "multiple": False, "transform": ["trim", "uppercase"]}
                ],
            },
            {
                "id": "countries_of_origin",
                "description": "Country of origin",
                "parent_xpath": ".//*[local-name()='countryOfOrigin'][./*[local-name()='countryCode']]",
                "canonical_field": "countries_of_origin",
                "jsonld_property": "gs1:countryOfOrigin",
                "object_type": "gs1:Country",
                "multiple": True,
                "fields": [
                    {"id": "origin_country_code", "xpath": "./*[local-name()='countryCode']", "value_xpath": "text()", "canonical_field": "country_code", "jsonld_property": "gs1:countryCode", "datatype": "string", "required": True, "multiple": False, "transform": ["trim", "uppercase"]}
                ],
            },
            {
                "id": "target_markets",
                "description": "Target market and first availability",
                "parent_xpath": ".//*[local-name()='targetMarket'][./*[local-name()='targetMarketCountryCode']]",
                "canonical_field": "target_markets",
                "jsonld_property": "gs1:targetMarket",
                "object_type": "gs1:TargetMarketDetails",
                "multiple": True,
                "fields": [
                    {"id": "target_market_country", "xpath": "./*[local-name()='targetMarketCountryCode']", "value_xpath": "text()", "canonical_field": "country.country_code", "jsonld_property": "gs1:targetMarketCountries.gs1:countryCode", "datatype": "string", "required": True, "multiple": False, "transform": ["trim", "uppercase"]},
                    {"id": "first_availability", "xpath": "ancestor::*[local-name()='tradeItem'][1]//*[local-name()='startAvailabilityDateTime']", "value_xpath": "text()", "canonical_field": "first_availability", "jsonld_property": "gs1:consumerFirstAvailabilityDateTime", "datatype": "string", "required": False, "multiple": False, "transform": ["trim"]},
                ],
            },
            {
                "id": "customer_support_centres",
                "description": "Consumer support organization and contact channel",
                "parent_xpath": ".//*[local-name()='tradeItemContactInformation'][./*[local-name()='contactTypeCode'][normalize-space(text())='CXC']]",
                "canonical_field": "customer_support_centres",
                "jsonld_property": "gs1:customerSupportCentre",
                "object_type": "gs1:Organization",
                "multiple": True,
                "fields": [
                    {"id": "support_party_gln", "xpath": "ancestor::*[local-name()='tradeItem'][1]/*[local-name()='informationProviderOfTradeItem']/*[local-name()='gln']", "value_xpath": "text()", "canonical_field": "party_gln", "jsonld_property": "gs1:partyGLN", "datatype": "string", "required": False, "multiple": False, "transform": ["trim"]},
                    {"id": "support_organization_name", "xpath": "ancestor::*[local-name()='tradeItem'][1]/*[local-name()='informationProviderOfTradeItem']/*[local-name()='partyName']", "value_xpath": "text()", "canonical_field": "organization_name", "jsonld_property": "gs1:organizationName", "datatype": "language_string", "language_xpath": "./@languageCode", "fallback_language": "und", "required": False, "multiple": False, "transform": ["trim", "normalize_whitespace"]},
                    {"id": "support_email", "xpath": ".//*[local-name()='communicationChannel'][./*[local-name()='communicationChannelCode'][normalize-space(text())='EMAIL']]/*[local-name()='communicationValue']", "value_xpath": "text()", "canonical_field": "contact.email", "jsonld_property": "gs1:contactPoint.gs1:email", "datatype": "string", "required": False, "multiple": False, "transform": ["trim"]},
                ],
            },
            {
                "id": "product_images",
                "description": "Product image metadata",
                "parent_xpath": ".//*[local-name()='referencedFileHeader'][./*[local-name()='referencedFileTypeCode'][normalize-space(text())='PRODUCT_IMAGE']]",
                "canonical_field": "product_images",
                "jsonld_property": "gs1:image",
                "object_type": "gs1:ReferencedFileDetails",
                "multiple": True,
                "fields": [
                    {"id": "image_url", "xpath": "./*[local-name()='uniformResourceIdentifier']", "value_xpath": "text()", "canonical_field": "url", "jsonld_property": "gs1:referencedFileURL", "datatype": "url", "required": True, "multiple": False, "transform": ["trim", "validate_url"]},
                    {"id": "image_name", "xpath": "./*[local-name()='fileName']", "value_xpath": "text()", "canonical_field": "name", "jsonld_property": "gs1:referencedFileName", "datatype": "string", "required": False, "multiple": False, "transform": ["trim"]},
                    {"id": "image_pixel_height", "xpath": ".//*[local-name()='filePixelHeight']", "value_xpath": "text()", "canonical_field": "pixel_height", "jsonld_property": "gs1:filePixelHeight", "datatype": "decimal", "required": False, "multiple": False, "transform": ["trim", "to_decimal"]},
                    {"id": "image_pixel_width", "xpath": ".//*[local-name()='filePixelWidth']", "value_xpath": "text()", "canonical_field": "pixel_width", "jsonld_property": "gs1:filePixelWidth", "datatype": "decimal", "required": False, "multiple": False, "transform": ["trim", "to_decimal"]},
                ],
            },
        ]
    )
    data["candidate_expansion"] = {
        "status": "review_required",
        "policy": "Only structurally reviewed additions execute. Remaining AI candidates stay removable review evidence.",
        "consensus_source": "mapping_catalog/unmapped_gdsn_webvoc_suggestions_v0_1.csv",
    }
    return data


if __name__ == "__main__":
    TARGET.write_text(yaml.safe_dump(build(), sort_keys=False, allow_unicode=True), encoding="utf-8")
    print(TARGET)
