"""Validate Product Passport Sources workflow."""

from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from app.ui import render_download_intro, render_section_header
from app.workflow_shared import REPOSITORY_ROOT
from gdsn_to_gs1_jsonld.product_passport_sources import (
    build_product_passport_source_inventory,
    inventory_report_bytes_csv,
    inventory_report_bytes_json,
    load_json_schema,
    load_product_passport_source_manifest,
    validate_product_passport_json,
    validate_product_passport_source_manifest,
)


def render_validate_product_passport_workflow() -> None:
    """Render the Validate Product Passport Sources workflow page."""
    st.markdown(
        """
        <div class="pp-prototype-warning">
          <strong>Prototype / Reference only — not official GS1 validation</strong>
          v0.12.0 performs source inventory and structural JSON Schema validation only.
          It does not claim official GS1 validation, EU DPP regulatory compliance,
          or production readiness.
        </div>
        """,
        unsafe_allow_html=True,
    )

    manifest_path = REPOSITORY_ROOT / "product_passport" / "reference_sources" / "source_manifest.json"

    tab_inventory, tab_validator, tab_examples = st.tabs([
        "Source Inventory",
        "Schema Validator",
        "Examples",
    ])

    with tab_inventory:
        with st.container(border=True):
            render_section_header(
                1,
                "Product Passport Reference Source Inventory",
                "Load the source manifest and inspect all reference sources by type "
                "and sector. No files are fetched from the internet.",
            )
            st.info(
                "Prototype/reference only. Source inventory is structural metadata "
                "tracking only. No official GS1 validation or production compliance claimed."
            )

        if st.button("Load Source Manifest", type="primary", use_container_width=True):
            try:
                pp_manifest = load_product_passport_source_manifest(str(manifest_path))
                manifest_schema = None
                schema_sibling = manifest_path.parent / "source_manifest.schema.json"
                if schema_sibling.is_file():
                    try:
                        manifest_schema = load_json_schema(str(schema_sibling))
                    except (OSError, ValueError):
                        manifest_schema = None
                errors = validate_product_passport_source_manifest(
                    pp_manifest, schema=manifest_schema
                )
                base_dir = str(REPOSITORY_ROOT)
                inventory = build_product_passport_source_inventory(pp_manifest, base_dir=base_dir)
                st.session_state["pp_inventory"] = inventory
                st.session_state["pp_manifest_errors"] = errors
            except (FileNotFoundError, OSError, ValueError, Exception) as exc:
                st.error(f"Failed to load source manifest: {exc}")

        inventory = st.session_state.get("pp_inventory")
        manifest_errors = st.session_state.get("pp_manifest_errors", [])

        if manifest_errors:
            for err in manifest_errors:
                st.warning(f"Manifest issue: {err}")

        if inventory is None:
            st.markdown(
                """
                <div class="empty-state">
                  <span class="empty-state-mark" aria-hidden="true">PP</span>
                  <div>
                    <strong>Ready to load source manifest</strong>
                    <span>Click "Load Source Manifest" to inspect all reference sources by type and sector.</span>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if inventory is not None:
            with st.container(border=True):
                render_section_header(
                    2,
                    "Inventory Summary",
                    "Source counts by type and sector. Missing local files are placeholder entries that require a separate download.",
                )
                col_total, col_missing = st.columns(2)
                col_total.metric("Total sources", inventory.get("total_sources", 0))
                col_missing.metric(
                    "Missing local files",
                    len(inventory.get("missing_local_files", [])),
                )
                by_type = inventory.get("sources_by_type", {})
                by_sector = inventory.get("sources_by_sector", {})
                type_col, sector_col = st.columns(2)
                with type_col:
                    st.markdown("**By type**")
                    for k, v in sorted(by_type.items()):
                        st.write(f"{k}: {v}")
                with sector_col:
                    st.markdown("**By sector**")
                    for k, v in sorted(by_sector.items()):
                        st.write(f"{k}: {v}")

            with st.container(border=True):
                render_section_header(
                    3,
                    "Source Table",
                    "All source entries with file and checksum status.",
                )
                entries = inventory.get("entries", [])
                if entries:
                    table_rows = [
                        {
                            "source_id": e.get("source_id", ""),
                            "title": e.get("title", ""),
                            "source_type": e.get("source_type", ""),
                            "sector": e.get("sector", ""),
                            "version": e.get("version", ""),
                            "local_path": e.get("local_path", ""),
                            "file_exists": e.get("_file_exists", False),
                            "checksum_status": e.get("_checksum_status", ""),
                        }
                        for e in entries
                    ]
                    st.dataframe(
                        pd.DataFrame(table_rows),
                        hide_index=True,
                        use_container_width=True,
                    )

            with st.container(border=True):
                render_section_header(
                    4,
                    "Download Inventory",
                    "Download inventory reports for offline review.",
                )
                dl_inv_col, dl_csv_col = st.columns(2)
                with dl_inv_col:
                    render_download_intro(
                        "Inventory JSON",
                        "Full source inventory with checksum status.",
                        "JSON",
                    )
                    st.download_button(
                        "Download inventory JSON",
                        data=inventory_report_bytes_json(inventory),
                        file_name="product_passport_source_inventory.json",
                        mime="application/json",
                        use_container_width=True,
                    )
                with dl_csv_col:
                    render_download_intro(
                        "Inventory CSV",
                        "Source table for spreadsheet review.",
                        "CSV",
                    )
                    st.download_button(
                        "Download inventory CSV",
                        data=inventory_report_bytes_csv(inventory),
                        file_name="product_passport_source_inventory.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )

    with tab_validator:
        with st.container(border=True):
            render_section_header(
                1,
                "Schema Validator",
                "Validate a Product Passport JSON file against a local JSON Schema. "
                "Structural validation only.",
            )
            st.warning(
                "Structural validation only. Not official GS1 validation. "
                "Not production compliance."
            )

        # Load manifest to get schema list.
        pp_manifest_data: dict | None = None
        try:
            pp_manifest_data = load_product_passport_source_manifest(str(manifest_path))
        except (FileNotFoundError, OSError, Exception):
            pass

        schema_entries = []
        if pp_manifest_data:
            schema_entries = [
                s for s in pp_manifest_data.get("sources", [])
                if s.get("source_type") == "json_schema"
            ]

        # Only schemas whose local file exists are offered as active choices.
        # Placeholder schemas (file not yet downloaded) are listed as
        # unavailable rather than presented as selectable validation targets.
        local_schema_options: dict[str, str] = {}
        unavailable_schemas: list[str] = []
        for s in schema_entries:
            local_path = s.get("local_path", "")
            schema_file_candidate = REPOSITORY_ROOT / local_path if local_path else None
            label = f"{s.get('source_id')} — {s.get('title', '')}"
            if schema_file_candidate and schema_file_candidate.is_file():
                local_schema_options[label] = local_path
            else:
                unavailable_schemas.append(str(s.get("source_id", "")))

        # Always add the built-in minimal schema (committed, always available).
        minimal_schema_path = str(
            REPOSITORY_ROOT / "product_passport" / "reference_sources" / "raw_public" / "schemas" / "dpp_minimal.schema.json"
        )
        local_schema_options["dpp_minimal — Minimal DPP Structural Schema (built-in)"] = minimal_schema_path

        if unavailable_schemas:
            st.caption(
                "Unavailable — placeholder source file not downloaded yet: "
                + ", ".join(unavailable_schemas)
                + ". These remain listed in Source Inventory as provenance "
                "placeholders and cannot be used for validation until downloaded."
            )

        with st.container(border=True):
            render_section_header(
                2,
                "Input",
                "Upload a Product Passport JSON file or paste JSON text.",
            )
            input_mode = st.radio(
                "Input mode",
                ["Upload file", "Paste JSON"],
                horizontal=True,
            )

            instance_data: dict | None = None
            if input_mode == "Upload file":
                uploaded = st.file_uploader(
                    "Product Passport JSON file",
                    type=["json"],
                    help="Upload a JSON or JSON-LD file for structural validation.",
                )
                if uploaded is not None:
                    try:
                        instance_data = json.loads(uploaded.getvalue().decode("utf-8"))
                        st.success(f"Loaded: {uploaded.name}")
                    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                        st.error(f"Could not parse JSON: {exc}")
            else:
                pasted = st.text_area(
                    "Paste Product Passport JSON",
                    height=200,
                    placeholder='{\n  "@context": "https://gs1.org/voc/",\n  "@type": "gs1:Product"\n}',
                )
                if pasted.strip():
                    try:
                        instance_data = json.loads(pasted)
                        st.success("JSON parsed successfully.")
                    except json.JSONDecodeError as exc:
                        st.error(f"Could not parse JSON: {exc}")

            selected_schema_label = st.selectbox(
                "Local schema",
                list(local_schema_options.keys()),
                help="Select a local JSON Schema for structural validation.",
            )
            selected_schema_path = local_schema_options.get(selected_schema_label, "")

            validate_button = st.button(
                "Validate",
                type="primary",
                use_container_width=True,
                disabled=(instance_data is None),
            )

        if validate_button and instance_data is not None:
            schema_file_path = str(REPOSITORY_ROOT / selected_schema_path) if not selected_schema_path.startswith(str(REPOSITORY_ROOT)) else selected_schema_path
            try:
                schema = load_json_schema(schema_file_path)
                report = validate_product_passport_json(instance_data, schema)
                report["schema_file"] = selected_schema_path
                report["instance_file"] = "(uploaded/pasted)"
                st.session_state["pp_validation_report"] = report
            except (FileNotFoundError, Exception) as exc:
                st.error(f"Validation error: {exc}")

        val_report = st.session_state.get("pp_validation_report")
        if val_report is not None:
            with st.container(border=True):
                render_section_header(
                    3,
                    "Validation Result",
                    "Structural schema validation result.",
                )
                status = val_report.get("validation_status", "unknown")
                error_count = len(val_report.get("errors", []))
                warning_count = len(val_report.get("warnings", []))
                s_col, e_col, w_col = st.columns(3)
                status_label = {
                    "valid": "Structural schema check: Passed",
                    "invalid": "Structural schema check: Failed — review schema errors",
                    "schema_error": "Schema could not be evaluated",
                    "not_run": "Not run",
                }.get(status, status)
                s_col.metric("Structural schema check", status_label)
                e_col.metric("Schema errors", error_count)
                w_col.metric("Validator warnings", warning_count)

                if val_report.get("errors"):
                    st.markdown("**Schema validation errors**")
                    error_rows = [{"#": i + 1, "error": e} for i, e in enumerate(val_report["errors"])]
                    st.dataframe(pd.DataFrame(error_rows), hide_index=True, use_container_width=True)

                if val_report.get("validator_mode") == "minimal_fallback":
                    st.warning(
                        "Fallback validator in use (jsonschema not available): only "
                        "required-field presence was checked. A 'Passed' result here "
                        "is weaker than full structural schema validation."
                    )

                if val_report.get("warnings"):
                    for warn in val_report["warnings"]:
                        st.info(warn)

                st.caption(f"Validator: {val_report.get('validator_version', 'unknown')}")
                st.caption(val_report.get("prototype_warning", ""))

                render_download_intro(
                    "Structural validation report JSON",
                    "Full structural validation report for offline review. Prototype/reference only — not official GS1 validation.",
                    "JSON",
                )
                st.download_button(
                    "Download structural validation report JSON",
                    data=json.dumps(val_report, indent=2, ensure_ascii=False).encode("utf-8"),
                    file_name="product_passport_validation_report.json",
                    mime="application/json",
                    use_container_width=True,
                )

    with tab_examples:
        with st.container(border=True):
            render_section_header(
                1,
                "Reference Examples",
                "Example and EPCIS example entries from the source manifest. "
                "Local committed examples can be previewed below. "
                "Placeholder entries require a separate download.",
            )
            st.info(
                "Prototype/reference examples only. Not official GS1 or DPP production data. "
                "The minimal example is committed to the repository for structural testing."
            )

        if pp_manifest_data:
            example_entries = [
                s for s in pp_manifest_data.get("sources", [])
                if s.get("source_type") in ("example", "epcis_example")
            ]
            if example_entries:
                example_rows = [
                    {
                        "source_id": e.get("source_id", ""),
                        "title": e.get("title", ""),
                        "sector": e.get("sector", ""),
                        "source_type": e.get("source_type", ""),
                        "local_path": e.get("local_path", ""),
                    }
                    for e in example_entries
                ]
                st.dataframe(
                    pd.DataFrame(example_rows),
                    hide_index=True,
                    use_container_width=True,
                )

                selected_example_id = st.selectbox(
                    "Preview example",
                    [e.get("source_id", "") for e in example_entries],
                )
                selected_example = next(
                    (e for e in example_entries if e.get("source_id") == selected_example_id),
                    None,
                )
                if selected_example:
                    local_path = selected_example.get("local_path", "")
                    example_file = REPOSITORY_ROOT / local_path if local_path else None
                    if example_file and example_file.is_file():
                        try:
                            example_data = json.loads(example_file.read_text(encoding="utf-8"))
                            with st.expander("Example JSON preview (prototype/reference only — not production data)", expanded=True):
                                st.json(example_data)
                        except (json.JSONDecodeError, OSError) as exc:
                            st.warning(f"Could not load example: {exc}")
                    else:
                        st.info(
                            f"Local file not yet available: `{local_path}`. "
                            "This is a placeholder entry. Download the file from the URL in the source manifest "
                            "and place it at the path shown."
                        )
            else:
                st.info("No example entries found in the source manifest.")
        else:
            st.info("Source manifest could not be loaded.")
