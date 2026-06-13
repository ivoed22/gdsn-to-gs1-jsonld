"""High-level mapping-driven conversion orchestration."""

from collections import Counter
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any

from lxml import etree

from .canonical_model import CanonicalProduct, LanguageValue
from .jsonld_builder import build_jsonld
from .mapping_loader import MappingConfig, MappingField, load_mapping
from .reporter import write_reports
from .utils import apply_transform, serializable_value
from .validator import validate_product
from .xml_parser import XMLInput, parse_xml

UNMAPPED_IGNORE = {
    "catalogueItemNotificationMessage",
    "transaction",
    "transactionIdentification",
    "catalogueItem",
    "tradeItem",
    "tradeItemInformation",
    "tradeItemDescriptionInformation",
    "tradeItemMeasurements",
    "marketingInformation",
    "brandNameInformation",
    "informationProviderOfTradeItem",
    "contentOwner",
    "referencedFileInformation",
    "quantityContained",
    "nutrientDetail",
    "allergen",
}


@dataclass
class ConversionResult:
    jsonld_data: dict[str, Any]
    canonical_product: CanonicalProduct
    mapping_report_rows: list[dict[str, Any]]
    validation_report: dict[str, Any]
    unmapped_fields: dict[str, Any]
    output_file_paths: dict[str, Path] = field(default_factory=dict)


def _xpath_scalar(element: etree._Element, xpath: str) -> str | None:
    values = element.xpath(xpath)
    if not values:
        return None
    value = values[0]
    if isinstance(value, etree._Element):
        return "".join(value.itertext())
    return str(value)


def _transform_value(raw_value: str, field: MappingField) -> str | Decimal:
    value: str | Decimal = raw_value
    for transform in field.transform:
        value = apply_transform(str(value), transform)
    return value


def _extract_field(
    root: etree._Element,
    field: MappingField,
    default_language: str,
) -> tuple[Any, dict[str, Any], set[str]]:
    elements = root.xpath(field.xpath)
    tree = root.getroottree()
    selected_paths = {
        tree.getpath(element)
        for element in elements
        if isinstance(element, etree._Element)
    }
    extracted: list[Any] = []
    errors: list[str] = []

    for element in elements:
        if not isinstance(element, etree._Element):
            errors.append("Field xpath must select XML elements.")
            continue
        raw_value = _xpath_scalar(element, field.value_xpath)
        if raw_value is None or not raw_value.strip():
            continue
        try:
            transformed = _transform_value(raw_value, field)
        except ValueError as exc:
            errors.append(str(exc))
            continue

        if field.datatype == "language_string":
            language = (
                _xpath_scalar(element, field.language_xpath)
                if field.language_xpath
                else None
            )
            extracted.append(
                LanguageValue(
                    value=str(transformed),
                    language=language
                    or field.fallback_language
                    or default_language,
                )
            )
        else:
            extracted.append(transformed)

    found = bool(extracted)
    if errors:
        status = (
            "validation_error"
            if any(name in field.transform for name in ("validate_gtin", "validate_url"))
            else "transform_error"
        )
        message = "; ".join(errors)
    elif found:
        status = "mapped"
        message = "Value mapped successfully."
    elif field.required:
        status = "missing_required"
        message = "Required value was not found."
    else:
        status = "missing_optional"
        message = "Optional value was not found."

    value: Any
    if field.multiple:
        value = extracted
    else:
        value = extracted[0] if extracted else None
    display_values = [
        item.model_dump() if isinstance(item, LanguageValue) else serializable_value(item)
        for item in extracted
    ]
    row = {
        "id": field.id,
        "description": field.description,
        "xpath": field.xpath,
        "canonical_field": field.canonical_field,
        "jsonld_property": field.jsonld_property,
        "required": field.required,
        "found": found,
        "value": display_values if field.multiple else (display_values[0] if display_values else None),
        "status": status,
        "message": message,
    }
    return value, row, selected_paths


def _find_unmapped(
    root: etree._Element,
    selected_paths: set[str],
) -> dict[str, list[dict[str, Any]]]:
    counts: Counter[str] = Counter()
    tree = root.getroottree()
    for element in root.iter():
        if not isinstance(element.tag, str):
            continue
        if tree.getpath(element) in selected_paths:
            continue
        local_name = etree.QName(element).localname
        if local_name in UNMAPPED_IGNORE:
            continue
        if "".join(element.itertext()).strip():
            counts[local_name] += 1
    return {
        "unmapped_elements": [
            {"element": name, "count": count}
            for name, count in sorted(counts.items())
        ]
    }


def convert_xml_to_jsonld(
    xml_input: XMLInput,
    mapping_path: str | Path,
    output_dir: str | Path | None = None,
    write_files: bool = False,
) -> ConversionResult:
    mapping: MappingConfig = load_mapping(mapping_path)
    root = parse_xml(xml_input)
    product_values: dict[str, Any] = {}
    mapping_rows: list[dict[str, Any]] = []
    selected_paths: set[str] = set()

    for mapping_field in mapping.fields:
        value, row, field_selected_paths = _extract_field(
            root,
            mapping_field,
            mapping.settings.default_language,
        )
        product_values[mapping_field.canonical_field] = value
        mapping_rows.append(row)
        selected_paths.update(field_selected_paths)

    product = CanonicalProduct.model_validate(product_values)
    validation_report = validate_product(product, mapping, mapping_rows)
    jsonld_data = build_jsonld(product, mapping)
    unmapped_fields = _find_unmapped(root, selected_paths)
    result = ConversionResult(
        jsonld_data=jsonld_data,
        canonical_product=product,
        mapping_report_rows=mapping_rows,
        validation_report=validation_report,
        unmapped_fields=unmapped_fields,
    )

    if write_files:
        if output_dir is None:
            raise ValueError("output_dir is required when write_files=True")
        result.output_file_paths = write_reports(
            output_dir,
            product.gtin or "unknown",
            jsonld_data,
            mapping_rows,
            validation_report,
            unmapped_fields,
        )
    return result
