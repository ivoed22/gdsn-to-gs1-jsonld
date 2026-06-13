"""High-level mapping-driven conversion orchestration."""

from collections import Counter
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any

from lxml import etree

from .canonical_model import CanonicalProduct, LanguageValue
from .jsonld_builder import build_jsonld
from .mapping_loader import (
    MappingConfig,
    MappingField,
    ObjectMapping,
    ObjectMappingField,
    load_mapping,
)
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


def _transform_value(
    raw_value: str,
    field: MappingField | ObjectMappingField,
) -> str | Decimal:
    value: str | Decimal = raw_value
    for transform in field.transform:
        value = apply_transform(str(value), transform)
    return value


def _set_nested_value(target: dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    current = target
    for part in parts[:-1]:
        current = current.setdefault(part, {})
    current[parts[-1]] = value


def _extract_object_mapping(
    root: etree._Element,
    object_mapping: ObjectMapping,
    default_language: str,
) -> tuple[list[dict[str, Any]], dict[str, Any], set[str]]:
    parents = [
        element
        for element in root.xpath(object_mapping.parent_xpath)
        if isinstance(element, etree._Element)
    ]
    tree = root.getroottree()
    selected_paths: set[str] = set()
    objects: list[dict[str, Any]] = []
    messages: list[str] = []

    for parent in parents:
        selected_paths.add(tree.getpath(parent))
        if parent.getparent() is not None:
            selected_paths.add(tree.getpath(parent.getparent()))
        object_data: dict[str, Any] = {}
        for field in object_mapping.fields:
            field_elements = [
                element
                for element in parent.xpath(field.xpath)
                if isinstance(element, etree._Element)
            ]
            values: list[Any] = []
            for element in field_elements:
                selected_paths.add(tree.getpath(element))
                ancestor = element.getparent()
                while ancestor is not None and ancestor is not parent:
                    selected_paths.add(tree.getpath(ancestor))
                    ancestor = ancestor.getparent()
                raw_value = _xpath_scalar(element, field.value_xpath)
                if raw_value is None or not raw_value.strip():
                    continue
                try:
                    transformed = _transform_value(raw_value, field)
                except ValueError as exc:
                    messages.append(f"{field.id}: {exc}")
                    continue
                if field.datatype == "language_string":
                    language = (
                        _xpath_scalar(element, field.language_xpath)
                        if field.language_xpath
                        else None
                    )
                    values.append(
                        LanguageValue(
                            value=str(transformed),
                            language=language
                            or field.fallback_language
                            or default_language,
                        )
                    )
                else:
                    values.append(transformed)
            if field.required and not values:
                messages.append(f"{field.id}: required value was not found")
            if field.canonical_field and values:
                _set_nested_value(
                    object_data,
                    field.canonical_field,
                    values if field.multiple else values[0],
                )
        if object_data:
            objects.append(object_data)

    found = bool(objects)
    if messages:
        status = "validation_error"
        message = "; ".join(messages)
    elif found:
        status = "mapped"
        message = f"Mapped {len(objects)} object(s)."
    else:
        status = "missing_optional"
        message = "Optional object mapping was not found."
    row = {
        "id": object_mapping.id,
        "description": object_mapping.description,
        "xpath": object_mapping.parent_xpath,
        "canonical_field": object_mapping.canonical_field,
        "jsonld_property": object_mapping.jsonld_property,
        "required": any(field.required for field in object_mapping.fields),
        "found": found,
        "value": [
            {
                key: serializable_value(value)
                for key, value in object_data.items()
            }
            for object_data in objects
        ],
        "status": status,
        "message": message,
    }
    return objects, row, selected_paths


def _extract_field(
    root: etree._Element,
    field: MappingField,
    default_language: str,
) -> tuple[Any, dict[str, Any], set[str], list[etree._Element]]:
    elements = root.xpath(field.xpath)
    selected_elements = [
        element for element in elements if isinstance(element, etree._Element)
    ]
    tree = root.getroottree()
    selected_paths = {
        tree.getpath(element)
        for element in selected_elements
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
    return value, row, selected_paths, selected_elements


def _find_unmapped(
    root: etree._Element,
    selected_paths: set[str],
) -> dict[str, list[dict[str, Any]]]:
    counts: Counter[
        tuple[str, str | None, str, tuple[tuple[str, str], ...]]
    ] = Counter()
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
            parent = element.getparent()
            parent_name = (
                etree.QName(parent).localname
                if parent is not None and isinstance(parent.tag, str)
                else None
            )
            ancestor_names = [
                etree.QName(ancestor).localname
                for ancestor in element.iterancestors()
                if isinstance(ancestor.tag, str)
            ]
            path = "/" + "/".join(reversed(ancestor_names))
            path = f"{path}/{local_name}"
            context: dict[str, str] = {}
            if parent_name == "referencedFileInformation" and parent is not None:
                context_fields = {
                    "referencedFileTypeCode",
                    "uniformResourceIdentifier",
                    "fileName",
                    "fileFormatName",
                }
                for sibling in parent:
                    if not isinstance(sibling.tag, str):
                        continue
                    sibling_name = etree.QName(sibling).localname
                    if sibling_name in context_fields:
                        sibling_value = "".join(sibling.itertext()).strip()
                        if sibling_value:
                            context[sibling_name] = sibling_value
            context_items = tuple(sorted(context.items()))
            counts[(local_name, parent_name, path, context_items)] += 1
    return {
        "unmapped_elements": [
            {
                "element": element,
                "parent": parent,
                "path": path,
                "count": count,
                **({"context": dict(context_items)} if context_items else {}),
            }
            for (element, parent, path, context_items), count in sorted(
                counts.items(),
                key=lambda item: (item[0][0], item[0][2], item[0][3]),
            )
        ]
    }


def _supporting_paths_for_combined_properties(
    root: etree._Element,
    selected_elements_by_property: dict[
        str,
        dict[str, list[etree._Element]],
    ],
) -> set[str]:
    tree = root.getroottree()
    supporting_paths: set[str] = set()

    for elements_by_field in selected_elements_by_property.values():
        if len(elements_by_field) < 2:
            continue
        fields_by_parent: dict[str, set[str]] = {}
        for field_id, selected_elements in elements_by_field.items():
            for element in selected_elements:
                parent = element.getparent()
                if parent is None:
                    continue
                parent_path = tree.getpath(parent)
                fields_by_parent.setdefault(parent_path, set()).add(field_id)
        supporting_paths.update(
            parent_path
            for parent_path, field_ids in fields_by_parent.items()
            if len(field_ids) >= 2
        )

    return supporting_paths


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
    selected_elements_by_property: dict[
        str,
        dict[str, list[etree._Element]],
    ] = {}

    for mapping_field in mapping.fields:
        value, row, field_selected_paths, field_elements = _extract_field(
            root,
            mapping_field,
            mapping.settings.default_language,
        )
        product_values[mapping_field.canonical_field] = value
        mapping_rows.append(row)
        selected_paths.update(field_selected_paths)
        if row["found"]:
            tree = root.getroottree()
            for element in field_elements:
                parent = element.getparent()
                if (
                    parent is not None
                    and isinstance(parent.tag, str)
                    and etree.QName(parent).localname
                    == etree.QName(element).localname
                ):
                    selected_paths.add(tree.getpath(parent))
            selected_elements_by_property.setdefault(
                mapping_field.jsonld_property,
                {},
            )[mapping_field.id] = field_elements

    for object_mapping in mapping.object_mappings:
        objects, row, object_selected_paths = _extract_object_mapping(
            root,
            object_mapping,
            mapping.settings.default_language,
        )
        product_values[object_mapping.canonical_field] = objects
        mapping_rows.append(row)
        selected_paths.update(object_selected_paths)

    selected_paths.update(
        _supporting_paths_for_combined_properties(
            root,
            selected_elements_by_property,
        )
    )

    product = CanonicalProduct.model_validate(product_values)
    validation_report = validate_product(product, mapping, mapping_rows)
    jsonld_data = build_jsonld(product, mapping)
    unmapped_fields = _find_unmapped(
        root,
        selected_paths,
    )
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
