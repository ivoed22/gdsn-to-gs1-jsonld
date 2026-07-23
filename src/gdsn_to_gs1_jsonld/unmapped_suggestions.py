"""Review-only Web Vocabulary suggestions for populated unmapped GDSN fields.

Suggestion rows are deliberately separate from executable mapping profiles.
They may explain a possible target property, but never emit JSON-LD and never
mark a source value as mapped.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


MINIMUM_SUGGESTION_PERCENTAGE = 60.0
AUTO_MAPPING_PERCENTAGE = 90.0


class MappingSuggestionCatalogError(ValueError):
    """Raised when a mapping-suggestion catalog cannot be used safely."""


def _source_local_name(attribute_name: str) -> str:
    """Return the XML local-name represented by a normalized GDSN name."""
    value = attribute_name.strip().replace("\\", "/")
    # A compound path such as ``netContent/@measurementUnitCode`` cannot be
    # matched safely from a bare XML local-name: the same terminal field may
    # occur under many semantically different GDSN parents. Context-aware
    # matching can be added later; until then, do not guess.
    if "/" in value or value.startswith("@"):
        return ""
    return value


def load_mapping_suggestion_catalog(path: str | Path) -> list[dict[str, Any]]:
    """Load vetted-shape heuristic suggestions from a UTF-8 CSV file."""
    catalog_path = Path(path)
    try:
        with catalog_path.open(newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
    except OSError as exc:
        raise MappingSuggestionCatalogError(
            f"Cannot read mapping suggestion catalog: {catalog_path}"
        ) from exc

    required = {
        "gdsn_attribute_name",
        "proposed_webvoc_property",
        "match_percentage",
        "suggestion_status",
        "auto_emit",
    }
    if not rows:
        return []
    missing = required - set(rows[0])
    if missing:
        raise MappingSuggestionCatalogError(
            "Mapping suggestion catalog is missing columns: "
            + ", ".join(sorted(missing))
        )

    loaded: list[dict[str, Any]] = []
    for row_number, row in enumerate(rows, start=2):
        try:
            percentage = float(row.get("match_percentage") or 0)
        except ValueError as exc:
            raise MappingSuggestionCatalogError(
                f"Invalid match percentage on catalog row {row_number}."
            ) from exc
        if percentage < MINIMUM_SUGGESTION_PERCENTAGE:
            continue
        if str(row.get("auto_emit") or "").strip().lower() != "false":
            raise MappingSuggestionCatalogError(
                f"Catalog row {row_number} must have auto_emit=false."
            )
        loaded.append(
            {
                **row,
                "match_percentage": percentage,
                "second_percentage": _optional_float(row.get("second_percentage")),
                "third_percentage": _optional_float(row.get("third_percentage")),
                "source_local_name": _source_local_name(
                    str(row.get("gdsn_attribute_name") or "")
                ),
                "auto_emit": False,
            }
        )
    return loaded


def _optional_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def add_mapping_suggestions(
    unmapped_report: dict[str, Any],
    catalog: list[dict[str, Any]],
) -> dict[str, Any]:
    """Attach matching 60%+ candidates without changing mapped evidence."""
    index: dict[str, list[dict[str, Any]]] = {}
    for row in catalog:
        local_name = str(row.get("source_local_name") or "").strip().lower()
        if local_name:
            index.setdefault(local_name, []).append(row)

    present_elements = {
        str(item.get("element") or "").strip()
        for item in unmapped_report.get("unmapped_elements", [])
        if item.get("element")
    }
    suggestions: list[dict[str, Any]] = []
    for element in sorted(present_elements, key=str.lower):
        candidates = sorted(
            index.get(element.lower(), []),
            key=lambda row: (
                -float(row["match_percentage"]),
                str(row.get("gdsn_attribute_name") or ""),
                str(row.get("proposed_webvoc_property") or ""),
            ),
        )
        seen: set[tuple[str, str]] = set()
        for candidate in candidates:
            marker = (
                str(candidate.get("gdsn_attribute_name") or ""),
                str(candidate.get("proposed_webvoc_property") or ""),
            )
            if marker in seen:
                continue
            seen.add(marker)
            suggestions.append(
                {
                    "source_element": element,
                    "gdsn_attribute_name": candidate["gdsn_attribute_name"],
                    "proposed_webvoc_property": candidate[
                        "proposed_webvoc_property"
                    ],
                    "proposed_webvoc_label": candidate.get(
                        "proposed_webvoc_label", ""
                    ),
                    "proposed_webvoc_range": candidate.get(
                        "proposed_webvoc_range", ""
                    ),
                    "match_percentage": candidate["match_percentage"],
                    "suggestion_status": candidate["suggestion_status"],
                    "match_reasons": candidate.get("match_reasons", ""),
                    "second_candidate": candidate.get("second_candidate", ""),
                    "second_percentage": candidate.get("second_percentage"),
                    "third_candidate": candidate.get("third_candidate", ""),
                    "third_percentage": candidate.get("third_percentage"),
                    "source_versions": candidate.get("source_versions", ""),
                    "auto_emitted": False,
                    "review_required": True,
                }
            )

    enriched = dict(unmapped_report)
    enriched["policy"] = (
        "Populated source values not emitted by the active mapping profile. "
        "Values remain lossless source evidence. Possible 60%+ Web Vocabulary "
        "matches may be listed as review-only suggestions; they are never "
        "automatically emitted as JSON-LD."
    )
    enriched["mapping_suggestion_policy"] = {
        "minimum_match_percentage": MINIMUM_SUGGESTION_PERCENTAGE,
        "review_only_below_percentage": AUTO_MAPPING_PERCENTAGE,
        "auto_emit": False,
        "warning": (
            "A similarity score is not semantic approval. Verify definition, "
            "domain, range, cardinality, nesting and codelists before promotion."
        ),
    }
    enriched["mapping_suggestions"] = suggestions
    enriched["summary"] = {
        **dict(unmapped_report.get("summary", {})),
        "mapping_suggestion_count": len(suggestions),
        "mapping_suggestion_source_elements": len(
            {item["source_element"] for item in suggestions}
        ),
    }
    return enriched
