"""Build Product Passport Prototype workflow."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.ui import render_download_intro, render_section_header
from app.workflow_shared import REPOSITORY_ROOT
from gdsn_to_gs1_jsonld.product_passport_builder import (
    DEFAULT_SCHEMA_PATH as PP_BUILDER_DEFAULT_SCHEMA,
    build_minimal_product_passport,
    build_product_passport_summary,
    extract_brand,
    extract_gtin,
    extract_product_identifier,
    extract_product_name,
    normalize_gs1_jsonld_input,
    product_passport_report_bytes_json,
    product_passport_to_json_bytes,
    validate_built_product_passport,
)


def render_build_product_passport_workflow() -> None:
    """Render the Build Product Passport Prototype workflow page."""
    st.markdown(
        """
        <div class="pp-prototype-warning">
          <strong>Prototype / Reference only — minimal-schema mode</strong>
          This builder wraps GS1 Web Vocabulary JSON-LD into a prototype Product
          Passport envelope and runs structural validation against a local
          schema (the built-in minimal schema by default). It is not official
          GS1 validation, not EU DPP regulatory compliance, and not
          production-ready.
        </div>
        """,
        unsafe_allow_html=True,
    )

    minimal_schema_path = str(REPOSITORY_ROOT / PP_BUILDER_DEFAULT_SCHEMA)
    example_path = (
        REPOSITORY_ROOT
        / "product_passport"
        / "examples"
        / "gs1_product_for_passport_builder.jsonld"
    )

    tab_input, tab_settings, tab_output, tab_report = st.tabs([
        "Input GS1 JSON-LD",
        "Builder Settings",
        "Product Passport Output",
        "Validation Report",
    ])

    with tab_input:
        with st.container(border=True):
            render_section_header(
                1,
                "Input GS1 JSON-LD",
                "Provide GS1 Web Vocabulary JSON-LD from the converter, the "
                "Manual JSON-LD Prototype Builder, or paste/upload your own.",
            )
            st.info(
                "Prototype/reference only. Minimal-schema mode. Structural "
                "validation only."
            )

        input_mode = st.radio(
            "Input mode",
            ["Upload file", "Paste JSON", "Use example"],
            horizontal=True,
        )
        gs1_data: dict | None = None
        if input_mode == "Upload file":
            uploaded = st.file_uploader(
                "GS1 JSON-LD file",
                type=["json", "jsonld"],
                help="Upload GS1 Web Vocabulary JSON-LD for wrapping.",
            )
            if uploaded is not None:
                try:
                    gs1_data = normalize_gs1_jsonld_input(
                        uploaded.getvalue().decode("utf-8")
                    )
                    st.success(f"Loaded: {uploaded.name}")
                except (ValueError, UnicodeDecodeError) as exc:
                    st.error(f"Could not parse JSON-LD: {exc}")
        elif input_mode == "Paste JSON":
            pasted = st.text_area(
                "Paste GS1 JSON-LD",
                height=200,
                placeholder='{\n  "@context": "https://ref.gs1.org/voc/data/gs1Voc.jsonld",\n  "@type": "gs1:Product",\n  "gtin": "09521234543213"\n}',
            )
            if pasted.strip():
                try:
                    gs1_data = normalize_gs1_jsonld_input(pasted)
                    st.success("JSON-LD parsed successfully.")
                except ValueError as exc:
                    st.error(f"Could not parse JSON-LD: {exc}")
        else:
            if example_path.is_file():
                try:
                    gs1_data = normalize_gs1_jsonld_input(
                        example_path.read_text(encoding="utf-8")
                    )
                    st.success(
                        "Loaded built-in example GS1 JSON-LD "
                        "(prototype/example only, not production data)."
                    )
                except (ValueError, OSError) as exc:
                    st.error(f"Could not load example: {exc}")
            else:
                st.info("Example GS1 JSON-LD not available.")

        if gs1_data is not None:
            st.session_state["pb_gs1_input"] = gs1_data

        current_gs1 = st.session_state.get("pb_gs1_input")
        if current_gs1 is not None:
            with st.container(border=True):
                render_section_header(
                    2,
                    "Parsed Summary",
                    "Fields detected in the GS1 JSON-LD input.",
                )
                summary_rows = [
                    {"field": "@type", "value": str(current_gs1.get("@type", ""))},
                    {"field": "@id", "value": extract_product_identifier(current_gs1) or ""},
                    {"field": "gtin", "value": extract_gtin(current_gs1) or ""},
                    {"field": "productName", "value": extract_product_name(current_gs1) or ""},
                    {"field": "brand", "value": extract_brand(current_gs1) or ""},
                ]
                st.dataframe(
                    pd.DataFrame(summary_rows),
                    hide_index=True,
                    use_container_width=True,
                )

    with tab_settings:
        with st.container(border=True):
            render_section_header(
                1,
                "Builder Settings",
                "Configure the prototype passport envelope. Minimal-schema mode.",
            )
            st.warning(
                "Minimal-schema mode. Structural validation only. Not official "
                "GS1 validation, not EU DPP regulatory compliance, and not "
                "production-ready."
            )
        setting_passport_id = st.text_input(
            "Passport id (optional)",
            help="Leave blank to derive a prototype id from the GTIN.",
        )
        setting_language = st.selectbox(
            "Default language",
            ["en", "nl", "de", "fr", "es"],
            index=0,
        )
        setting_include_source = st.checkbox(
            "Include source GS1 JSON-LD inside the passport envelope",
            value=True,
        )
        st.selectbox(
            "Validation schema",
            ["dpp_minimal — Minimal DPP Structural Schema (built-in)"],
            help="The built-in minimal schema is the only active validation "
            "target in v0.13.0.",
        )
        st.caption(
            "External DPP schemas listed in the source manifest are placeholders "
            "(not downloaded) and are unavailable for building until downloaded."
        )
        st.session_state["pb_settings"] = {
            "passport_id": setting_passport_id or None,
            "default_language": setting_language,
            "include_source_gs1_jsonld": setting_include_source,
        }

    with tab_output:
        with st.container(border=True):
            render_section_header(
                1,
                "Product Passport Output",
                "Build the prototype passport and preview it. Prototype/reference "
                "only.",
            )
        current_gs1 = st.session_state.get("pb_gs1_input")
        build_clicked = st.button(
            "Build Product Passport Prototype",
            type="primary",
            use_container_width=True,
            disabled=(current_gs1 is None),
        )
        if current_gs1 is None:
            st.markdown(
                """
                <div class="empty-state">
                  <span class="empty-state-mark" aria-hidden="true">PB</span>
                  <div>
                    <strong>Provide GS1 JSON-LD first</strong>
                    <span>Add input in the "Input GS1 JSON-LD" tab, then build the prototype passport here.</span>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if build_clicked and current_gs1 is not None:
            settings = dict(st.session_state.get("pb_settings", {}))
            settings["validation_schema"] = minimal_schema_path
            passport = build_minimal_product_passport(current_gs1, settings)
            report = validate_built_product_passport(passport, minimal_schema_path)
            st.session_state["pb_passport"] = passport
            st.session_state["pb_report"] = report

        built_passport = st.session_state.get("pb_passport")
        built_report = st.session_state.get("pb_report")
        if built_passport is not None:
            summary = build_product_passport_summary(built_passport, built_report or {})
            with st.container(border=True):
                render_section_header(2, "Summary", "Prototype passport metrics.")
                m1, m2, m3 = st.columns(3)
                m1.metric("Source GTIN", summary.get("sourceGtin") or "—")
                m2.metric(
                    "Structural schema check",
                    {
                        "valid": "Passed",
                        "invalid": "Failed",
                        "schema_error": "Could not be evaluated",
                    }.get(
                        summary.get("structuralValidationStatus"),
                        summary.get("structuralValidationStatus") or "—",
                    ),
                )
                m3.metric("Validator", summary.get("validatorMode") or "—")

            with st.container(border=True):
                render_section_header(
                    3,
                    "Prototype Product Passport JSON-LD",
                    "Prototype/reference only — not official GS1 validation.",
                )
                st.json(built_passport)
                render_download_intro(
                    "Product Passport JSON-LD",
                    "Prototype Product Passport envelope for offline review.",
                    "JSON-LD",
                )
                st.download_button(
                    "Download Product Passport JSON-LD",
                    data=product_passport_to_json_bytes(built_passport),
                    file_name="product_passport.jsonld",
                    mime="application/ld+json",
                    use_container_width=True,
                )

    with tab_report:
        with st.container(border=True):
            render_section_header(
                1,
                "Validation Report",
                "Structural schema validation of the built passport.",
            )
        report = st.session_state.get("pb_report")
        if report is None:
            st.info(
                "Build a Product Passport in the Product Passport Output tab to "
                "see the validation report."
            )
        else:
            status = report.get("validation_status", "unknown")
            status_label = {
                "valid": "Structural schema check: Passed",
                "invalid": "Structural schema check: Failed — review errors",
                "schema_error": "Schema could not be evaluated",
            }.get(status, status)
            col_status, col_errors = st.columns(2)
            col_status.metric("Structural schema check", status_label)
            col_errors.metric("Schema errors", len(report.get("errors", [])))

            if report.get("validator_mode") == "minimal_fallback":
                st.warning(
                    "Fallback validator in use (jsonschema not available): only "
                    "required-field presence was checked. A 'Passed' result here "
                    "is weaker than full structural schema validation."
                )

            if report.get("errors"):
                error_rows = [
                    {"#": idx + 1, "error": err}
                    for idx, err in enumerate(report["errors"])
                ]
                st.dataframe(
                    pd.DataFrame(error_rows),
                    hide_index=True,
                    use_container_width=True,
                )

            for warn in report.get("warnings", []):
                st.info(warn)

            st.caption(f"Validator: {report.get('validator_version', 'unknown')}")
            st.info(
                "Passing this check means only that the JSON matches the "
                "selected local structural schema. It is not an official GS1 "
                "validation or EU DPP compliance result."
            )
            render_download_intro(
                "Validation report JSON",
                "Structural validation report for offline review.",
                "JSON",
            )
            st.download_button(
                "Download validation report JSON",
                data=product_passport_report_bytes_json(report),
                file_name="product_passport_validation_report.json",
                mime="application/json",
                use_container_width=True,
            )
