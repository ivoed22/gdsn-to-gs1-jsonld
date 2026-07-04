"""Standards Review workflow (read-only SDR/governance status)."""

from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from app.ui import render_section_header
from app.workflow_shared import REPOSITORY_ROOT, _backlog_categories
from gdsn_to_gs1_jsonld.webvoc_monitor import compare_webvoc_snapshot_bytes


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
