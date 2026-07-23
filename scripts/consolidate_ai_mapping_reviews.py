"""Consolidate independent AI mapping reviews without auto-promoting mappings."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from collections import Counter
from pathlib import Path


REVIEWERS = ("antigravity", "gemini", "deepresearch", "chatgpt")
DECISIONS = {"accept", "reject", "needs_human_review", "no_equivalent"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def normalize(value: str | None) -> str:
    return (value or "").strip()


def reviewer_vote(row: dict[str, str] | None, target: str) -> tuple[str, bool]:
    """Return a readable vote and whether it directly concerns ``target``."""
    if row is None:
        return "not_reviewed", False
    decision = normalize(row.get("decision"))
    proposal = normalize(row.get("proposed_webvoc_property"))
    if decision not in DECISIONS:
        return "invalid_decision", False
    if proposal == target:
        return decision, True
    if decision == "no_equivalent" and not proposal:
        return "no_equivalent", True
    if proposal:
        return f"alternative {proposal}: {decision}", False
    return decision, False


def consensus_for(attribute: str, target: str, indexes: dict[str, dict[str, dict[str, str]]]) -> dict[str, object]:
    votes: dict[str, str] = {}
    direct: list[str] = []
    alternative_accept = False
    confidence: list[float] = []
    for reviewer in REVIEWERS:
        row = indexes[reviewer].get(attribute)
        vote, is_direct = reviewer_vote(row, target)
        votes[reviewer] = vote
        if is_direct:
            direct.append(vote)
            if row and normalize(row.get("confidence_percent")):
                try:
                    confidence.append(float(row["confidence_percent"]))
                except ValueError:
                    pass
        elif vote.endswith(": accept"):
            alternative_accept = True

    counts = Counter(direct)
    accepts = counts["accept"]
    opposition = counts["reject"] + counts["no_equivalent"]
    if opposition or (accepts and alternative_accept):
        status = "conflicted"
        action = "Keep review-only; resolve conflicting semantics or target property."
    elif accepts == 4:
        status = "unanimous_accept"
        action = "Eligible for human promotion review; structure and codelists still required."
    elif accepts >= 3:
        status = "strong_accept_consensus"
        action = "Eligible for human promotion review; structure and codelists still required."
    elif accepts >= 2:
        status = "accept_consensus"
        action = "Keep review-only until remaining reviewer concerns are resolved."
    elif counts["no_equivalent"] >= 2 and not accepts:
        status = "no_equivalent_consensus"
        action = "Do not map to this WebVoc property."
    elif counts["needs_human_review"] or accepts:
        status = "human_review"
        action = "Keep review-only; authoritative standards review required."
    else:
        status = "insufficient_review"
        action = "Keep heuristic candidate only."

    return {
        "review_consensus_status": status,
        "reviewer_count": sum(v != "not_reviewed" for v in votes.values()),
        "accept_count": accepts,
        "needs_human_review_count": counts["needs_human_review"],
        "reject_count": counts["reject"],
        "no_equivalent_count": counts["no_equivalent"],
        "mean_reviewer_confidence": round(sum(confidence) / len(confidence), 1) if confidence else "",
        "reviewer_decisions": " | ".join(f"{name}={votes[name]}" for name in REVIEWERS),
        "recommended_action": action,
        "auto_emit": "false",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--antigravity", type=Path, required=True)
    parser.add_argument("--gemini", type=Path, required=True)
    parser.add_argument("--deepresearch", type=Path, required=True)
    parser.add_argument("--chatgpt", type=Path, required=True)
    parser.add_argument("--suggestions", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--web-json", type=Path)
    args = parser.parse_args()

    sources = {name: getattr(args, name) for name in REVIEWERS}
    rows_by_reviewer = {name: read_csv(path) for name, path in sources.items()}
    indexes = {
        name: {normalize(row.get("gdsn_attribute_name")): row for row in rows}
        for name, rows in rows_by_reviewer.items()
    }

    inputs_dir = args.output_dir / "input_reviews"
    inputs_dir.mkdir(parents=True, exist_ok=True)
    for name, path in sources.items():
        shutil.copyfile(path, inputs_dir / f"reviewer_decisions_{name}.csv")

    suggestions = read_csv(args.suggestions)
    enriched: list[dict[str, object]] = []
    consensus_rows: list[dict[str, object]] = []
    status_counts: Counter[str] = Counter()
    for row in suggestions:
        attribute = normalize(row.get("gdsn_attribute_name"))
        target = normalize(row.get("proposed_webvoc_property"))
        consensus = consensus_for(attribute, target, indexes)
        status_counts[str(consensus["review_consensus_status"])] += 1
        combined = {**row, **consensus}
        enriched.append(combined)
        consensus_rows.append(
            {
                "gdsn_attribute_name": attribute,
                "proposed_webvoc_property": target,
                "heuristic_match_percentage": row.get("match_percentage", ""),
                **consensus,
            }
        )

    extra_fields = [
        "review_consensus_status", "reviewer_count", "accept_count",
        "needs_human_review_count", "reject_count", "no_equivalent_count",
        "mean_reviewer_confidence", "reviewer_decisions", "recommended_action",
    ]
    suggestion_fields = list(suggestions[0]) + [field for field in extra_fields if field not in suggestions[0]]
    write_csv(args.suggestions, enriched, suggestion_fields)
    if args.web_json:
        args.web_json.parent.mkdir(parents=True, exist_ok=True)
        args.web_json.write_text(
            json.dumps(enriched, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    write_csv(
        args.output_dir / "ai_reviewer_consensus_for_suggestions.csv",
        consensus_rows,
        ["gdsn_attribute_name", "proposed_webvoc_property", "heuristic_match_percentage", *extra_fields, "auto_emit"],
    )

    summary = {
        "policy": "Reviewer consensus enriches review-only suggestions and never auto-emits JSON-LD.",
        "source_reviewers": {name: len(rows) for name, rows in rows_by_reviewer.items()},
        "suggestion_rows_analyzed": len(suggestions),
        "consensus_status_counts": dict(sorted(status_counts.items())),
        "promotion_rule": "Human approval remains required, including for unanimous AI acceptance.",
    }
    (args.output_dir / "ai_reviewer_consensus_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
