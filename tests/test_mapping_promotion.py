"""Tests for mapping candidate promotion lanes (v0.16.0 Track B).

Both lanes must reach the same terminal status (accepted); hard mappings are
a flag with a dedicated extra review gate, never a permanent block and never
a separate status. Nothing here writes mapping YAML or the mapping registry.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from gdsn_to_gs1_jsonld.mapping_registry import STATUS_VOCABULARY
from gdsn_to_gs1_jsonld.mapping_promotion import (
    REVIEW_LANES,
    annotate_promotion_fields,
    build_hard_mapping_signoff,
    build_promotion_artifact,
    compute_promotion_eligibility,
    derive_status,
    load_reviewed_hard_mappings,
    write_promotion_artifact,
)

ROOT = Path(__file__).resolve().parents[1]


def _candidate(**overrides) -> dict:
    base = {
        "candidate_id": "cand_gs1_gtin__100",
        "review_status": "proposed",
        "hard_mapping": False,
        "hard_mapping_reasons": [],
        "review_lane": "standard",
        "reasons": [],
        "warnings": [],
        "blocking_notes": [],
        "linked_sdr_ids": [],
    }
    base.update(overrides)
    return base


def test_review_lanes_are_fixed():
    assert REVIEW_LANES == ("standard", "hard_mapping")


def test_derive_status_maps_review_status_to_registry_vocabulary():
    assert derive_status(_candidate(review_status="proposed")) == "proposed"
    assert derive_status(_candidate(review_status="already_mapped")) == "accepted"
    assert derive_status(_candidate(review_status="review_required")) == "review_required"
    assert derive_status(_candidate(review_status="not_recommended")) == "rejected"


def test_derive_status_always_in_fixed_vocabulary():
    for review_status in ("proposed", "already_mapped", "review_required", "not_recommended"):
        assert derive_status(_candidate(review_status=review_status)) in STATUS_VOCABULARY


def test_no_hard_mapping_candidate_status_exists():
    assert "hard_mapping_candidate" not in STATUS_VOCABULARY


def test_standard_lane_eligible_when_not_blocked():
    candidate = _candidate(review_status="proposed", hard_mapping=False)
    eligible, note = compute_promotion_eligibility(candidate)
    assert eligible is True
    assert "eligible" in note.lower()


def test_standard_lane_blocked_when_review_required():
    candidate = _candidate(review_status="review_required", hard_mapping=False)
    eligible, _ = compute_promotion_eligibility(candidate)
    assert eligible is False


def test_hard_mapping_lane_never_eligible_without_dedicated_review():
    candidate = _candidate(
        review_status="proposed", hard_mapping=True, hard_mapping_reasons=["x"]
    )
    eligible, note = compute_promotion_eligibility(candidate, reviewed_hard_mapping_ids=set())
    assert eligible is False
    assert "dedicated" in note.lower()


def test_hard_mapping_lane_eligible_after_dedicated_review_same_terminal_status():
    """A hard-mapping candidate that passes dedicated review becomes eligible
    for exactly the same accepted status as a standard-lane candidate — the
    lane is a gate, not a separate destination."""
    candidate = _candidate(
        candidate_id="cand_gs1_brandName__200",
        review_status="proposed",
        hard_mapping=True,
        hard_mapping_reasons=["cross_class_reference_to_PartyIdentification: ..."],
    )
    eligible, note = compute_promotion_eligibility(
        candidate, reviewed_hard_mapping_ids={candidate["candidate_id"]}
    )
    assert eligible is True
    assert "dedicated extra review recorded" in note.lower()
    # Reaching "accepted" for a hard-mapping candidate still goes through
    # derive_status the same way as any other candidate once its
    # review_status is already_mapped/accepted-equivalent.
    accepted_hard = _candidate(
        candidate_id=candidate["candidate_id"],
        review_status="already_mapped",
        hard_mapping=True,
    )
    assert derive_status(accepted_hard) == "accepted"


def test_hard_mapping_never_promoted_if_scoring_itself_is_blocked():
    """Dedicated review sign-off does not override an unresolved scoring
    blocker (review_required/not_recommended) — that must be fixed first."""
    candidate = _candidate(
        candidate_id="cand_x",
        review_status="not_recommended",
        hard_mapping=True,
    )
    eligible, _ = compute_promotion_eligibility(
        candidate, reviewed_hard_mapping_ids={"cand_x"}
    )
    assert eligible is False


def test_annotate_promotion_fields_does_not_mutate_input():
    candidates = [_candidate()]
    original = dict(candidates[0])
    annotate_promotion_fields(candidates)
    assert candidates[0] == original


def test_build_promotion_artifact_splits_lanes_and_never_writes_mapping():
    candidates = [
        _candidate(candidate_id="std_1", review_status="proposed", hard_mapping=False),
        _candidate(
            candidate_id="hard_1",
            review_status="proposed",
            hard_mapping=True,
            hard_mapping_reasons=["reason"],
            review_lane="hard_mapping",
        ),
    ]
    artifact = build_promotion_artifact(candidates)
    assert artifact["summary"]["total_candidates"] == 2
    assert artifact["summary"]["standard_lane_count"] == 1
    assert artifact["summary"]["hard_mapping_lane_count"] == 1
    assert len(artifact["standard_lane"]) == 1
    assert len(artifact["hard_mapping_lane"]) == 1
    # hard_1 is not eligible without a recorded dedicated review.
    assert artifact["hard_mapping_lane"][0]["promotion_eligible"] is False
    assert artifact["standard_lane"][0]["promotion_eligible"] is True


def test_load_reviewed_hard_mappings_missing_file_returns_empty_set():
    assert load_reviewed_hard_mappings(None) == set()
    assert load_reviewed_hard_mappings("does/not/exist.json") == set()


def test_load_reviewed_hard_mappings_accepts_list_or_object(tmp_path):
    list_path = tmp_path / "reviewed_list.json"
    list_path.write_text(json.dumps(["a", "b", "b"]), encoding="utf-8")
    assert load_reviewed_hard_mappings(list_path) == {"a", "b"}

    object_path = tmp_path / "reviewed_object.json"
    object_path.write_text(
        json.dumps({"reviewed_candidate_ids": ["c"]}), encoding="utf-8"
    )
    assert load_reviewed_hard_mappings(object_path) == {"c"}


def test_build_hard_mapping_signoff_includes_only_approved_in_reviewed_ids():
    """v0.25.0: in-UI sign-off authoring. Only 'approved' decisions land in
    reviewed_candidate_ids -- the only key load_reviewed_hard_mappings
    actually reads; 'reviews' is additive audit metadata it ignores."""
    reviews = [
        {
            "candidate_id": "hard_1",
            "reviewer": "Alice",
            "date": "2026-07-04",
            "decision": "Approved",
            "notes": "Cross-reference confirmed against party master data.",
        },
        {
            "candidate_id": "hard_2",
            "reviewer": "Alice",
            "date": "2026-07-04",
            "decision": "Rejected",
            "notes": "Not a real cross-reference.",
        },
    ]

    signoff = build_hard_mapping_signoff(reviews)

    assert signoff["reviewed_candidate_ids"] == ["hard_1"]
    assert len(signoff["reviews"]) == 2
    assert signoff["reviews"][0]["decision"] == "approved"
    assert signoff["reviews"][1]["decision"] == "rejected"


def test_build_hard_mapping_signoff_ignores_blank_and_unreviewed_entries():
    reviews = [
        {"candidate_id": "hard_1", "decision": "Not reviewed"},
        {"candidate_id": "", "decision": "Approved"},
        {"candidate_id": "hard_2", "decision": "approved"},
    ]

    signoff = build_hard_mapping_signoff(reviews)

    assert signoff["reviewed_candidate_ids"] == ["hard_2"]


def test_build_hard_mapping_signoff_round_trips_through_load_reviewed_hard_mappings(
    tmp_path,
):
    """The authored file must be readable by the exact same loader used by
    both the CLI and the promotion pipeline -- no schema drift."""
    reviews = [
        {"candidate_id": "hard_1", "reviewer": "Alice", "decision": "approved"},
        {"candidate_id": "hard_2", "reviewer": "Alice", "decision": "rejected"},
    ]
    signoff = build_hard_mapping_signoff(reviews)
    path = tmp_path / "authored_signoff.json"
    path.write_text(json.dumps(signoff), encoding="utf-8")

    assert load_reviewed_hard_mappings(path) == {"hard_1"}


def test_write_promotion_artifact_writes_expected_files(tmp_path):
    candidates = [
        _candidate(candidate_id="std_1", review_status="proposed", hard_mapping=False),
        _candidate(
            candidate_id="hard_1",
            review_status="proposed",
            hard_mapping=True,
            hard_mapping_reasons=["reason"],
            review_lane="hard_mapping",
        ),
    ]
    artifact = build_promotion_artifact(candidates)
    paths = write_promotion_artifact(artifact, tmp_path)
    assert Path(paths["summary"]).is_file()
    assert Path(paths["standard_lane_json"]).is_file()
    assert Path(paths["hard_mapping_lane_json"]).is_file()
    assert Path(paths["eligible_for_promotion_json"]).is_file()

    written_summary = json.loads(Path(paths["summary"]).read_text(encoding="utf-8"))
    assert written_summary == artifact["summary"]

    # Nothing in the promotion artifact touches mapping YAML/registry files.
    mapping_dir = ROOT / "mapping"
    before = {p: p.read_bytes() for p in mapping_dir.glob("*.yaml")}
    write_promotion_artifact(artifact, tmp_path)
    after = {p: p.read_bytes() for p in mapping_dir.glob("*.yaml")}
    assert before == after
