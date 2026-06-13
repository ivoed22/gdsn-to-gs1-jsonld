"""Build GS1 Web Vocabulary JSON-LD from the canonical product."""

from decimal import Decimal
from typing import Any

from pydantic import BaseModel

from .canonical_model import CanonicalProduct, LanguageValue
from .mapping_loader import MappingConfig
from .utils import serializable_value


def _language_values(values: list[LanguageValue]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in values:
        marker = (item.value, item.language)
        if item.value and marker not in seen:
            output.append({"@value": item.value, "@language": item.language})
            seen.add(marker)
    return output


def _get_nested_value(value: Any, path: str) -> Any:
    current = value
    for part in path.split("."):
        if isinstance(current, BaseModel):
            current = getattr(current, part, None)
        elif isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def _set_nested_value(target: dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    current = target
    for part in parts[:-1]:
        current = current.setdefault(part, {})
    current[parts[-1]] = value


def _object_values(values: list[Any], object_mapping: Any) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for value in values:
        item: dict[str, Any] = {}
        if object_mapping.object_type:
            item["@type"] = object_mapping.object_type
        for field in object_mapping.fields:
            if not field.canonical_field:
                continue
            field_value = _get_nested_value(value, field.canonical_field)
            if field_value in (None, "", []):
                continue
            if isinstance(field_value, Decimal):
                field_value = serializable_value(field_value)
            _set_nested_value(item, field.jsonld_property, field_value)
        if len(item) == (1 if object_mapping.object_type else 0):
            continue
        marker = repr(item)
        if marker not in seen:
            output.append(item)
            seen.add(marker)
    return output


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
        "ingredient_statement": _language_values(product.ingredient_statement),
    }
    for canonical_field, value in simple_values.items():
        if canonical_field in properties and value not in (None, "", []):
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

    for object_mapping in mapping.object_mappings:
        values = getattr(product, object_mapping.canonical_field, [])
        objects = _object_values(values, object_mapping)
        if objects:
            data[object_mapping.jsonld_property] = (
                objects if object_mapping.multiple else objects[0]
            )
    return data
