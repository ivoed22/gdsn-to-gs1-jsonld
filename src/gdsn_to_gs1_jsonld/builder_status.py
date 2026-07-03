"""Manual JSON-LD Builder per-field status derivation (v0.18.0).

Pure, deterministic functions — no Streamlit dependency — so they're
unit-testable in isolation. Used by app/workflows/prototype.py to render
status chips, per-section warning counts, and the coverage overview without
changing the builder's serializer output (build_empty_builder_state,
serialize_builder_state_to_jsonld, validate_builder_state are untouched).

Status vocabulary (fixed): filled, missing, review_required,
hard_mapping_review, codelist_pending, external_source_required,
extension_candidate, blocked.

Two statuses are reserved and never triggered by current local data:
- external_source_required: would flag fields needing a promoted hard
  mapping's GLN/GTIN reference lookup (Track B hard-mapping candidates are
  not automatically promoted; see mapping_promotion.py). Reserved until a
  hard mapping is actually promoted into the manifest.
- extension_candidate: would flag fields identified as local-extension
  candidates by the GS1-first DPP Crosswalk (v0.19.0+, not built yet).

Deriving these two now would mean inventing data that does not exist —
against the project's no-fabricated-data rule. They exist in the vocabulary
so downstream UI/exports have a stable status set to render against once
Track C/the Crosswalk exist, not because the data exists today.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .mapping_candidate_generator import detect_hard_mapping, load_gdsn_reference

STATUS_VALUES = (
    "filled",
    "missing",
    "review_required",
    "hard_mapping_review",
    "codelist_pending",
    "external_source_required",
    "extension_candidate",
    "blocked",
)

# Reserved: not derivable from current local data (see module docstring).
RESERVED_STATUS_VALUES = ("external_source_required", "extension_candidate")

REVIEW_REQUIRED_COVERAGE_STATUSES = frozenset({"standards_review_required"})


def build_hard_mapping_index(gdsn_path: str | Path) -> dict[str, tuple[bool, list[str]]]:
    """Index GDSN reference rows by bms_id -> (is_hard_mapping, reasons).

    Reuses the same deterministic detection rules as the Mapping Candidate
    Generator (Track B), applied here to whatever GDSN attributes are cited
    as evidence for a builder field, not to score new candidates.
    """
    index: dict[str, tuple[bool, list[str]]] = {}
    for row in load_gdsn_reference(str(gdsn_path)):
        bms_id = str(row.get("bms_id") or "").strip()
        if bms_id and bms_id not in index:
            index[bms_id] = detect_hard_mapping(row)
    return index


def _evidence_hard_mapping_reasons(
    evidence: list[dict[str, Any]] | None,
    hard_mapping_index: dict[str, tuple[bool, list[str]]] | None,
) -> list[str]:
    if not evidence or not hard_mapping_index:
        return []
    reasons: list[str] = []
    for item in evidence:
        bms_id = str(item.get("gdsn_bms_id") or item.get("bms_id") or "").strip()
        if not bms_id:
            continue
        is_hard, item_reasons = hard_mapping_index.get(bms_id, (False, []))
        if is_hard:
            reasons.extend(item_reasons)
    return reasons


def compute_field_status(
    metadata: dict[str, Any],
    *,
    value_present: bool,
    hard_mapping_index: dict[str, tuple[bool, list[str]]] | None = None,
) -> tuple[str, list[str]]:
    """Return (status, reasons) for one builder field.

    Priority (first match wins): blocked > missing > hard_mapping_review >
    codelist_pending > review_required > filled > empty-optional (reported
    as "filled" is false, so callers treat it as the neutral/untouched case
    -- not part of STATUS_VALUES, filtered out by callers that only display
    filled/flagged fields).
    """
    if not metadata.get("supported_in_v0_10", True):
        reason = str(metadata.get("planned_reason") or "Requires governed modelling.")
        return "blocked", [reason]

    requirement = str(metadata.get("requirement") or "optional")
    if requirement == "required" and not value_present:
        return "missing", ["Required field has no value yet."]

    hard_reasons = _evidence_hard_mapping_reasons(
        metadata.get("evidence"), hard_mapping_index
    )
    if hard_reasons:
        return "hard_mapping_review", hard_reasons

    input_type_override = metadata.get("input_type_override")
    if input_type_override == "code" and not (metadata.get("options") or []):
        return "codelist_pending", [
            "Controlled-vocabulary options are not yet populated for this field."
        ]

    if metadata.get("coverage_status") in REVIEW_REQUIRED_COVERAGE_STATUSES:
        return "review_required", ["Open standards-review item for this property."]

    if value_present:
        return "filled", []

    return "optional_empty", []


def summarize_field_statuses(statuses: list[str]) -> dict[str, int]:
    """Count fields per status, including the neutral optional_empty bucket."""
    counts = {status: 0 for status in (*STATUS_VALUES, "optional_empty")}
    for status in statuses:
        counts[status] = counts.get(status, 0) + 1
    return counts
