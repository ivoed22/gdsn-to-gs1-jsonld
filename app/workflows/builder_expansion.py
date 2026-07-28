"""Builder Manifest Expansion Analysis workflow (Track C, v0.19.0).

Read-only. Shows which not-yet-authorable WebVoc properties are mature
enough to add to the Manual JSON-LD Builder manifest next, based on the
mapping registry's governance catalog and Track B's hard-mapping detection.
Never writes to the builder manifest.
"""

from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from app.ui import render_download_intro, render_section_header, render_status_badge
from app.workflow_shared import REPOSITORY_ROOT
from gdsn_to_gs1_jsonld.builder_expansion_analysis import (
    READINESS_PHASES,
    build_expansion_analysis,
    load_catalog_rows_from_registry,
)
from gdsn_to_gs1_jsonld.jsonld_builder import load_builder_manifest
from gdsn_to_gs1_jsonld.mapping_candidate_generator import load_webvoc_properties

_PHASE_LABELS = {
    "ready_now": "Ready now",
    "needs_codelist_curation": "Needs codelist curation",
    "needs_hard_mapping_review": "Needs hard-mapping review",
    "not_ready_no_evidence": "Not ready (no evidence)",
}
_PHASE_TONES = {
    "ready_now": "accepted",
    "needs_codelist_curation": "review",
    "needs_hard_mapping_review": "review",
    "not_ready_no_evidence": "archived",
}


@st.cache_data(show_spinner=False)
def _load_expansion_analysis() -> dict:
    webvoc_rows = load_webvoc_properties(
        str(
            REPOSITORY_ROOT
            / "reference_data"
            / "normalized"
            / "webvoc_properties_1_18.csv"
        )
    )
    manifest = load_builder_manifest(
        REPOSITORY_ROOT / "builder_manifest" / "product_builder_v0_10.yaml"
    )
    catalog_rows = load_catalog_rows_from_registry(
        REPOSITORY_ROOT / "mapping" / "mapping_registry.yaml"
    )
    return build_expansion_analysis(
        webvoc_rows,
        manifest,
        catalog_rows,
        REPOSITORY_ROOT
        / "reference_data"
        / "normalized"
        / "gdsn_attributes_bms_xpath_3_1_36.csv",
    )


def render_builder_expansion_analysis() -> None:
    """Render the read-only Builder Manifest Expansion Analysis workflow."""
    with st.container(border=True):
        render_section_header(
            1,
            "Builder Manifest Expansion Analysis",
            "Which not-yet-authorable WebVoc properties are mature enough to "
            "add to the Manual Builder manifest next.",
        )
        st.warning(
            "Read-only analysis. It never modifies the builder manifest — "
            "adding a field is a separate, deliberate decision. DPP "
            "relevance is not yet assessed for any candidate: that judgment "
            "belongs to the GS1-first DPP Crosswalk (not built). No "
            "codelist enforcement is claimed."
        )

    try:
        analysis = _load_expansion_analysis()
    except (FileNotFoundError, OSError, ValueError) as exc:
        st.error(f"Builder manifest expansion analysis could not load local sources: {exc}")
        return

    with st.container(border=True):
        render_section_header(
            2,
            "Coverage summary",
            "How much of the GS1 Web Vocabulary is authorable today.",
        )
        m1, m2, m3 = st.columns(3)
        m1.metric("Authored in manifest", analysis["authored_property_count"])
        m2.metric("Total WebVoc properties", analysis["total_webvoc_property_count"])
        m3.metric("Not yet authorable", analysis["not_yet_authorable_count"])

        by_phase = analysis["by_readiness_phase"]
        phase_cols = st.columns(len(READINESS_PHASES))
        for column, phase in zip(phase_cols, READINESS_PHASES, strict=True):
            column.metric(_PHASE_LABELS[phase], by_phase.get(phase, 0))

    with st.container(border=True):
        render_section_header(
            3,
            "Filter candidates",
            "Narrow the candidate list by readiness phase.",
        )
        selected_phases = st.multiselect(
            "Readiness phase",
            options=list(READINESS_PHASES),
            format_func=lambda phase: _PHASE_LABELS[phase],
            default=["ready_now"],
            help="Leave empty to show every not-yet-authorable property.",
        )

    candidates = analysis["candidates"]
    if selected_phases:
        candidates = [c for c in candidates if c["readiness_phase"] in selected_phases]

    with st.container(border=True):
        render_section_header(
            4,
            "Candidate properties",
            f"{len(candidates)} of {analysis['not_yet_authorable_count']} "
            "not-yet-authorable properties shown.",
        )
        if candidates:
            table_rows = [
                {
                    "WebVoc property": c["term_id"],
                    "Label": c["label"],
                    "Range": c["range"],
                    "Source mapping status": ", ".join(c["source_mapping_status"]) or "—",
                    "Codelist dependency": c["codelist_dependency"],
                    "Hard-mapping dependency": c["hard_mapping_dependency"],
                    "DPP relevance": "Not yet assessed",
                    "Readiness phase": _PHASE_LABELS[c["readiness_phase"]],
                }
                for c in candidates
            ]
            st.dataframe(
                pd.DataFrame(table_rows),
                hide_index=True,
                width="stretch",
            )

            selected_idx = st.selectbox(
                "Select candidate for detail",
                range(len(candidates)),
                format_func=lambda i: (
                    f"{candidates[i]['term_id']} — {_PHASE_LABELS[candidates[i]['readiness_phase']]}"
                ),
            )
            with st.expander("Candidate detail", expanded=False):
                selected = candidates[selected_idx]
                render_status_badge(
                    _PHASE_LABELS[selected["readiness_phase"]],
                    _PHASE_TONES[selected["readiness_phase"]],
                )
                st.markdown("**Reason**")
                st.write(selected["reason"])
                if selected["hard_mapping_reasons"]:
                    st.markdown("**Hard-mapping reasons**")
                    for reason in selected["hard_mapping_reasons"]:
                        st.write(f"- {reason}")
                st.markdown("**Source mapping status**")
                st.write(", ".join(selected["source_mapping_status"]) or "No governed mapping evidence.")
        else:
            st.info("No candidates match the selected readiness phases.")

    with st.container(border=True):
        render_section_header(
            5,
            "Download analysis",
            "Full analysis for offline review. Proposal only — approving an "
            "addition to the manifest is a separate step.",
        )
        render_download_intro(
            "Expansion analysis JSON",
            "Full candidate list with readiness phases and reasons.",
            "JSON",
        )
        st.download_button(
            "Download builder manifest expansion analysis JSON",
            data=json.dumps(analysis, indent=2, ensure_ascii=False).encode("utf-8"),
            file_name="builder_manifest_expansion_analysis.json",
            mime="application/json",
            width="stretch",
        )
