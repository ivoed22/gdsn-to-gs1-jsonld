"""Generate Mapping Candidates workflow."""

from __future__ import annotations

import streamlit as st

from app.ui import render_download_intro, render_section_header
from app.workflow_shared import REPOSITORY_ROOT
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
            REPOSITORY_ROOT / "mapping" / "mapping_v0_3.yaml"
        ),
        backlog_path=str(
            REPOSITORY_ROOT
            / "docs"
            / "standards-decisions"
            / "standards_review_backlog.json"
        ),
    )


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
            use_container_width=True,
        )

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

            st.session_state["candidate_results"] = candidates
            st.session_state["candidate_json_bytes"] = candidate_report_bytes_json(candidates)
            st.session_state["candidate_csv_bytes"] = candidate_report_bytes_csv(candidates)
            xlsx_b = candidate_report_bytes_xlsx(candidates)
            if xlsx_b:
                st.session_state["candidate_xlsx_bytes"] = xlsx_b

    candidates_result = st.session_state.get("candidate_results")
    if candidates_result is not None:
        summary = generate_candidate_summary(candidates_result)
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
                        "Top reason": (c.get("reasons") or [""])[0],
                        "SDR linked": "; ".join(str(s) for s in (c.get("linked_sdr_ids") or [])),
                    }
                    for c in candidates_result
                ]
                df = pd.DataFrame(table_rows)
                st.dataframe(df, hide_index=True, use_container_width=True)

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
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.markdown("**WebVoc property**")
                            st.code(selected_cand.get("webvoc_property_id", ""))
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

        with st.container(border=True):
            render_section_header(
                5,
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
                        use_container_width=True,
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
                        use_container_width=True,
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
                            use_container_width=True,
                        )
                    else:
                        st.info("XLSX generation requires openpyxl.")
