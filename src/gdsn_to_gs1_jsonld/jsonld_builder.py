"""Build GS1 Web Vocabulary JSON-LD from the canonical product."""

import json
import re
from decimal import Decimal
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel
import yaml

from .canonical_model import CanonicalProduct, LanguageValue
from .mapping_loader import MappingConfig
from .utils import serializable_value


GS1_WEBVOC_CONTEXT = "https://ref.gs1.org/voc/data/gs1Voc.jsonld"
SCHEMA_ORG_CONTEXT = {"schema": "https://schema.org/"}
PROTOTYPE_GOVERNANCE_WARNING = (
    "Manual JSON-LD prototype. This output is entered manually, not generated "
    "from GDSN XML. It is not BMS/XPath traceable unless linked to governed "
    "mapping evidence. It is not an official GS1 validation result."
)


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


def load_builder_manifest(path: str | Path) -> dict[str, Any]:
    """Load the manifest that controls the manual JSON-LD Builder UI."""
    manifest = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("Builder manifest must be a YAML object.")
    for key in ("root_classes", "product_categories", "groups"):
        if key not in manifest:
            raise ValueError(f"Builder manifest missing required key: {key}")
    return manifest


def build_empty_builder_state(root_class: str = "Product") -> dict[str, Any]:
    """Return an empty deterministic manual-builder state."""
    return {
        "root_class": root_class,
        "product_category": "General Product",
        "default_language": "en",
        "selected_groups": ["core_product_information"],
        "values": {},
        "validation_warnings": [],
    }


def get_builder_groups(manifest: dict[str, Any], category: str) -> list[dict[str, Any]]:
    """Return groups in manifest order for a selected product category."""
    categories = {
        item.get("label"): item
        for item in manifest.get("product_categories", [])
        if isinstance(item, dict)
    }
    enabled = categories.get(category, {}).get("groups")
    enabled_keys = set(enabled or [])
    groups = [group for group in manifest.get("groups", []) if isinstance(group, dict)]
    if not enabled_keys:
        return groups
    return [group for group in groups if group.get("key") in enabled_keys]


def get_builder_fields(
    manifest: dict[str, Any],
    group: str | dict[str, Any],
) -> list[dict[str, Any]]:
    """Return field definitions in display order for a manifest group."""
    group_key = group.get("key") if isinstance(group, dict) else group
    for item in manifest.get("groups", []):
        if isinstance(item, dict) and item.get("key") == group_key:
            return [
                field
                for field in item.get("properties", [])
                if isinstance(field, dict)
            ]
    return []


def _metadata_value(metadata: Any, key: str, default: Any = "") -> Any:
    if isinstance(metadata, dict):
        return metadata.get(key, default)
    return getattr(metadata, key, default)


def _metadata_for_property(
    property_metadata: Any,
    property_id: str,
) -> dict[str, Any]:
    if isinstance(property_metadata, dict):
        value = property_metadata.get(property_id, {})
        return value if isinstance(value, dict) else vars(value)
    for item in property_metadata or []:
        term_id = _metadata_value(item, "term_id")
        if term_id == property_id:
            return item if isinstance(item, dict) else vars(item)
    return {}


def _metadata_range(metadata: dict[str, Any]) -> list[str]:
    value = metadata.get("range", [])
    if isinstance(value, list):
        return [str(item) for item in value]
    if value:
        return [str(value)]
    return []


def _is_quantity_property(property_id: str, ranges: list[str]) -> bool:
    compact = _compact_property_name(property_id).lower()
    return "gs1:QuantitativeValue" in ranges or any(
        token in compact
        for token in (
            "content",
            "weight",
            "height",
            "width",
            "depth",
            "dimension",
        )
    )


def infer_input_type(
    property_metadata: Any,
    manifest_override: str | None = None,
) -> str:
    """Infer the manual-builder input type from WebVoc range metadata."""
    if manifest_override:
        return manifest_override
    metadata = property_metadata if isinstance(property_metadata, dict) else vars(property_metadata)
    term_id = str(metadata.get("term_id", ""))
    ranges = _metadata_range(metadata)
    range_set = set(ranges)
    if _is_quantity_property(term_id, ranges):
        return "quantity"
    if "rdf:langString" in range_set:
        return "language_text"
    if "xsd:boolean" in range_set:
        return "checkbox"
    if "xsd:integer" in range_set:
        return "integer"
    if {"xsd:float", "xsd:decimal", "xsd:double"} & range_set:
        return "number"
    if "xsd:dateTime" in range_set:
        return "datetime"
    if "xsd:date" in range_set:
        return "date"
    if "xsd:anyURI" in range_set:
        return "url"
    if "xsd:string" in range_set or not ranges:
        return "text"
    return "unsupported"


def update_builder_value(
    state: dict[str, Any],
    property_id: str,
    value: Any,
    language: str | None = None,
    unit_code: str | None = None,
) -> dict[str, Any]:
    """Return a copy of state with a manual property value updated."""
    updated = {
        **state,
        "values": dict(state.get("values", {})),
        "validation_warnings": list(state.get("validation_warnings", [])),
    }
    if value in (None, "", []) and not language and not unit_code:
        updated["values"].pop(property_id, None)
        return updated
    if isinstance(value, dict):
        entry = dict(value)
    else:
        entry = {"value": value}
    if language:
        entry["language"] = language
    if unit_code:
        entry["unitCode"] = unit_code
    updated["values"][property_id] = entry
    return updated


def _compact_property_name(property_id: str) -> str:
    return property_id.split(":", 1)[1] if ":" in property_id else property_id


