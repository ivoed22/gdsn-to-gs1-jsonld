"""Build GS1 Web Vocabulary JSON-LD from the canonical product."""

from typing import Any

from .canonical_model import CanonicalProduct, LanguageValue
from .mapping_loader import MappingConfig
from .utils import serializable_value


def _language_values(values: list[LanguageValue]) -> list[dict[str, str]]:
    return [
        {"@value": item.value, "@language": item.language}
        for item in values
        if item.value
    ]


def build_jsonld(
    product: CanonicalProduct,
    mapping: MappingConfig,
) -> dict[str, Any]:
    properties = {
        field.canonical_field: field.jsonld_property for field in mapping.fields
    }
    data: dict[str, Any] = {
        "@context": mapping.settings.jsonld_context,
        "@type": "gs1:Product",
    }

    if product.gtin:
        data["@id"] = f"https://id.gs1.org/01/{product.gtin}"

    simple_values: dict[str, Any] = {
        "gtin": product.gtin,
        "product_name": _language_values(product.product_name),
        "product_description": _language_values(product.product_description),
        "brand_name": product.brand_name,
        "gpc_category_code": product.gpc_category_code,
        "product_image_url": list(dict.fromkeys(product.product_image_url)),
        "product_page_url": product.product_page_url,
    }
    for canonical_field, value in simple_values.items():
        if value not in (None, "", []):
            data[properties[canonical_field]] = value

    if (
        product.net_content_value is not None
        and product.net_content_unit is not None
    ):
        net_content_property = properties["net_content_value"]
        data[net_content_property] = {
            "value": serializable_value(product.net_content_value),
            "unitCode": product.net_content_unit,
        }
    return data
