from __future__ import annotations

import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_DIRECTORY = REPOSITORY_ROOT / "src"

for directory in (REPOSITORY_ROOT, SRC_DIRECTORY):
    directory_path = str(directory)
    if directory_path not in sys.path:
        sys.path.insert(0, directory_path)

import streamlit as st

from app.ui import (
    APP_VERSION,
    apply_page_styles,
    render_page_header,
    render_standards_backlog_status,
    render_vocabulary_status,
    render_workflow_mode_card,
)
from app.workflow_shared import (
    DEFAULT_WORKFLOW_MODE,
    REPOSITORY_ROOT,
    SRC_DIRECTORY,
    WORKFLOW_MODES,
    _backlog_categories,
    _load_open_standards_backlog,
    _load_webvoc_metadata,
    set_workflow_mode,
)
from app.workflows.builder_expansion import render_builder_expansion_analysis
from app.workflows.candidates import render_mapping_candidates_workflow
from app.workflows.convert import (
    render_bulk_zip_workflow,
    render_mapping_profile_selector,
    render_single_xml_workflow,
)
from app.workflows.dashboard import render_workbench_status_dashboard
from app.workflows.explore import render_webvoc_explorer
from app.workflows.product_passport import render_validate_product_passport_workflow
from app.workflows.product_passport_builder import render_build_product_passport_workflow
from app.workflows.prototype import render_manual_jsonld_builder
from app.workflows.standards import render_standards_review_mode


def main() -> None:
    st.set_page_config(
        page_title="GDSN to GS1 JSON-LD Converter",
        page_icon="G",
        layout="wide",
    )
    apply_page_styles()
    render_page_header()
    backlog = _load_open_standards_backlog()
    render_workbench_status_dashboard(len(backlog))
    if st.session_state.get("workflow_mode") not in {
        mode["title"] for mode in WORKFLOW_MODES
    }:
        st.session_state["workflow_mode"] = DEFAULT_WORKFLOW_MODE

    with st.sidebar:
        st.markdown(
            f"""
            <div class="sidebar-brand">
              <strong>Standards workbench</strong>
              <span>App version: {APP_VERSION}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        # Compact workspace status/context — not the primary work area.
        st.markdown(
            """
            <div class="vocabulary-status">
              <strong>Workspace status</strong>
              Mode: Prototype / review<br>
              Storage: In-memory<br>
              Warnings: visible (not suppressed)
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<p class="sidebar-label">Sources</p>', unsafe_allow_html=True)
        webvoc_metadata = _load_webvoc_metadata()
        render_vocabulary_status(
            webvoc_metadata.get("detected_version"),
            webvoc_metadata.get("detected_last_modified"),
        )
        st.markdown(
            """
            <div class="vocabulary-status">
              <strong>Product Passport schemas</strong>
              Built-in minimal schema (offline).<br>
              External DPP schemas: placeholders, not downloaded.<br>
              Prototype/reference only.
            </div>
            """,
            unsafe_allow_html=True,
        )

        # One governance block (v0.30.0: previously two near-duplicate
        # boxes — the backlog status and a separate governance note).
        render_standards_backlog_status(
            len(backlog),
            _backlog_categories(backlog),
        )
        st.markdown(
            """
            <div class="standards-backlog-status">
              <strong>Governance</strong>
              No official GS1 validation.<br>
              No production compliance claim.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Direct navigation (v0.30.0): five workflow cards, one stage. The
    # two-stage route->child card navigation existed to manage nine
    # workflows; with five it only cost clicks and screen height.
    with st.container(border=True):
        st.markdown(
            '<p class="workflow-group-label">Choose a workflow</p>',
            unsafe_allow_html=True,
        )
        workflow_columns = st.columns(len(WORKFLOW_MODES))
        for column, mode in zip(workflow_columns, WORKFLOW_MODES, strict=True):
            with column:
                selected = st.session_state["workflow_mode"] == mode["title"]
                render_workflow_mode_card(
                    mode["title"],
                    mode["description"],
                    mode["outcome"],
                    mode["marker"],
                    selected,
                )
                st.button(
                    "Active" if selected else "Open",
                    key=f"workflow_mode_{mode['key']}",
                    type="primary" if selected else "secondary",
                    disabled=selected,
                    on_click=set_workflow_mode,
                    args=(mode["title"],),
                    use_container_width=True,
                )

    workflow_mode = st.session_state["workflow_mode"]
    if workflow_mode == "Convert GDSN XML":
        mapping_path = render_mapping_profile_selector()
        single_tab, bulk_tab = st.tabs(["Single XML", "Bulk ZIP"])
        with single_tab:
            render_single_xml_workflow(mapping_path)
        with bulk_tab:
            render_bulk_zip_workflow(mapping_path)
    elif workflow_mode == "Explore GS1 Web Vocabulary":
        render_webvoc_explorer()
    elif workflow_mode == "Create JSON-LD Prototype":
        builder_tab, expansion_tab = st.tabs(["Builder", "Expansion analysis"])
        with builder_tab:
            render_manual_jsonld_builder()
        with expansion_tab:
            render_builder_expansion_analysis()
    elif workflow_mode == "Mapping Governance":
        candidates_tab, standards_tab = st.tabs(
            ["Mapping candidates", "Standards review"]
        )
        with candidates_tab:
            render_mapping_candidates_workflow()
        with standards_tab:
            render_standards_review_mode(backlog)
    else:
        sources_tab, build_tab = st.tabs(
            ["Sources & validation", "Build prototype passport"]
        )
        with sources_tab:
            render_validate_product_passport_workflow()
        with build_tab:
            render_build_product_passport_workflow()


if __name__ == "__main__":
    main()