def _entry_value(entry: Any) -> Any:
    if isinstance(entry, dict):
        return entry.get("value")
    return entry


def _entry_language(entry: Any) -> str:
    if isinstance(entry, dict):
        return str(entry.get("language") or "")
    return ""


def _entry_unit_code(entry: Any) -> str:
    if isinstance(entry, dict):
        return str(entry.get("unitCode") or "")
    return ""


def _empty_manual_value(value: Any) -> bool:
    if value in (None, "", []):
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def _coerce_scalar(value: Any, input_type: str) -> Any:
    if input_type == "checkbox":
        return bool(value)
    if input_type == "integer":
        return int(value)
    if input_type in {"number", "quantity"}:
        number = Decimal(str(value))
        return serializable_value(number)
    return value


def _looks_like_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _valid_gtin(value: str) -> bool:
    digits = re.sub(r"\D", "", value or "")
    if len(digits) not in {8, 12, 13, 14}:
        return False
    check_digit = int(digits[-1])
    body = digits[:-1]
    total = 0
    for index, digit in enumerate(reversed(body), start=1):
        multiplier = 3 if index % 2 == 1 else 1
        total += int(digit) * multiplier
    return (10 - (total % 10)) % 10 == check_digit


def validate_builder_state(
    state: dict[str, Any],
    property_metadata: Any,
) -> list[str]:
    """Return prototype and field-level warnings for a manual builder state."""
    warnings = [PROTOTYPE_GOVERNANCE_WARNING]
    values = state.get("values", {})
    gtin_entry = values.get("gs1:gtin")
    gtin = str(_entry_value(gtin_entry) or "").strip()
    if not gtin:
        warnings.append("Missing GTIN. The generated JSON-LD will not include a GS1 Digital Link-style @id.")
    elif not _valid_gtin(gtin):
        warnings.append("Invalid GTIN format or check digit.")

    for property_id, entry in values.items():
        metadata = _metadata_for_property(property_metadata, property_id)
        input_type = infer_input_type(
            metadata,
            metadata.get("input_type_override") or metadata.get("input_type"),
        )
        supported = metadata.get("supported_in_v0_10", True)
        value = _entry_value(entry)
        unit_code = _entry_unit_code(entry)
        if (
            _empty_manual_value(value)
            and input_type != "checkbox"
            and not (input_type == "quantity" and unit_code)
        ):
            continue
        if not supported:
            warnings.append(
                f"{property_id} is not supported in v0.10 and will not be emitted."
            )
        if input_type == "unsupported":
            ranges = ", ".join(_metadata_range(metadata)) or "unknown range"
            warnings.append(
                f"{property_id} has unsupported nested or complex range ({ranges}) and will not be emitted."
            )
        if input_type == "url" and value and not _looks_like_url(str(value)):
            warnings.append(f"{property_id} is not a valid HTTP(S) URL.")
        if input_type == "language_text" and value and not _entry_language(entry):
            warnings.append(f"{property_id} needs a language tag.")
        if input_type in {"integer", "number", "quantity"} and value not in (None, ""):
            try:
                _coerce_scalar(value, input_type)
            except (ArithmeticError, ValueError):
                warnings.append(f"{property_id} must be a valid number.")
        if input_type == "quantity":
            if value not in (None, "") and not unit_code:
                warnings.append(f"{property_id} has a quantity value without unitCode.")
            if unit_code and value in (None, ""):
                warnings.append(f"{property_id} has unitCode without a quantity value.")
    return list(dict.fromkeys(warnings))


def serialize_builder_state_to_jsonld(
    state: dict[str, Any],
    property_metadata: Any,
) -> dict[str, Any]:
    """Serialize manual-builder state to deterministic prototype JSON-LD."""
    data: dict[str, Any] = {
        "@context": [GS1_WEBVOC_CONTEXT, SCHEMA_ORG_CONTEXT],
        "@type": state.get("root_class") or "Product",
    }
    values = state.get("values", {})
    gtin = str(_entry_value(values.get("gs1:gtin")) or "").strip()
    if gtin:
        data["@id"] = f"https://id.gs1.org/01/{gtin}"

    for property_id in sorted(values):
        entry = values[property_id]
        value = _entry_value(entry)
        if _empty_manual_value(value) and value is not False:
            continue
        metadata = _metadata_for_property(property_metadata, property_id)
        input_type = infer_input_type(
            metadata,
            metadata.get("input_type_override") or metadata.get("input_type"),
        )
        if not metadata.get("supported_in_v0_10", True) or input_type == "unsupported":
            continue
        compact_name = _compact_property_name(property_id)
        if input_type == "language_text":
            language = _entry_language(entry)
            if not language:
                continue
            data[compact_name] = [{"@language": language, "@value": str(value)}]
        elif input_type == "quantity":
            unit_code = _entry_unit_code(entry)
            if value in (None, "") or not unit_code:
                continue
            try:
                quantity_value = _coerce_scalar(value, "quantity")
            except (ArithmeticError, ValueError):
                continue
            data[compact_name] = {
                "value": quantity_value,
                "unitCode": unit_code,
            }
        elif input_type == "url":
            if _looks_like_url(str(value)):
                data[compact_name] = str(value)
        else:
            try:
                data[compact_name] = _coerce_scalar(value, input_type)
            except (ArithmeticError, ValueError):
                continue
    return data


def jsonld_bytes(data: dict[str, Any]) -> bytes:
    """Return deterministic UTF-8 JSON-LD bytes for download/tests."""
    return (
        json.dumps(data, indent=2, ensure_ascii=False, sort_keys=False) + "\n"
    ).encode("utf-8")
