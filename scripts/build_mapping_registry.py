"""Build the consolidated mapping registry (v0.15.0 Track A).

Deterministically merges the executable mapping profile
``mapping/mapping_v0_3.yaml`` with the governance review catalog
``mapping_catalog/gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_3_webvoc_validated.csv``
into one governed artifact: ``mapping/mapping_registry.yaml``.

Design rules (see docs/mapping-consolidation.md):

- ``settings``, ``fields`` and ``object_mappings`` are copied structurally
  identical from mapping_v0_3.yaml, so the existing converter loader
  (pydantic, extra keys ignored) executes the registry with byte-identical
  output. Each field gains a ``governance`` block the converter ignores.
- The full review catalog is preserved under a top-level ``catalog`` list
  the converter never reads. Registry ``status`` uses the fixed vocabulary
  proposed / review_required / accepted / rejected / deprecated / blocked;
  the original catalog ``mapping_status`` is preserved verbatim as
  ``catalog_status`` so no review provenance is lost.
- Every current catalog row is implemented in mapping_v0_3.yaml, so every
  row normalizes to ``status: accepted``; rows whose catalog status is not
  ``mapped_official_bms_xpath`` additionally carry ``review_required: true``.
  Future non-implemented rows (Track B) will use the other statuses.

Neither source file is modified. Re-running the script is idempotent.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_MAPPING = REPO_ROOT / "mapping" / "mapping_v0_3.yaml"
SOURCE_CATALOG = (
    REPO_ROOT
    / "mapping_catalog"
    / "gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_3_webvoc_validated.csv"
)
TARGET = REPO_ROOT / "mapping" / "mapping_registry.yaml"

STATUS_VOCABULARY = (
    "proposed",
    "review_required",
    "accepted",
    "rejected",
    "deprecated",
    "blocked",
)

# Catalog canonical_field -> YAML canonical_field(s). The catalog and the
# executable YAML are not 1:1: one catalog row can govern two YAML fields
# (value + unit pairs) and the catalog splits document groups that the YAML
# implements as one object mapping.
TOP_LEVEL_ALIASES: dict[str, tuple[str, ...]] = {
    "net_content": ("net_content_value", "net_content_unit"),
}
# Catalog object-group prefix -> YAML object_mapping id.
OBJECT_GROUP_ALIASES: dict[str, str] = {
    "allergens": "allergens",
    "nutrients": "nutrients",
    "certifications": "certifications",
    "certification_documents": "referenced_documents",
    "referenced_documents": "referenced_documents",
}
# Catalog nested canonical_field -> YAML nested canonical_field(s), where
# they differ from an exact match within the object mapping.
NESTED_ALIASES: dict[tuple[str, str], tuple[str, ...]] = {
    ("nutrients", "quantity_contained"): (
        "quantity_contained.value",
        "quantity_contained.unit_code",
    ),
    ("nutrients", "preparation_state"): ("preparation_state_code",),
    ("nutrients", "nutrient_type"): ("nutrient_type_code",),
    ("allergens", "allergen_type"): ("allergen_type",),
    ("certifications", "assessment_date"): ("assessment_date",),
}
# Catalog status normalization: every current row is implemented in the
# executable profile, so all normalize to accepted; anything other than the
# fully reviewed status keeps a review_required flag.
FULLY_REVIEWED_CATALOG_STATUS = "mapped_official_bms_xpath"


def _load_sources() -> tuple[dict, list[dict]]:
    with SOURCE_MAPPING.open("r", encoding="utf-8") as handle:
        mapping_data = yaml.safe_load(handle)
    with SOURCE_CATALOG.open("r", encoding="utf-8-sig", newline="") as handle:
        catalog_rows = list(csv.DictReader(handle))
    return mapping_data, catalog_rows


def _normalize_status(catalog_status: str) -> tuple[str, bool]:
    """Return (registry status, review_required flag) for a catalog row."""
    catalog_status = (catalog_status or "").strip()
    review_required = catalog_status != FULLY_REVIEWED_CATALOG_STATUS
    return "accepted", review_required


def _split_catalog_canonical(canonical_field: str) -> tuple[str | None, str]:
    """Split ``group[].field`` catalog keys into (group, field)."""
    if "[]" in canonical_field:
        group, _, rest = canonical_field.partition("[]")
        return group.strip(), rest.lstrip(".").strip()
    return None, canonical_field.strip()


def _governance_from_row(row: dict, *, matched: bool) -> dict:
    status, review_required = _normalize_status(row.get("mapping_status", ""))
    governance = {
        "status": status,
        "catalog_status": (row.get("mapping_status") or "").strip() or None,
        "confidence": (row.get("confidence") or "").strip() or None,
        "review_required": review_required,
        "source": "mapping_catalog v0.3 (webvoc validated)",
    }
    notes = (row.get("notes") or "").strip()
    if notes:
        governance["notes"] = notes
    review_action = (row.get("review_action") or "").strip()
    if review_action:
        governance["review_action"] = review_action
    if not matched:
        governance["catalog_match"] = "unmatched"
    return governance


def _fallback_governance() -> dict:
    """Governance for YAML fields with no catalog row (experimental terms)."""
    return {
        "status": "accepted",
        "catalog_status": None,
        "confidence": None,
        "review_required": True,
        "source": "mapping_v0_3.yaml (no catalog row; experimental alignment)",
    }


def _catalog_entry(row: dict) -> dict:
    status, review_required = _normalize_status(row.get("mapping_status", ""))
    entry = {
        "canonical_field": (row.get("canonical_field") or "").strip(),
        "jsonld_property": (row.get("jsonld_property") or "").strip(),
        "status": status,
        "catalog_status": (row.get("mapping_status") or "").strip() or None,
        "review_required": review_required,
        "implemented": True,
        "confidence": (row.get("confidence") or "").strip() or None,
        "scope_group": (row.get("scope_group") or "").strip() or None,
        "gdsn_bms_id": (row.get("gdsn_bms_id") or "").strip() or None,
        "gdsn_attribute_name": (row.get("gdsn_attribute_name") or "").strip() or None,
        "gdsn_xpath": (row.get("gdsn_xpath") or "").strip() or None,
        "gdsn_module": (row.get("gdsn_module") or "").strip() or None,
        "gdsn_datatype": (row.get("gdsn_datatype") or "").strip() or None,
        "gdsn_cardinality": (row.get("gdsn_cardinality") or "").strip() or None,
        "code_list": (row.get("code_list") or "").strip() or None,
        "technical_mapping_file": (row.get("technical_mapping_file") or "").strip() or None,
        "webvoc_property_status": (row.get("webvoc_property_status") or "").strip() or None,
        "webvoc_property_validation": (row.get("webvoc_property_validation") or "").strip() or None,
        "recommended_jsonld_property": (row.get("recommended_jsonld_property") or "").strip() or None,
        "notes": (row.get("notes") or "").strip() or None,
        "source": "mapping_catalog v0.3 (webvoc validated)",
    }
    return entry


def build_registry() -> dict:
    mapping_data, catalog_rows = _load_sources()

    # Index catalog rows by (group, field) for governance attachment. Several
    # catalog rows can govern the same YAML field (the YAML merged the
    # certification_documents and referenced_documents catalog groups into one
    # object mapping), so each key holds a list; the row whose original group
    # matches the YAML object id is preferred for the governance block.
    top_level_rows: dict[str, dict] = {}
    nested_rows: dict[tuple[str, str], list[tuple[str, dict]]] = {}
    parent_rows: dict[str, dict] = {}
    for row in catalog_rows:
        group, field = _split_catalog_canonical(row.get("canonical_field", ""))
        if group is None:
            top_level_rows[field] = row
        elif not field:
            parent_rows[OBJECT_GROUP_ALIASES.get(group, group)] = row
        else:
            yaml_group = OBJECT_GROUP_ALIASES.get(group, group)
            key_fields = NESTED_ALIASES.get((yaml_group, field), (field,))
            for key_field in key_fields:
                nested_rows.setdefault((yaml_group, key_field), []).append(
                    (group, row)
                )

    matched_row_ids: set[int] = set()

    fields = []
    for field in mapping_data.get("fields", []):
        new_field = dict(field)
        canonical = str(field.get("canonical_field", ""))
        row = top_level_rows.get(canonical)
        if row is None:
            for catalog_key, yaml_keys in TOP_LEVEL_ALIASES.items():
                if canonical in yaml_keys:
                    row = top_level_rows.get(catalog_key)
                    break
        if row is not None:
            matched_row_ids.add(id(row))
            new_field["governance"] = _governance_from_row(row, matched=True)
        else:
            new_field["governance"] = _fallback_governance()
        fields.append(new_field)

    object_mappings = []
    for obj in mapping_data.get("object_mappings", []):
        new_obj = dict(obj)
        obj_id = str(obj.get("id", ""))
        parent_row = parent_rows.get(obj_id)
        if parent_row is not None:
            matched_row_ids.add(id(parent_row))
            new_obj["governance"] = _governance_from_row(parent_row, matched=True)
        new_fields = []
        for sub in obj.get("fields", []):
            new_sub = dict(sub)
            canonical = str(sub.get("canonical_field") or sub.get("id") or "")
            candidates = nested_rows.get((obj_id, canonical), [])
            if candidates:
                # Prefer the row whose catalog group matches the YAML object
                # id; all rows for the key count as matched (they are all
                # preserved in the catalog list).
                row = next(
                    (r for group, r in candidates if group == obj_id),
                    candidates[0][1],
                )
                for _, matched_row in candidates:
                    matched_row_ids.add(id(matched_row))
                new_sub["governance"] = _governance_from_row(row, matched=True)
            else:
                new_sub["governance"] = _fallback_governance()
            new_fields.append(new_sub)
        new_obj["fields"] = new_fields
        object_mappings.append(new_obj)

    unmatched = [row for row in catalog_rows if id(row) not in matched_row_ids]

    registry = {
        "metadata": {
            "name": "GDSN to GS1 JSON-LD Consolidated Mapping Registry",
            "version": str(mapping_data.get("metadata", {}).get("version", "0.3.0")),
            "registry_version": "1.0.0",
            "description": (
                "Consolidated mapping registry: the executable mapping profile "
                "(structurally identical to mapping_v0_3.yaml) merged with the "
                "governance review catalog. The converter executes fields and "
                "object_mappings only; governance and catalog entries are "
                "review metadata. Review-only; not an official GS1 decision."
            ),
            "consolidated_from": [
                "mapping/mapping_v0_3.yaml",
                (
                    "mapping_catalog/gdsn_to_gs1_web_vocabulary_mapping_catalog"
                    "_v0_3_webvoc_validated.csv"
                ),
            ],
            "status_vocabulary": list(STATUS_VOCABULARY),
        },
        "settings": mapping_data.get("settings", {}),
        "fields": fields,
        "object_mappings": object_mappings,
        "catalog": [_catalog_entry(row) for row in catalog_rows],
    }
    if unmatched:
        registry["metadata"]["unmatched_catalog_rows"] = [
            (row.get("canonical_field") or "").strip() for row in unmatched
        ]
    return registry


def main() -> int:
    registry = build_registry()
    for entry in registry["catalog"]:
        if entry["status"] not in STATUS_VOCABULARY:
            raise ValueError(f"Status outside vocabulary: {entry['status']}")
    header = (
        "# Consolidated mapping registry (generated by "
        "scripts/build_mapping_registry.py).\n"
        "# fields/object_mappings are structurally identical to "
        "mapping_v0_3.yaml and are\n"
        "# the only sections the converter executes; governance and catalog "
        "are review\n"
        "# metadata. Do not edit by hand: changing accepted mappings is a "
        "reviewed\n"
        "# standards decision. Regenerate via the script after any reviewed "
        "change.\n"
    )
    body = yaml.safe_dump(
        registry,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
        width=88,
    )
    TARGET.write_text(header + body, encoding="utf-8", newline="\n")
    print(f"Wrote {TARGET.relative_to(REPO_ROOT)}")
    print(
        f"fields={len(registry['fields'])}, "
        f"object_mappings={len(registry['object_mappings'])}, "
        f"catalog_rows={len(registry['catalog'])}"
    )
    unmatched = registry["metadata"].get("unmatched_catalog_rows", [])
    if unmatched:
        print(f"Unmatched catalog rows ({len(unmatched)}): {', '.join(unmatched)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
