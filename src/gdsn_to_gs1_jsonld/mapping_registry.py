"""Consolidated mapping registry loader (v0.15.0 Track A).

The registry file (``mapping/mapping_registry.yaml``) is a superset of the
executable mapping schema: the converter executes only ``fields`` and
``object_mappings`` (via the unchanged :mod:`mapping_loader`), while this
module exposes the governance view — per-field ``governance`` blocks and the
top-level ``catalog`` review list — for review tooling.

Offline, deterministic, read-only. Registry statuses use a fixed vocabulary;
the original catalog ``mapping_status`` values are preserved verbatim as
``catalog_status`` so review provenance is never lost.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

DEFAULT_REGISTRY_PATH = Path("mapping") / "mapping_registry.yaml"

STATUS_VOCABULARY = (
    "proposed",
    "review_required",
    "accepted",
    "rejected",
    "deprecated",
    "blocked",
)


class MappingRegistryError(ValueError):
    """Raised when the registry file is missing or structurally invalid."""


def load_registry(registry_path: str | Path = DEFAULT_REGISTRY_PATH) -> dict[str, Any]:
    """Load the full registry (executable sections + governance + catalog)."""
    path = Path(registry_path)
    if not path.is_file():
        raise MappingRegistryError(f"Mapping registry not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise MappingRegistryError(f"Mapping registry must be a YAML object: {path}")
    for required_key in ("metadata", "settings", "fields", "catalog"):
        if required_key not in data:
            raise MappingRegistryError(
                f"Mapping registry missing required section '{required_key}': {path}"
            )
    for entry in data.get("catalog", []):
        status = entry.get("status")
        if status not in STATUS_VOCABULARY:
            raise MappingRegistryError(
                "Mapping registry catalog entry has status outside the fixed "
                f"vocabulary {STATUS_VOCABULARY}: {status!r} "
                f"({entry.get('canonical_field')!r})"
            )
    return data


def registry_catalog_rows(
    registry: dict[str, Any] | None = None,
    *,
    registry_path: str | Path = DEFAULT_REGISTRY_PATH,
) -> list[dict[str, Any]]:
    """Return the catalog review rows from the registry.

    Row keys mirror the original mapping-catalog CSV columns where they exist
    (``canonical_field``, ``jsonld_property``, ``gdsn_bms_id`` and friends) so
    review tooling can consume either source with the same shape.
    """
    if registry is None:
        registry = load_registry(registry_path)
    return [dict(entry) for entry in registry.get("catalog", [])]


def registry_field_governance(
    registry: dict[str, Any] | None = None,
    *,
    registry_path: str | Path = DEFAULT_REGISTRY_PATH,
) -> dict[str, dict[str, Any]]:
    """Return governance blocks per executable field.

    Keys are ``canonical_field`` for top-level fields and
    ``<object_id>[].<canonical_field>`` for nested object-mapping fields.
    """
    if registry is None:
        registry = load_registry(registry_path)
    governance: dict[str, dict[str, Any]] = {}
    for field in registry.get("fields", []):
        canonical = str(field.get("canonical_field", ""))
        if canonical and isinstance(field.get("governance"), dict):
            governance[canonical] = dict(field["governance"])
    for obj in registry.get("object_mappings", []):
        obj_id = str(obj.get("id", ""))
        if isinstance(obj.get("governance"), dict):
            governance[f"{obj_id}[]"] = dict(obj["governance"])
        for sub in obj.get("fields", []):
            canonical = str(sub.get("canonical_field") or sub.get("id") or "")
            if canonical and isinstance(sub.get("governance"), dict):
                governance[f"{obj_id}[].{canonical}"] = dict(sub["governance"])
    return governance


def registry_summary(
    registry: dict[str, Any] | None = None,
    *,
    registry_path: str | Path = DEFAULT_REGISTRY_PATH,
) -> dict[str, Any]:
    """Deterministic counts for the registry (review support only)."""
    if registry is None:
        registry = load_registry(registry_path)
    catalog = registry.get("catalog", [])
    by_status: dict[str, int] = {status: 0 for status in STATUS_VOCABULARY}
    review_required_count = 0
    for entry in catalog:
        by_status[entry.get("status", "proposed")] = (
            by_status.get(entry.get("status", "proposed"), 0) + 1
        )
        if entry.get("review_required"):
            review_required_count += 1
    executable_field_count = len(registry.get("fields", []))
    nested_field_count = sum(
        len(obj.get("fields", []))
        for obj in registry.get("object_mappings", [])
    )
    return {
        "registry_version": registry.get("metadata", {}).get("registry_version"),
        "executable_top_level_fields": executable_field_count,
        "executable_nested_fields": nested_field_count,
        "executable_total_fields": executable_field_count + nested_field_count,
        "object_mappings": len(registry.get("object_mappings", [])),
        "catalog_rows": len(catalog),
        "catalog_by_status": by_status,
        "catalog_review_required": review_required_count,
    }
