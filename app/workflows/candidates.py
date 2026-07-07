"""Generate Mapping Candidates workflow."""

from __future__ import annotations

import json
import re

import streamlit as st

from app.ui import render_download_intro, render_section_header, render_status_badge
from app.workflow_shared import REPOSITORY_ROOT, navigate_to_webvoc_property
from gdsn_to_gs1_jsonld.mapping_candidate_generator import (
    build_candidate_inputs,
    candidate_report_bytes_csv,
    candidate_report_bytes_json,
    candidate_report_bytes_xlsx,
    filter_candidates,
    generate_all_candidates,
    generate_candidate_summary,
    generate_candidates_for_property,
)
from gdsn_to_gs1_jsonld.mapping_promotion import (
    build_hard_mapping_signoff,
    build_promotion_artifact,
)

_SIGNOFF_DECISIONS = ("Not reviewed", "Approved", "Rejected")

# Status-badge tone per fixed registry status (mapping_registry.STATUS_VOCABULARY).
_STATUS_BADGE_TONES = {
    "accepted": "accepted",
    "proposed": "current",
    "review_required": "review",
    "rejected": "blocked",
    "deprecated": "blocked",
    "blocked": "blocked",
}


@st.cache_data(show_spinner=False)
def load_candidate_inputs() -> object:
    """Load and index all candidate generation inputs (cached)."""
    return build_candidate_inputs(
        webvoc_path=str(
            REPOSITORY_ROOT / "reference_data" / "normalized" / "webvoc_properties_1_17.csv"
        ),
        gdsn_path=str(
            REPOSITORY_ROOT
            / "reference_data"
            / "normalized"
            / "gdsn_attributes_bms_xpath_3_1_36.csv"
        ),
        catalog_path=str(
            REPOSITORY_ROOT
            / "mapping_catalog"
            / "gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_3_webvoc_validated.csv"
        ),
        mapping_path=str(
            REPOSITORY_ROOT / "mapping" / "mapping_registry.yaml"
        ),
        backlog_path=str(
            REPOSITORY_ROOT
            / "docs"
            / "standards-decisions"
            / "standards_review_backlog.json"
        ),
    )


