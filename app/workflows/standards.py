"""Standards Review workflow (read-only SDR/governance status)."""

from __future__ import annotations

import json
import re

import pandas as pd
import streamlit as st

from app.ui import render_section_header
from app.workflow_shared import REPOSITORY_ROOT, _backlog_categories
from gdsn_to_gs1_jsonld.standards_backlog import (
    VALID_DECISION_STATUSES,
    build_sdr_review_annotation,
)
from gdsn_to_gs1_jsonld.webvoc_monitor import compare_webvoc_snapshot_bytes

_NOT_REVIEWED = "Not reviewed"
_PROPOSED_STATUS_OPTIONS = (_NOT_REVIEWED, *sorted(VALID_DECISION_STATUSES - {"open"}))


def render_standards_review_mode(backlog: list[dict]) -> None:
    categories = _backlog_categories(backlog)
    with st.container(border=True):
        render_section_header(
            1,
            "Standards Review",
            "Read-only status for open standards and governance decisions.",
        )
        count_column, category_column = st.columns([1, 2])
        count_column.metric("Open SDRs", len(backlog))
        category_column.markdown(
            "**Categories**\n\n"
            + (", ".join(categories) if categories else "metadata unavailable")
        )
        st.markdown("**Register**")
        st.code("docs/standards-decisions/index.md")
        st.info(
            "These are standards/governance decisions, not runtime converter failures."
        )

    _render_vocabulary_freshness_check()
    _render_sdr_review_annotation(backlog)


def _render_vocabulary_freshness_check() -> None:
    """Offline comparison against the pinned WebVoc snapshot (v0.24.0).

    This project never fetches vocabulary resources itself; the comparison
    file is provided by the reviewer. Diagnostic only -- does not update
    the committed snapshot, mapping catalog, or any governed data.
    """
    with st.container(border=True):
        render_section_header(
            2,
            "Vocabulary freshness check",
            "Compare the pinned local GS1 Web Vocabulary snapshot against a "
            "candidate updated file you provide. Fully offline: this project "
            "never fetches vocabulary resources itself.",
        )
        uploaded_file = st.file_uploader(
            "Candidate gs1Voc.jsonld",
            type=["jsonld", "json"],
            help=(
                "Upload a JSON-LD file shaped like webvoc/current/gs1Voc.jsonld "
                "(e.g. a newer official export) to see what would change."
            ),
        )
        if uploaded_file is None:
            st.caption(
                "No file uploaded yet. See docs/webvoc-update-monitor.md for the "
                "CLI-based network check (`check-webvoc-updates`), a separate, "
                "explicitly human-invoked operation."
            )
            return

        try:
            result = compare_webvoc_snapshot_bytes(
                REPOSITORY_ROOT / "webvoc" / "current", uploaded_file.getvalue()
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            st.error(f"Could not compare the uploaded file: {exc}")
            return

        metric_columns = st.columns(4)
        metric_columns[0].metric("Local terms", result["local_term_count"])
        metric_columns[1].metric("Uploaded terms", result["comparison_term_count"])
        metric_columns[2].metric("New terms", len(result["new_terms"]))
        metric_columns[3].metric("Changed terms", len(result["changed_terms"]))
        st.caption(
            f"Local version: {result['local_version'] or 'unknown'} · "
            f"Uploaded version: {result['comparison_version'] or 'unknown'}"
        )

        if not result["changed"]:
            st.success("No differences detected against the local snapshot.")
            return

        st.warning(
            f"{len(result['new_terms'])} new, "
            f"{len(result['removed_terms'])} removed, "
            f"{len(result['changed_terms'])} changed term(s) detected."
        )
        with st.expander("Open term differences"):
            st.dataframe(
                pd.DataFrame(
                    {
                        "New terms": pd.Series(result["new_terms"]),
                        "Removed terms": pd.Series(result["removed_terms"]),
                        "Changed terms": pd.Series(result["changed_terms"]),
                    }
                ),
                hide_index=True,
                use_container_width=True,
            )
        st.caption(
            "Diagnostic only. Updating the committed snapshot or mapping catalog "
            "is a separate, explicit review step."
        )


def _annotation_key(sdr_id: str, suffix: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_]+", "_", sdr_id).strip("_") or "sdr"
    return f"sdr_review_annotation_{safe}_{suffix}"


def _render_sdr_review_annotation(backlog: list[dict]) -> None:
    """Record a proposed reviewer/date/status per open SDR (v0.29.0).

    First slice of the "Standards-review workflow (future)" roadmap item:
    intentionally not the full state machine (named-reviewer assignment,
    moving records through Proposed/Accepted/Rejected/Deferred, versioned
    mapping changes for accepted decisions). This only lets a reviewer
    record a proposal and download it -- it never writes to
    docs/standards-decisions/standards_review_backlog.json (governed data)
    and never changes an SDR's status in this session.
    """
    if not backlog:
        return

    with st.container(border=True):
        render_section_header(
            3,
            "Record a review annotation",
            "Propose a reviewer, decision date, and target status for an "
            "open SDR below, then download the annotation. This is a "
            "record of a proposal, not an applied decision -- it does not "
            "change any SDR's status or write to the governed backlog file.",
        )
        annotations: list[dict] = []
        for item in backlog:
            sdr_id = str(item.get("sdr_id") or item.get("id") or "")
            if not sdr_id:
                continue
            with st.container(border=True):
                st.caption(f"**{sdr_id}** — {item.get('title', '')}")
                reviewer_col, date_col, status_col, notes_col = st.columns(
                    [1.2, 1, 1, 1.6]
                )
                reviewer = reviewer_col.text_input(
                    "Reviewer",
                    key=_annotation_key(sdr_id, "reviewer"),
                )
                decision_date = date_col.date_input(
                    "Decision date",
                    key=_annotation_key(sdr_id, "date"),
                )
                proposed_status = status_col.selectbox(
                    "Proposed status",
                    _PROPOSED_STATUS_OPTIONS,
                    key=_annotation_key(sdr_id, "status"),
                )
                notes = notes_col.text_input(
                    "Notes",
                    key=_annotation_key(sdr_id, "notes"),
                )
            if proposed_status != _NOT_REVIEWED:
                annotations.append(
                    {
                        "sdr_id": sdr_id,
                        "reviewer": reviewer,
                        "decision_date": str(decision_date),
                        "proposed_status": proposed_status,
                        "notes": notes,
                    }
                )

        if not annotations:
            st.caption(
                "Set a Proposed status for at least one SDR to enable download."
            )
            return

        annotation_artifact = build_sdr_review_annotation(annotations)
        st.caption(f"{len(annotation_artifact['annotations'])} annotation(s) recorded.")
        st.download_button(
            "Download review annotations JSON",
            data=json.dumps(
                annotation_artifact, indent=2, ensure_ascii=False
            ).encode("utf-8"),
            file_name="sdr_review_annotations.json",
            mime="application/json",
            use_container_width=True,
        )
