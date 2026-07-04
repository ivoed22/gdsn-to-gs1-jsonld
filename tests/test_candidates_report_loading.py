"""Tests for loading a previously generated candidate report (v0.28.0).

``parse_uploaded_candidate_report`` is a pure function (no Streamlit API
calls) so it is tested directly here; the Streamlit-facing "Load report"
button is covered separately in tests/test_streamlit_app.py via AppTest.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# pyproject.toml's pytest pythonpath only covers src/ (gdsn_to_gs1_jsonld),
# not the repo root -- app/ is normally only ever loaded via
# streamlit.testing.v1.AppTest.from_file, which handles its own sys.path
# setup (see app/workflow_shared.py's _ensure_import_paths). A plain import
# needs the repo root on sys.path explicitly; this worked locally by
# accident (running `python -m pytest` from the repo root implicitly adds
# cwd to sys.path) but not in CI, which runs plain `pytest`.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.workflows.candidates import parse_uploaded_candidate_report  # noqa: E402


def _candidate(**overrides) -> dict:
    base = {
        "candidate_id": "cand_1",
        "webvoc_property_id": "gs1:gtin",
        "gdsn_attribute_name": "gtin",
        "review_status": "proposed",
        "review_lane": "standard",
        "hard_mapping": False,
    }
    base.update(overrides)
    return base


def test_parses_valid_candidate_report():
    raw = json.dumps([_candidate(), _candidate(candidate_id="cand_2")]).encode("utf-8")

    parsed = parse_uploaded_candidate_report(raw)

    assert len(parsed) == 2
    assert {c["candidate_id"] for c in parsed} == {"cand_1", "cand_2"}


def test_rejects_non_json_bytes():
    with pytest.raises(ValueError, match="Could not parse"):
        parse_uploaded_candidate_report(b"not json")


def test_rejects_json_that_is_not_a_list():
    raw = json.dumps({"reviewed_candidate_ids": []}).encode("utf-8")

    with pytest.raises(ValueError, match="JSON array"):
        parse_uploaded_candidate_report(raw)


def test_rejects_list_with_no_recognizable_candidates():
    raw = json.dumps([{"foo": "bar"}, "not a dict"]).encode("utf-8")

    with pytest.raises(ValueError, match="No recognizable candidate"):
        parse_uploaded_candidate_report(raw)


def test_skips_entries_missing_required_fields_but_keeps_valid_ones():
    raw = json.dumps(
        [_candidate(), {"candidate_id": "incomplete"}, "not a dict"]
    ).encode("utf-8")

    parsed = parse_uploaded_candidate_report(raw)

    assert len(parsed) == 1
    assert parsed[0]["candidate_id"] == "cand_1"