def _parse_reviewed_hard_mapping_ids(uploaded_file) -> set[str]:
    """Parse an uploaded hard-mapping review sign-off JSON into candidate_ids."""
    if uploaded_file is None:
        return set()
    try:
        raw = json.loads(uploaded_file.getvalue().decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        st.warning(f"Could not parse hard-mapping review file: {exc}")
        return set()
    if isinstance(raw, dict):
        raw = raw.get("reviewed_candidate_ids", [])
    if not isinstance(raw, list):
        return set()
    return {str(item).strip() for item in raw if str(item).strip()}


def _signoff_key(candidate_id: str, suffix: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_]+", "_", candidate_id).strip("_") or "candidate"
    return f"hard_mapping_signoff_{safe}_{suffix}"


def _render_hard_mapping_signoff_authoring(
    hard_mapping_candidates: list[dict],
) -> None:
    """In-UI authoring for the hard-mapping review sign-off file (v0.25.0).

    Convenience only: builds a JSON file matching exactly the schema
    ``mapping_promotion.load_reviewed_hard_mappings`` already reads, so a
    reviewer no longer has to hand-edit that file externally. This does
    not change promotion eligibility by itself, and does not write to any
    governed file -- the reviewer downloads the file and uploads it back
    through the existing "Hard-mapping review sign-off" uploader above to
    see updated eligibility.
    """
    if not hard_mapping_candidates:
        return

    with st.container(border=True):
        render_section_header(
            5,
            "Author hard-mapping review sign-off",
            "Record a dedicated review decision for each hard-mapping-lane "
            "candidate below, then download a sign-off file. Upload it back "
            "through the sign-off field above and regenerate candidates to "
            "see updated promotion eligibility.",
        )
        reviews: list[dict] = []
        for candidate in hard_mapping_candidates:
            candidate_id = str(candidate.get("candidate_id") or "")
            if not candidate_id:
                continue
            with st.container(border=True):
                st.caption(
                    f"`{candidate.get('webvoc_property_id', '')}` / "
                    f"`{candidate.get('gdsn_attribute_name', '')}` "
                    f"(candidate_id: `{candidate_id}`)"
                )
                reviewer_col, date_col, decision_col, notes_col = st.columns(
                    [1.2, 1, 1, 1.6]
                )
                reviewer = reviewer_col.text_input(
                    "Reviewer",
                    key=_signoff_key(candidate_id, "reviewer"),
                )
                review_date = date_col.date_input(
                    "Date",
                    key=_signoff_key(candidate_id, "date"),
                )
                decision = decision_col.selectbox(
                    "Decision",
                    _SIGNOFF_DECISIONS,
                    key=_signoff_key(candidate_id, "decision"),
                )
                notes = notes_col.text_input(
                    "Notes",
                    key=_signoff_key(candidate_id, "notes"),
                )
            if decision != "Not reviewed":
                reviews.append(
                    {
                        "candidate_id": candidate_id,
                        "reviewer": reviewer,
                        "date": str(review_date),
                        "decision": decision,
                        "notes": notes,
                    }
                )

        if not reviews:
            st.caption("Set a Decision for at least one candidate to enable download.")
            return

        signoff = build_hard_mapping_signoff(reviews)
        approved_count = len(signoff["reviewed_candidate_ids"])
        rejected_count = len(reviews) - approved_count
        st.caption(f"{approved_count} approved, {rejected_count} rejected.")
        st.download_button(
            "Download hard-mapping review sign-off JSON",
            data=json.dumps(signoff, indent=2, ensure_ascii=False).encode("utf-8"),
            file_name="hard_mapping_review_signoff.json",
            mime="application/json",
            width="stretch",
        )


def _store_candidate_results(
    candidates: list[dict], reviewed_hard_mapping_ids: set[str]
) -> None:
    """Annotate candidates with promotion fields and persist for rendering.

    Shared by both the live "Generate Candidates" path and the v0.28.0
    "Load a previously generated report" path, so both end up rendered by
    the exact same downstream UI (metrics, table, detail, sign-off
    authoring, downloads) with no duplicated logic.
    """
    promotion_artifact = build_promotion_artifact(candidates, reviewed_hard_mapping_ids)
    candidates = promotion_artifact["all_candidates"]
    st.session_state["candidate_results"] = candidates
    st.session_state["promotion_summary"] = promotion_artifact["summary"]
    st.session_state["candidate_json_bytes"] = candidate_report_bytes_json(candidates)
    st.session_state["candidate_csv_bytes"] = candidate_report_bytes_csv(candidates)
    xlsx_bytes = candidate_report_bytes_xlsx(candidates)
    if xlsx_bytes:
        st.session_state["candidate_xlsx_bytes"] = xlsx_bytes


def parse_uploaded_candidate_report(raw_bytes: bytes) -> list[dict]:
    """Parse and validate an uploaded candidate report JSON (v0.28.0).

    Accepts the same shape ``candidate_report_bytes_json`` produces: a flat
    JSON array of candidate dicts. This is how a reviewer loads a report
    from a previous session, or from the CLI's ``--full-scope`` sweep (all
    553 WebVoc properties x ~6,067 GDSN attributes, ~7 minutes offline --
    too slow to re-run inside a single Streamlit interaction), instead of
    regenerating it live.

    Raises ``ValueError`` with a human-readable message on anything that
    isn't a JSON array of candidate-shaped objects (each must at least have
    ``candidate_id`` and ``webvoc_property_id``). Returns only the valid
    entries; the caller is responsible for warning about any skipped ones.
    """
    try:
        raw = json.loads(raw_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(f"Could not parse candidate report: {exc}") from exc
    if not isinstance(raw, list):
        raise ValueError("Candidate report must be a JSON array of candidate objects.")
    required_keys = {"candidate_id", "webvoc_property_id"}
    valid = [
        item
        for item in raw
        if isinstance(item, dict) and required_keys.issubset(item)
    ]
    if not valid:
        raise ValueError(
            "No recognizable candidate objects found (each needs at least "
            "'candidate_id' and 'webvoc_property_id')."
        )
    return valid


def render_mapping_candidates_workflow() -> None:
    """Render the Generate Mapping Candidates workflow page."""
    with st.container(border=True):
        render_section_header(
            1,
            "Generate Mapping Candidates",
            "Propose possible GDSN/BMS/XPath source fields for GS1 Web Vocabulary "
            "properties. Candidates are review support only.",
        )
        st.warning(
            "Review support only. Candidates are proposals, not accepted mappings. "
            "They do not update mapping YAML, the mapping catalog, or converter "
            "behavior. Review each candidate before any mapping decision is made."
        )

    try:
        inputs = load_candidate_inputs()
    except (FileNotFoundError, OSError, ValueError) as exc:
        st.error(
            f"Mapping Candidate Generator could not load local reference data: {exc}"
        )
        return

    webvoc_ids = sorted(
        str(row.get("term_id") or "").strip()
        for row in inputs["webvoc_rows"]
        if row.get("term_id")
    )

    with st.container(border=True):
        render_section_header(
            2,
            "Controls",
            "Select a property or generate candidates for all properties.",
        )
        all_props_option = "All properties"
        property_options = [all_props_option] + webvoc_ids
        selected_property = st.selectbox(
            "WebVoc property",
            property_options,
            help="Select a specific property or 'All properties'.",
        )
        if selected_property == all_props_option:
            st.caption(
                "All properties scores every WebVoc property in this "
                "session; a true full-scope sweep against all GDSN "
                "attributes can take several minutes. For the full offline "
                "sweep use the CLI: "
                "`gdsn-to-gs1-jsonld generate-mapping-candidates --full-scope`."
            )
        lane_options = ["All lanes", "standard", "hard_mapping"]
        selected_lane = st.selectbox(
            "Review lane",
            lane_options,
            help=(
                "Standard lane: score -> review -> accepted. Hard-mapping "
                "lane: score -> dedicated extra review -> accepted (never a "
                "permanent block)."
            ),
        )
        reviewed_hard_mappings_file = st.file_uploader(
            "Hard-mapping review sign-off (optional JSON)",
            type=["json"],
            help=(
                "A JSON file listing candidate_ids that already passed "
                "dedicated hard-mapping review. Without it, no hard-mapping "
                "candidate shows as eligible for promotion."
            ),
        )
        # Progressive disclosure (v0.33.0): the five filter controls sit in
        # a collapsed expander so the page leads with the two decisions
        # that matter (property, lane) and its one primary action. All
        # defaults are unchanged — expanding is optional.
        with st.expander("Filters", expanded=False):
            confidence_options = ["high", "medium", "low", "review_required"]
            selected_confidence = st.multiselect(
                "Confidence levels to include",
                confidence_options,
                default=["high", "medium", "low"],
                help="Filter candidates by confidence level.",
            )
            review_status_options = ["proposed", "already_mapped", "review_required", "not_recommended"]
            selected_review_statuses = st.multiselect(
                "Review statuses to include",
                review_status_options,
                default=["proposed", "already_mapped", "review_required"],
                help="Filter candidates by review status.",
            )
            include_already_mapped = st.checkbox(
                "Include already mapped",
                value=True,
                help="Include candidates where this property is already in the mapping catalog.",
            )
            include_low_conf = st.checkbox(
                "Include low confidence",
                value=True,
                help="Include candidates scored below medium confidence threshold.",
            )
            limit_per_prop = st.number_input(
                "Limit per property",
                min_value=1,
                max_value=50,
                value=20,
                step=1,
                help="Maximum candidate GDSN attributes per WebVoc property.",
            )
        generate_button = st.button(
            "Generate Candidates",
            type="primary",
            width="stretch",
        )

        st.markdown("---")
        st.caption(
            "Already have a report from a previous session, or from the "
            "CLI's `generate-mapping-candidates --full-scope` sweep (all "
            "553 properties x ~6,067 GDSN attributes, ~7 min offline -- too "
            "slow to run inside one Streamlit interaction)? Load it instead "
            "of regenerating."
        )
        uploaded_report_file = st.file_uploader(
            "Load a previously generated candidate report (JSON)",
            type=["json"],
            key="candidate_report_uploader",
            help=(
                "Accepts the JSON candidate report downloaded from this "
                "workflow, or the `mapping_candidates.json` the CLI writes "
                "(with or without --full-scope). Promotion eligibility is "
                "recomputed using the hard-mapping sign-off file above, if "
                "any."
            ),
        )
        load_report_button = st.button(
            "Load report",
            disabled=uploaded_report_file is None,
            width="stretch",
        )

    if load_report_button and uploaded_report_file is not None:
        try:
            loaded_candidates = parse_uploaded_candidate_report(
                uploaded_report_file.getvalue()
            )
        except ValueError as exc:
            st.error(str(exc))
        else:
            reviewed_hard_mapping_ids = _parse_reviewed_hard_mapping_ids(
                reviewed_hard_mappings_file
            )
            _store_candidate_results(loaded_candidates, reviewed_hard_mapping_ids)
            st.success(f"Loaded {len(loaded_candidates)} candidate(s) from the report.")

    if generate_button:
        with st.spinner("Generating mapping candidates..."):
            if selected_property == all_props_option:
                raw_candidates = generate_all_candidates(
                    inputs, limit_per_property=int(limit_per_prop)
                )
            else:
                raw_candidates = generate_candidates_for_property(
                    selected_property, inputs, limit=int(limit_per_prop)
                )

            # Apply confidence filter.
            min_conf = "high"
            if "low" in selected_confidence:
                min_conf = "low"
            elif "medium" in selected_confidence:
                min_conf = "medium"

            candidates = filter_candidates(
                raw_candidates,
                min_confidence=min_conf,
                include_low_confidence=include_low_conf,
                include_review_required="review_required" in selected_confidence,
            )
            # Apply review status filter.
            if selected_review_statuses:
                if not include_already_mapped:
                    selected_review_statuses = [
                        s for s in selected_review_statuses if s != "already_mapped"
                    ]
                candidates = [
                    c for c in candidates
                    if c.get("review_status") in selected_review_statuses
                ]
            # Apply review-lane filter.
            if selected_lane != "All lanes":
                candidates = [
                    c for c in candidates if c.get("review_lane") == selected_lane
                ]

            reviewed_hard_mapping_ids = _parse_reviewed_hard_mapping_ids(
                reviewed_hard_mappings_file
            )
            _store_candidate_results(candidates, reviewed_hard_mapping_ids)

    candidates_result = st.session_state.get("candidate_results")
    if candidates_result is not None:
        summary = generate_candidate_summary(candidates_result)
        promotion_summary = st.session_state.get("promotion_summary", {})
        with st.container(border=True):
            render_section_header(
                3,
                "Candidate Metrics",
                "Review-only counts. No mappings are created or applied.",
            )
            m1, m2, m3, m4, m5, m6 = st.columns(6)
            m1.metric("Total candidates", summary["total_candidates"])
            m2.metric("High confidence", summary["by_confidence"].get("high", 0))
            m3.metric("Medium confidence", summary["by_confidence"].get("medium", 0))
            m4.metric("Low confidence", summary["by_confidence"].get("low", 0))
            m5.metric("Review required", summary["by_confidence"].get("review_required", 0))
            m6.metric("Already mapped", summary["by_review_status"].get("already_mapped", 0))

            st.caption(
                "Promotion lanes — standard: score → review → accepted. "
                "Hard-mapping: score → dedicated extra review → accepted "
                "(never a permanent block)."
            )
            p1, p2, p3, p4 = st.columns(4)
            p1.metric("Standard lane", promotion_summary.get("standard_lane_count", 0))
            p2.metric(
                "Hard-mapping lane", promotion_summary.get("hard_mapping_lane_count", 0)
            )
            p3.metric(
                "Eligible for promotion",
                promotion_summary.get("eligible_for_promotion_count", 0),
            )
            p4.metric(
                "Hard-mapping reviews recorded",
                promotion_summary.get("hard_mapping_reviewed_count", 0),
            )

        with st.container(border=True):
            render_section_header(
                4,
                "Candidate Table",
                "Review candidates before any mapping decision. "
                "This table does not accept or write any mapping.",
            )
            if candidates_result:
                import pandas as pd

                table_rows = [
                    {
                        "WebVoc property": c.get("webvoc_property_id", ""),
                        "GDSN attribute name": c.get("gdsn_attribute_name", ""),
                        "BMS ID": c.get("gdsn_bms_id", ""),
                        "Score": c.get("score", 0.0),
                        "Confidence": c.get("confidence_level", ""),
                        "Review status": c.get("review_status", ""),
                        "Lane": c.get("review_lane", "standard"),
                        "Status": c.get("status", ""),
                        "Eligible for promotion": c.get("promotion_eligible", False),
                        "Top reason": (c.get("reasons") or [""])[0],
                        "SDR linked": "; ".join(str(s) for s in (c.get("linked_sdr_ids") or [])),
                    }
                    for c in candidates_result
                ]
                df = pd.DataFrame(table_rows)
                st.dataframe(
                    df,
                    hide_index=True,
                    width="stretch",
                    column_config={
                        "WebVoc property": st.column_config.TextColumn(
                            "WebVoc property", pinned=True
                        ),
                        "Score": st.column_config.NumberColumn(
                            "Score", format="%.3f"
                        ),
                        "Eligible for promotion": st.column_config.CheckboxColumn(
                            "Eligible for promotion"
                        ),
                    },
                )

                if candidates_result:
                    selected_idx = st.selectbox(
                        "Select candidate for detail",
                        range(len(candidates_result)),
                        format_func=lambda i: (
                            f"{candidates_result[i].get('webvoc_property_id', '')} / "
                            f"{candidates_result[i].get('gdsn_attribute_name', '')} "
                            f"(score={candidates_result[i].get('score', 0):.3f})"
                        ),
                    )
                    with st.expander("Candidate detail", expanded=False):
                        selected_cand = candidates_result[selected_idx]
                        status = selected_cand.get("status", "")
                        st.markdown("**Status / Review lane / Promotion eligibility**")
                        badge_col1, badge_col2, badge_col3 = st.columns(3)
                        with badge_col1:
                            render_status_badge(
                                status or "unknown",
                                _STATUS_BADGE_TONES.get(status, "archived"),
                            )
                        with badge_col2:
                            lane = selected_cand.get("review_lane", "standard")
                            render_status_badge(
                                "Hard-mapping lane" if lane == "hard_mapping"
                                else "Standard lane",
                                "review" if lane == "hard_mapping" else "current",
                            )
                        with badge_col3:
                            eligible = selected_cand.get("promotion_eligible", False)
                            render_status_badge(
                                "Eligible for promotion" if eligible
                                else "Not yet eligible",
                                "accepted" if eligible else "blocked",
                            )
                        st.caption(selected_cand.get("review_notes", ""))
                        if selected_cand.get("hard_mapping"):
                            st.markdown("**Hard-mapping reasons**")
                            for reason in selected_cand.get("hard_mapping_reasons") or []:
                                st.write(f"- {reason}")

                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.markdown("**WebVoc property**")
                            st.code(selected_cand.get("webvoc_property_id", ""))
                            webvoc_property_id = selected_cand.get(
                                "webvoc_property_id", ""
                            )
                            if webvoc_property_id:
                                st.button(
                                    "View in Explorer",
                                    key=f"deep_link_explorer_{selected_idx}",
                                    on_click=navigate_to_webvoc_property,
                                    args=(webvoc_property_id,),
                                )
                            st.markdown("**Label**")
                            st.write(selected_cand.get("webvoc_label") or "—")
                            st.markdown("**Comment**")
                            st.write(selected_cand.get("webvoc_comment") or "—")
                            st.markdown("**Domain / Range**")
                            st.write(
                                f"{selected_cand.get('webvoc_domain') or '—'} / "
                                f"{selected_cand.get('webvoc_range') or '—'}"
                            )
                        with col_b:
                            st.markdown("**GDSN attribute name**")
                            st.code(selected_cand.get("gdsn_attribute_name", ""))
                            st.markdown("**BMS ID / Module**")
                            st.write(
                                f"{selected_cand.get('gdsn_bms_id') or '—'} / "
                                f"{selected_cand.get('gdsn_module') or '—'}"
                            )
                            st.markdown("**DataType / Multiplicity**")
                            st.write(
                                f"{selected_cand.get('gdsn_data_type') or '—'} / "
                                f"{selected_cand.get('gdsn_multiplicity') or '—'}"
                            )
                            st.markdown("**Definition**")
                            st.write(selected_cand.get("gdsn_definition") or "—")
                        st.markdown("**Score / Confidence / Review status**")
                        st.write(
                            f"{selected_cand.get('score', 0):.4f} / "
                            f"{selected_cand.get('confidence_level', '—')} / "
                            f"{selected_cand.get('review_status', '—')}"
                        )
                        st.markdown("**Reasons**")
                        st.write("; ".join(selected_cand.get("reasons") or []) or "—")
                        st.markdown("**Warnings**")
                        st.write("; ".join(selected_cand.get("warnings") or []) or "None")
                        st.markdown("**Blocking notes**")
                        st.write(
                            "; ".join(selected_cand.get("blocking_notes") or []) or "None"
                        )
                        st.markdown("**Linked SDRs**")
                        st.write(
                            "; ".join(
                                str(s) for s in (selected_cand.get("linked_sdr_ids") or [])
                            ) or "None"
                        )
            else:
                st.info("No candidates match the selected filters.")

        _render_hard_mapping_signoff_authoring(
            [c for c in candidates_result if c.get("review_lane") == "hard_mapping"]
        )

        with st.container(border=True):
            render_section_header(
                6,
                "Download Reports",
                "Download the candidate report for offline review. "
                "These reports do not modify any mapping file.",
            )
            dl_col1, dl_col2, dl_col3 = st.columns(3)
            with dl_col1:
                with st.container(border=True):
                    render_download_intro(
                        "Candidate report JSON",
                        "Full candidate list with scores, reasons, and field metadata.",
                        "JSON",
                    )
                    json_bytes_data = st.session_state.get("candidate_json_bytes", b"")
                    st.download_button(
                        "Download mapping candidate report JSON",
                        data=json_bytes_data,
                        file_name="mapping_candidates.json",
                        mime="application/json",
                        width="stretch",
                    )
            with dl_col2:
                with st.container(border=True):
                    render_download_intro(
                        "Candidate report CSV",
                        "Flat CSV for spreadsheet review and sorting.",
                        "CSV",
                    )
                    csv_bytes_data = st.session_state.get("candidate_csv_bytes", b"")
                    st.download_button(
                        "Download mapping candidate report CSV",
                        data=csv_bytes_data,
                        file_name="mapping_candidates.csv",
                        mime="text/csv",
                        width="stretch",
                    )
            with dl_col3:
                with st.container(border=True):
                    render_download_intro(
                        "Candidate report XLSX",
                        "Excel workbook for review and annotation.",
                        "XLSX",
                    )
                    xlsx_bytes_data = st.session_state.get("candidate_xlsx_bytes", b"")
                    if xlsx_bytes_data:
                        st.download_button(
                            "Download mapping candidate report XLSX",
                            data=xlsx_bytes_data,
                            file_name="mapping_candidates.xlsx",
                            mime=(
                                "application/vnd.openxmlformats-officedocument"
                                ".spreadsheetml.sheet"
                            ),
                            width="stretch",
                        )
                    else:
                        st.info("XLSX generation requires openpyxl.")
