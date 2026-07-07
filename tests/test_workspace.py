"""Tests for light workspace persistence (v0.35.0).

All tests run against tmp_path — never the real git-ignored workspace/
directory. The governance-relevant property is structural: the fixed
kind vocabulary plus fixed per-kind filenames make writing outside the
given workspace directory impossible.
"""

from __future__ import annotations

import pytest

from gdsn_to_gs1_jsonld.workspace import (
    ARTIFACT_KINDS,
    WorkspaceError,
    list_artifacts,
    load_artifact,
    save_artifact,
)


def test_save_load_roundtrip_for_every_kind(tmp_path):
    payloads = {
        "hard_mapping_signoff": {"reviewed_candidate_ids": ["a"], "reviews": []},
        "sdr_review_annotations": {"annotations": [{"sdr_id": "SDR-001"}]},
        "candidate_report": [{"candidate_id": "c1", "webvoc_property_id": "gs1:gtin"}],
    }
    assert set(payloads) == set(ARTIFACT_KINDS)

    for kind, payload in payloads.items():
        path = save_artifact(kind, payload, workspace_dir=tmp_path)
        assert path.parent == tmp_path
        assert path.name == f"{kind}.json"
        assert load_artifact(kind, workspace_dir=tmp_path) == payload


def test_save_overwrites_previous_artifact(tmp_path):
    save_artifact("candidate_report", [{"candidate_id": "old"}], workspace_dir=tmp_path)
    save_artifact("candidate_report", [{"candidate_id": "new"}], workspace_dir=tmp_path)

    assert load_artifact("candidate_report", workspace_dir=tmp_path) == [
        {"candidate_id": "new"}
    ]


def test_load_missing_or_corrupt_returns_none(tmp_path):
    assert load_artifact("candidate_report", workspace_dir=tmp_path) is None

    (tmp_path / "candidate_report.json").write_text("not json{", encoding="utf-8")
    assert load_artifact("candidate_report", workspace_dir=tmp_path) is None

    (tmp_path / "hard_mapping_signoff.json").write_text('"a string"', encoding="utf-8")
    assert load_artifact("hard_mapping_signoff", workspace_dir=tmp_path) is None


def test_unknown_kind_rejected_never_writes(tmp_path):
    with pytest.raises(WorkspaceError):
        save_artifact("mapping_registry", {"x": 1}, workspace_dir=tmp_path)
    with pytest.raises(WorkspaceError):
        load_artifact("../../mapping/mapping_registry.yaml", workspace_dir=tmp_path)  # type: ignore[arg-type]
    assert list(tmp_path.iterdir()) == []


def test_unserializable_payload_rejected(tmp_path):
    with pytest.raises(WorkspaceError):
        save_artifact("candidate_report", [{"bad": object()}], workspace_dir=tmp_path)  # type: ignore[list-item]
    assert list(tmp_path.iterdir()) == []


def test_list_artifacts_reports_existence(tmp_path):
    save_artifact("sdr_review_annotations", {"annotations": []}, workspace_dir=tmp_path)

    inventory = list_artifacts(workspace_dir=tmp_path)

    assert set(inventory) == set(ARTIFACT_KINDS)
    assert inventory["sdr_review_annotations"]["exists"] is True
    assert inventory["hard_mapping_signoff"]["exists"] is False
    for entry in inventory.values():
        assert str(tmp_path) in entry["path"]
