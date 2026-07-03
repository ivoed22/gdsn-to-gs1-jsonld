"""Mapping candidate promotion lanes (v0.16.0 Track B).

Every scored candidate (see :mod:`mapping_candidate_generator`) routes
through one of two review lanes on the way to the same terminal status:

- **standard lane** — score -> review -> ``accepted``.
- **hard-mapping lane** — score -> dedicated extra review -> ``accepted``.

``hard_mapping`` is a flag with reasons (set by
:func:`mapping_candidate_generator.detect_hard_mapping`), never a status.
There is no ``hard_mapping_candidate`` status and no permanent block: a
hard-mapping candidate reaches exactly the same ``accepted`` status as a
standard-lane candidate once its dedicated review passes.

This module never writes mapping YAML or the mapping registry. Promotions
are exported as a reviewable artifact (JSON/CSV) for a human to act on;
turning a promotion into a governed mapping entry remains a separate,
deliberate standards decision.
"""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any

from .mapping_registry import STATUS_VOCABULARY

REVIEW_LANES = ("standard", "hard_mapping")

# review_status (mapping_candidate_generator) -> registry status vocabulary.
_REVIEW_STATUS_TO_REGISTRY_STATUS: dict[str, str] = {
    "already_mapped": "accepted",
    "proposed": "proposed",
    "review_required": "review_required",
    "not_recommended": "rejected",
}


