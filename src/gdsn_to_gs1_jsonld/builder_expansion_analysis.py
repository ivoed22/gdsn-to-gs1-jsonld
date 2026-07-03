"""Builder manifest expansion analysis (Track C, v0.19.0).

Read-only analysis of which WebVoc properties not yet authorable in the
Manual JSON-LD Prototype Builder manifest are mature enough to add next.
Fed by Track B's hard-mapping detection and the mapping registry's
governance catalog. Produces a proposal for a human to approve — it never
writes to the builder manifest.

Readiness phases (fixed vocabulary, deterministic derivation only):

- ``ready_now``: has governed mapping evidence (accepted or otherwise
  implemented), not hard-mapping, not codelist-dependent.
- ``needs_codelist_curation``: has mapping evidence but the property looks
  controlled-vocabulary shaped (per the same code-list heuristic used by the
  Mapping Candidate Generator), so manifest ``options`` would need curating
  before the field is authorable (mirrors how existing "code" builder
  fields work today).
- ``needs_hard_mapping_review``: has mapping evidence but that evidence's
  GDSN attribute is a Track B hard mapping (cross-reference outside the
  current product message) and would need the same dedicated review as any
  other hard mapping before being trusted as builder evidence.
- ``not_ready_no_evidence``: no governed mapping evidence at all. Nothing
  here invents evidence to promote a property regardless of demand.

DPP relevance is intentionally reported as "not yet assessed" for every
property: that judgment is the GS1-first DPP Crosswalk's job (v0.20.0+,
not built), and fabricating it here would be exactly the kind of invented
data this project does not produce.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .mapping_candidate_generator import detect_hard_mapping, load_gdsn_reference
from .mapping_registry import load_registry, registry_catalog_rows

READINESS_PHASES = (
    "ready_now",
    "needs_codelist_curation",
    "needs_hard_mapping_review",
    "not_ready_no_evidence",
)

DPP_RELEVANCE_NOT_ASSESSED = "not_yet_assessed_pending_crosswalk"

# Same controlled-vocabulary heuristic used by
# mapping_candidate_generator.score_candidate's code_list_signal, applied to
# the WebVoc side only (no GDSN attribute needed) since it is a WebVoc-shape
# signal used to flag manifest curation effort, not a match score.
_CODE_LIST_RANGE_TOKENS = {"code", "enumeration", "type"}
_CODE_LIST_NAME_TOKENS = {"code", "type", "status", "method"}


def _looks_codelist_shaped(webvoc_row: dict[str, Any]) -> bool:
    range_value = str(webvoc_row.get("range") or "").lower()
    compact_name = str(webvoc_row.get("compact_name") or "").lower()
    return any(token in range_value for token in _CODE_LIST_RANGE_TOKENS) or any(
        token in compact_name for token in _CODE_LIST_NAME_TOKENS
    )


def authored_property_ids(manifest: dict[str, Any]) -> set[str]:
    """Property ids already authorable in the builder manifest."""
    ids: set[str] = set()
    for group in manifest.get("groups", []):
        if not isinstance(group, dict):
            continue
        for field in group.get("properties", []):
            if isinstance(field, dict) and field.get("property_id"):
                ids.add(str(field["property_id"]))
    return ids


def _hard_mapping_index(gdsn_reference_path: str | Path) -> dict[str, tuple[bool, list[str]]]:
    index: dict[str, tuple[bool, list[str]]] = {}
    for row in load_gdsn_reference(str(gdsn_reference_path)):
        bms_id = str(row.get("bms_id") or "").strip()
        if bms_id and bms_id not in index:
            index[bms_id] = detect_hard_mapping(row)
    return index


def _catalog_index_by_property(catalog_rows: list[dict[str, Any]]) -> dict[str, list[dict]]:
    index: dict[str, list[dict]] = {}
    for row in catalog_rows:
        prop = str(row.get("jsonld_property") or "").strip()
        if prop:
            index.setdefault(prop, []).append(row)
    return index


def _classify_property(
    webvoc_row: dict[str, Any],
    catalog_hits: list[dict[str, Any]],
    hard_mapping_index: dict[str, tuple[bool, list[str]]],
) -> tuple[str, str, bool, bool, list[str]]:
    """Return (phase, reason, codelist_dependency, hard_mapping_dependency, hard_mapping_reasons)."""
    if not catalog_hits:
        return (
            "not_ready_no_evidence",
            "No governed mapping evidence (mapping registry catalog) for this property.",
            False,
            False,
            [],
        )

    hard_mapping_reasons: list[str] = []
    for hit in catalog_hits:
        bms_id = str(hit.get("gdsn_bms_id") or "").strip()
        if not bms_id:
            continue
        is_hard, reasons = hard_mapping_index.get(bms_id, (False, []))
        if is_hard:
            hard_mapping_reasons.extend(reasons)
    hard_mapping_dependency = bool(hard_mapping_reasons)

    codelist_dependency = _looks_codelist_shaped(webvoc_row)

    if hard_mapping_dependency:
        return (
            "needs_hard_mapping_review",
            "Mapping evidence exists, but its GDSN attribute is a hard "
            "mapping (cross-reference outside the current product message) "
            "and needs dedicated review before use as builder evidence.",
            codelist_dependency,
            True,
            hard_mapping_reasons,
        )
    if codelist_dependency:
        return (
            "needs_codelist_curation",
            "Mapping evidence exists, but this property looks "
            "controlled-vocabulary shaped; manifest options would need "
            "curating before the field is authorable.",
            True,
            False,
            [],
        )
    return (
        "ready_now",
        "Mapping evidence exists; not hard-mapping; not controlled-vocabulary "
        "shaped.",
        False,
        False,
        [],
    )


def build_expansion_analysis(
    webvoc_rows: list[dict[str, Any]],
    manifest: dict[str, Any],
    catalog_rows: list[dict[str, Any]],
    gdsn_reference_path: str | Path,
) -> dict[str, Any]:
    """Build the full expansion analysis. Never modifies the manifest."""
    authored = authored_property_ids(manifest)
    catalog_index = _catalog_index_by_property(catalog_rows)
    hard_mapping_index = _hard_mapping_index(gdsn_reference_path)

    candidates: list[dict[str, Any]] = []
    for row in webvoc_rows:
        term_id = str(row.get("term_id") or "").strip()
        if not term_id or term_id in authored:
            continue
        catalog_hits = catalog_index.get(term_id, [])
        phase, reason, codelist_dep, hard_mapping_dep, hard_reasons = _classify_property(
            row, catalog_hits, hard_mapping_index
        )
        mapping_status = (
            sorted({str(hit.get("status") or "") for hit in catalog_hits})
            if catalog_hits
            else []
        )
        candidates.append(
            {
                "term_id": term_id,
                "label": str(row.get("label") or ""),
                "range": str(row.get("range") or ""),
                "source_mapping_status": mapping_status,
                "codelist_dependency": codelist_dep,
                "hard_mapping_dependency": hard_mapping_dep,
                "hard_mapping_reasons": hard_reasons,
                "dpp_relevance": DPP_RELEVANCE_NOT_ASSESSED,
                "readiness_phase": phase,
                "reason": reason,
            }
        )

    candidates.sort(key=lambda c: (c["readiness_phase"] != "ready_now", c["term_id"]))

    counts = {phase: 0 for phase in READINESS_PHASES}
    for candidate in candidates:
        counts[candidate["readiness_phase"]] += 1

    return {
        "authored_property_count": len(authored),
        "total_webvoc_property_count": len(webvoc_rows),
        "not_yet_authorable_count": len(candidates),
        "by_readiness_phase": counts,
        "candidates": candidates,
    }


def load_catalog_rows_from_registry(registry_path: str | Path) -> list[dict[str, Any]]:
    """Convenience loader: catalog rows from the consolidated mapping registry."""
    registry = load_registry(registry_path)
    return registry_catalog_rows(registry)


def write_expansion_analysis(analysis: dict[str, Any], output_dir: str | Path) -> dict[str, str]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "builder_manifest_expansion_analysis.json"
    path.write_bytes(json.dumps(analysis, indent=2, ensure_ascii=False).encode("utf-8"))
    return {"json": str(path)}
