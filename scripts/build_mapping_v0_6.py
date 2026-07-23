"""Build the standards-clean v0.6 mapping profile from v0.5."""

from __future__ import annotations

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mapping" / "mapping_v0_5.yaml"
YAML_TARGET = ROOT / "mapping" / "mapping_v0_6.yaml"
JSON_TARGET = ROOT / "cloudflare_pwa" / "data" / "mappings" / "mapping_v0_6.json"


def main() -> None:
    data = yaml.safe_load(SOURCE.read_text(encoding="utf-8"))
    data["metadata"].update(
        {
            "name": "GDSN to GS1 JSON-LD Clean Product Profile",
            "version": "0.6.0",
            "description": (
                "Clean product output with explicit GS1 code IRIs, typed nested "
                "country/contact objects and referenced-file type metadata."
            ),
            "derived_from": "mapping/mapping_v0_5.yaml",
        }
    )
    objects = {item["id"]: item for item in data["object_mappings"]}

    allergen_fields = {item["id"]: item for item in objects["allergens"]["fields"]}
    allergen_fields["allergen_type"]["code_prefix"] = "gs1:AllergenTypeCode-"
    allergen_fields["level_of_containment"]["code_prefix"] = "gs1:LevelOfContainmentCode-"

    target_field = objects["target_markets"]["fields"][0]
    target_field["nested_object_type"] = "gs1:Country"

    support = objects["customer_support_centres"]
    support_fields = {item["id"]: item for item in support["fields"]}
    support_fields["support_email"]["nested_object_type"] = "gs1:ContactPoint"
    support["fields"].insert(
        -1,
        {
            "id": "support_contact_name",
            "xpath": ".//*[local-name()='contactName']",
            "value_xpath": "text()",
            "canonical_field": "contact.name",
            "jsonld_property": "gs1:contactPoint.schema:name",
            "datatype": "string",
            "nested_object_type": "gs1:ContactPoint",
            "required": False,
            "multiple": False,
            "transform": ["trim", "normalize_whitespace"],
        },
    )

    images = objects["product_images"]
    images["fields"].insert(
        1,
        {
            "id": "image_type",
            "xpath": "./*[local-name()='referencedFileTypeCode']",
            "value_xpath": "text()",
            "canonical_field": "referenced_file_type",
            "jsonld_property": "gs1:referencedFileType",
            "datatype": "string",
            "code_prefix": "gs1:ReferencedFileTypeCode-",
            "required": False,
            "multiple": False,
            "transform": ["trim", "uppercase"],
        },
    )

    YAML_TARGET.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    JSON_TARGET.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