def load_reviewed_hard_mappings(path: str | Path | None) -> set[str]:
    """Load candidate_ids that already passed dedicated hard-mapping review.

    This is the human sign-off record for the hard-mapping lane's extra
    review gate. Missing or empty input is treated as "nothing reviewed
    yet" rather than an error, since no hard mapping has been reviewed by
    default.
    """
    if not path:
        return set()
    file_path = Path(path)
    if not file_path.is_file():
        return set()
    try:
        raw = json.loads(file_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    if isinstance(raw, dict):
        raw = raw.get("reviewed_candidate_ids", [])
    if not isinstance(raw, list):
        return set()
    return {str(item).strip() for item in raw if str(item).strip()}


def derive_status(candidate: dict[str, Any]) -> str:
    """Map a candidate's review_status onto the fixed registry status
    vocabulary (proposed/review_required/accepted/rejected/deprecated/blocked).
    """
    status = _REVIEW_STATUS_TO_REGISTRY_STATUS.get(
        candidate.get("review_status", "proposed"), "review_required"
    )
    assert status in STATUS_VOCABULARY, status
    return status


def compute_promotion_eligibility(
    candidate: dict[str, Any],
    reviewed_hard_mapping_ids: set[str] | None = None,
) -> tuple[bool, str]:
    """Return (promotion_eligible, review_note) for one candidate.

    Standard lane: eligible once the scorer's own review_status carries no
    blocker (i.e. not ``review_required`` and not ``not_recommended``).
    Hard-mapping lane: never eligible from scoring alone — it additionally
    requires the candidate_id to appear in the dedicated hard-mapping review
    sign-off set. Passing that gate makes it eligible for the same
    ``accepted`` status as the standard lane; it is not a separate status.
    """
    reviewed_hard_mapping_ids = reviewed_hard_mapping_ids or set()
    review_status = candidate.get("review_status", "proposed")
    scoring_blocked = review_status in {"review_required", "not_recommended"}

    if not candidate.get("hard_mapping"):
        if scoring_blocked:
            return False, f"Review support only: review_status is {review_status!r}."
        return True, "Standard lane: eligible for review-based promotion to accepted."

    if scoring_blocked:
        return False, (
            f"Hard mapping: review_status is {review_status!r}; resolve before "
            "dedicated review."
        )
    candidate_id = str(candidate.get("candidate_id") or "")
    if candidate_id in reviewed_hard_mapping_ids:
        return True, (
            "Hard mapping: dedicated extra review recorded; eligible for "
            "promotion to accepted."
        )
    return False, (
        "Hard mapping: requires dedicated extra review (cross-reference or "
        "identifier outside the current product message) before it is "
        "eligible for promotion, regardless of score."
    )


def annotate_promotion_fields(
    candidates: list[dict[str, Any]],
    reviewed_hard_mapping_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Return copies of *candidates* with status/promotion fields attached.

    Adds ``status`` (fixed vocabulary), ``promotion_eligible``, and
    ``review_notes`` without mutating the input list. ``review_lane`` and
    ``hard_mapping``/``hard_mapping_reasons`` are expected to already be
    present (set by :mod:`mapping_candidate_generator`).
    """
    reviewed_hard_mapping_ids = reviewed_hard_mapping_ids or set()
    annotated: list[dict[str, Any]] = []
    for candidate in candidates:
        new_candidate = dict(candidate)
        new_candidate.setdefault("review_lane", "standard")
        new_candidate.setdefault("hard_mapping", False)
        new_candidate.setdefault("hard_mapping_reasons", [])
        new_candidate["status"] = derive_status(new_candidate)
        eligible, note = compute_promotion_eligibility(
            new_candidate, reviewed_hard_mapping_ids
        )
        new_candidate["promotion_eligible"] = eligible
        new_candidate["review_notes"] = note
        annotated.append(new_candidate)
    return annotated


def build_promotion_artifact(
    candidates: list[dict[str, Any]],
    reviewed_hard_mapping_ids: set[str] | None = None,
) -> dict[str, Any]:
    """Build the full reviewable promotion artifact from scored candidates.

    Review support only. Nothing here writes mapping YAML, the mapping
    registry, or the mapping catalog; promoting a candidate into a governed
    mapping entry remains a separate, deliberate standards decision.
    """
    annotated = annotate_promotion_fields(candidates, reviewed_hard_mapping_ids)
    standard_lane = [c for c in annotated if c["review_lane"] == "standard"]
    hard_mapping_lane = [c for c in annotated if c["review_lane"] == "hard_mapping"]
    eligible_for_promotion = [c for c in annotated if c["promotion_eligible"]]

    by_status: dict[str, int] = {status: 0 for status in STATUS_VOCABULARY}
    for candidate in annotated:
        by_status[candidate["status"]] = by_status.get(candidate["status"], 0) + 1

    summary = {
        "total_candidates": len(annotated),
        "standard_lane_count": len(standard_lane),
        "hard_mapping_lane_count": len(hard_mapping_lane),
        "eligible_for_promotion_count": len(eligible_for_promotion),
        "hard_mapping_reviewed_count": len(reviewed_hard_mapping_ids or set()),
        "by_status": by_status,
    }
    return {
        "summary": summary,
        "all_candidates": annotated,
        "standard_lane": standard_lane,
        "hard_mapping_lane": hard_mapping_lane,
        "eligible_for_promotion": eligible_for_promotion,
    }


def _csv_bytes(rows: list[dict[str, Any]]) -> bytes:
    if not rows:
        return b""
    from .mapping_candidate_generator import candidate_to_dict

    flat_rows = [candidate_to_dict(row) for row in rows]
    fieldnames = list(flat_rows[0].keys())
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    writer.writerows(flat_rows)
    return buf.getvalue().encode("utf-8")


def write_promotion_artifact(
    artifact: dict[str, Any],
    output_dir: str | Path,
) -> dict[str, str]:
    """Write the promotion artifact (summary + per-lane JSON/CSV reports)."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}

    summary_path = out / "promotion_summary.json"
    summary_path.write_bytes(
        json.dumps(artifact["summary"], indent=2, ensure_ascii=False).encode("utf-8")
    )
    paths["summary"] = str(summary_path)

    for key, filename in (
        ("standard_lane", "promotion_standard_lane"),
        ("hard_mapping_lane", "promotion_hard_mapping_lane"),
        ("eligible_for_promotion", "promotion_eligible"),
    ):
        rows = artifact[key]
        json_path = out / f"{filename}.json"
        json_path.write_bytes(
            json.dumps(rows, indent=2, ensure_ascii=False).encode("utf-8")
        )
        paths[f"{key}_json"] = str(json_path)

        csv_bytes = _csv_bytes(rows)
        if csv_bytes:
            csv_path = out / f"{filename}.csv"
            csv_path.write_bytes(csv_bytes)
            paths[f"{key}_csv"] = str(csv_path)

    return paths
