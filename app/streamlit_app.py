from __future__ import annotations

import streamlit as st

from app.ui import (
    APP_VERSION,
    apply_page_styles,
    render_page_header,
    render_route_card,
    render_standards_backlog_status,
    render_vocabulary_status,
    render_workflow_entry_intro,
    render_workflow_mode_card,
    render_workflow_overview,
)
from app.workflow_shared import (
    DEFAULT_ROUTE,
    DEFAULT_WORKFLOW_MODE,
    REPOSITORY_ROOT,
    ROUTES,
    SRC_DIRECTORY,
    WORKFLOW_MODES,
    _backlog_categories,
    _load_open_standards_backlog,
    _load_webvoc_metadata,
    clear_all_results,
    set_route,
    set_workflow_mode,
)
from app.workflows.candidates import render_mapping_candidates_workflow
from app.workflows.convert import render_bulk_zip_workflow, render_single_xml_workflow
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
    render_workflow_overview()
    if st.session_state.get("workflow_mode") not in {
        mode["title"] for mode in WORKFLOW_MODES
    }:
        st.session_state["workflow_mode"] = DEFAULT_WORKFLOW_MODE
    if st.session_state.get("selected_route") not in {
        route["key"] for route in ROUTES
    }:
        st.session_state["selected_route"] = DEFAULT_ROUTE

    mapping_profiles = {
        "Certifications & Documents v0.3.0": (
            REPOSITORY_ROOT / "mapping" / "mapping_v0_3.yaml"
        ),
        "Food v0.2.0 mapping": REPOSITORY_ROOT / "mapping" / "mapping_v0_2.yaml",
        "MVP v0.1.0 mapping": REPOSITORY_ROOT / "mapping" / "mapping_mvp.yaml",
    }

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

        with st.container(border=True):
            st.markdown(
                '<p class="sidebar-label">Current context</p>',
                unsafe_allow_html=True,
            )
            selected_profile = st.selectbox(
                "Mapping profile",
                list(mapping_profiles),
                on_change=clear_all_results,
                help=(
                    "Active mapping profile. It also applies inside Convert "
                    "GDSN XML. Changing it clears current conversion results."
                ),
            )
            mapping_path = mapping_profiles[selected_profile]
            st.markdown("**Active mapping file**")
            st.code(mapping_path.relative_to(REPOSITORY_ROOT).as_posix())

        with st.expander("Profile coverage & supported groups", expanded=False):
            st.markdown(
                """
                <p class="sidebar-label">Supported groups</p>
                <div class="coverage-badges">
                  <span class="coverage-badge">Identity</span>
                  <span class="coverage-badge">Descriptions</span>
                  <span class="coverage-badge">Brand &amp; GPC</span>
                  <span class="coverage-badge">Net content</span>
                  <span class="coverage-badge">Images &amp; links</span>
                  <span class="coverage-badge">Ingredients</span>
                  <span class="coverage-badge">Allergens</span>
                  <span class="coverage-badge">Nutrients</span>
                  <span class="coverage-badge">Certifications</span>
                  <span class="coverage-badge">Documents</span>
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

        backlog = _load_open_standards_backlog()
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

    modes_by_key = {mode["key"]: mode for mode in WORKFLOW_MODES}
    routes_by_key = {route["key"]: route for route in ROUTES}

    with st.container(border=True):
        render_workflow_entry_intro()

        # Stage 1 — three primary route cards (progressive disclosure).
        st.markdown(
            '<p class="workflow-group-label">Choose a route</p>',
            unsafe_allow_html=True,
        )
        route_columns = st.columns(len(ROUTES))
        for column, route in zip(route_columns, ROUTES, strict=True):
            with column:
                route_selected = st.session_state["selected_route"] == route["key"]
                render_route_card(
                    route["title"],
                    route["description"],
                    route["outcome"],
                    route["marker"],
                    route_selected,
                )
                st.button(
                    "Active" if route_selected else "Open",
                    key=f"route_{route['key']}",
                    type="primary" if route_selected else "secondary",
                    disabled=route_selected,
                    on_click=set_route,
                    args=(route["key"],),
                    use_container_width=True,
                )

        # Stage 2 — only the child workflow cards for the selected route.
        active_route = routes_by_key[st.session_state["selected_route"]]
        st.markdown(
            f'<p class="route-child-heading">{active_route["child_heading"]}</p>',
            unsafe_allow_html=True,
        )
        child_keys = active_route["children"]
        child_columns = st.columns(len(child_keys))
        for column, key in zip(child_columns, child_keys, strict=True):
            mode = modes_by_key[key]
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
        single_tab, bulk_tab = st.tabs(["Single XML", "Bulk ZIP"])
        with single_tab:
            render_single_xml_workflow(mapping_path)
        with bulk_tab:
            render_bulk_zip_workflow(mapping_path)
    elif workflow_mode == "Explore GS1 Web Vocabulary":
        render_webvoc_explorer()
    elif workflow_mode == "Create JSON-LD Prototype":
        render_manual_jsonld_builder()
    elif workflow_mode == "Generate Mapping Candidates":
        render_mapping_candidates_workflow()
    elif workflow_mode == "Validate Product Passport Sources":
        render_validate_product_passport_workflow()
    elif workflow_mode == "Build Product Passport Prototype":
        render_build_product_passport_workflow()
    else:
        render_standards_review_mode(backlog)


if __name__ == "__main__":
    main()
