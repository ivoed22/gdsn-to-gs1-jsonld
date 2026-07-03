"""Create JSON-LD Prototype workflow (manual builder)."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

import pandas as pd
import streamlit as st

from app.ui import render_section_header, render_status_badge
from app.workflow_shared import REPOSITORY_ROOT
from app.workflows.explore import load_webvoc_explorer_dataset
from gdsn_to_gs1_jsonld.builder_status import (
    build_hard_mapping_index,
    compute_field_status,
    summarize_field_statuses,
)
from gdsn_to_gs1_jsonld.jsonld_builder import (
    build_empty_builder_state,
    get_builder_fields,
    get_builder_groups,
    infer_input_type,
    jsonld_bytes as prototype_jsonld_bytes,
    load_builder_manifest,
    object_subfield_key,
    serialize_builder_state_to_jsonld,
    update_builder_value,
    validate_builder_state,
)

# Status-badge tone per builder field status (see builder_status.STATUS_VALUES).
_FIELD_STATUS_TONES = {
    "filled": "accepted",
    "missing": "blocked",
    "review_required": "review",
    "hard_mapping_review": "review",
    "codelist_pending": "archived",
    "external_source_required": "archived",
    "extension_candidate": "archived",
    "blocked": "blocked",
    "optional_empty": "archived",
}
_FIELD_STATUS_LABELS = {
    "filled": "Filled",
    "missing": "Missing (required)",
    "review_required": "Review required",
    "hard_mapping_review": "Hard-mapping review",
    "codelist_pending": "Codelist pending",
    "external_source_required": "External source required",
    "extension_candidate": "Extension candidate",
    "blocked": "Blocked",
    "optional_empty": "Not filled",
}


@st.cache_data(show_spinner=False)
def _load_builder_manifest() -> dict:
    return load_builder_manifest(
        REPOSITORY_ROOT / "builder_manifest" / "product_builder_v0_10.yaml"
    )


@st.cache_data(show_spinner=False)
def _load_hard_mapping_index() -> dict[str, tuple[bool, list[str]]]:
    return build_hard_mapping_index(
        REPOSITORY_ROOT
        / "reference_data"
        / "normalized"
        / "gdsn_attributes_bms_xpath_3_1_36.csv"
    )


def _builder_key(property_id: str, suffix: str = "value") -> str:
    safe_property = (
        property_id.replace(":", "_")
        .replace("/", "_")
        .replace("-", "_")
    )
    reset_index = st.session_state.get("manual_builder_reset_index", 0)
    return f"manual_builder_{reset_index}_{safe_property}_{suffix}"


def reset_manual_builder() -> None:
    st.session_state.pop("manual_builder_values", None)
    for key in list(st.session_state):
        if key.startswith("manual_builder_") and key != "manual_builder_reset_index":
            st.session_state.pop(key, None)
    st.session_state["manual_builder_reset_index"] = (
        st.session_state.get("manual_builder_reset_index", 0) + 1
    )


def _property_metadata_index(dataset: object, manifest: dict) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for property_item in getattr(dataset, "properties", []):
        evidence = [
            asdict(item)
            for item in getattr(property_item, "evidence", [])
        ]
        index[property_item.term_id] = {
            "term_id": property_item.term_id,
            "label": property_item.label,
            "comment": property_item.comment,
            "domain": list(property_item.domain),
            "range": list(property_item.range),
            "sub_property_of": list(property_item.sub_property_of),
            "type": list(property_item.types),
            "term_status": property_item.term_status,
            "is_link_type": property_item.is_link_type,
            "coverage_status": property_item.coverage_status,
            "evidence": evidence,
            "supported_in_v0_10": True,
        }
    for group in manifest.get("groups", []):
        for field in group.get("properties", []):
            property_id = field.get("property_id")
            if not property_id:
                continue
            metadata = dict(index.get(property_id, {"term_id": property_id}))
            metadata.update(
                {
                    "requirement": field.get("requirement", "optional"),
                    "input_type_override": field.get("input_type_override"),
                    "example_value": field.get("example_value", ""),
                    "help_text": field.get("help_text", ""),
                    "appears_because": field.get("appears_because", ""),
                    "supported_in_v0_10": field.get("supported_in_v0_10", True),
                    "planned_reason": field.get("planned_reason", ""),
                    "object_type": field.get("object_type"),
                    "object_fields": field.get("object_fields"),
                    "options": field.get("options"),
                }
            )
            index[property_id] = metadata
    return index


def _metadata_for_field(
    field: dict[str, Any],
    property_metadata: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    property_id = str(field["property_id"])
    metadata = dict(property_metadata.get(property_id, {"term_id": property_id}))
    metadata.update(
        {
            "requirement": field.get("requirement", "optional"),
            "input_type_override": field.get("input_type_override"),
            "example_value": field.get("example_value", ""),
            "help_text": field.get("help_text", ""),
            "appears_because": field.get("appears_because", ""),
            "supported_in_v0_10": field.get("supported_in_v0_10", True),
            "planned_reason": field.get("planned_reason", ""),
        }
    )
    return metadata


def _value_present(state: dict[str, Any], metadata: dict[str, Any]) -> bool:
    """True if this field (or, for objects, any sub-field) has a value."""
    property_id = metadata["term_id"]
    values = state.get("values", {})
    object_fields = metadata.get("object_fields") or []
    if object_fields:
        return any(
            object_subfield_key(property_id, sub.get("property_id")) in values
            for sub in object_fields
            if sub.get("property_id")
        )
    return property_id in values


def _render_field_header(
    metadata: dict[str, Any],
    *,
    status: str,
    status_reasons: list[str],
) -> None:
    property_id = metadata["term_id"]
    label = metadata.get("label") or property_id.split(":", 1)[-1]
    requirement = str(metadata.get("requirement") or "optional").title()
    ranges = ", ".join(metadata.get("range") or []) or "range unavailable"
    evidence = metadata.get("evidence") or []
    evidence_hint = (
        f"{len(evidence)} mapping evidence row(s)"
        if evidence
        else "No catalog evidence linked"
    )
    header_col, badge_col = st.columns([3, 1])
    with header_col:
        st.markdown(f"**{label}** — {requirement}")
    with badge_col:
        render_status_badge(
            _FIELD_STATUS_LABELS.get(status, status),
            _FIELD_STATUS_TONES.get(status, "archived"),
        )
    st.caption(f"`{property_id}` · Range: {ranges} · {evidence_hint}")
    if metadata.get("help_text"):
        st.caption(str(metadata["help_text"]))
    if metadata.get("example_value"):
        st.caption(f"Example: `{metadata['example_value']}`")
    if status_reasons:
        st.caption(" · ".join(status_reasons))
    if evidence:
        with st.expander(f"Evidence ({len(evidence)})", expanded=False):
            evidence_df = pd.DataFrame(evidence)
            display_columns = [
                col
                for col in (
                    "source_attribute_name",
                    "bms_id",
                    "gdsn_xpath",
                    "mapping_status",
                    "confidence",
                )
                if col in evidence_df.columns
            ]
            st.dataframe(
                evidence_df[display_columns] if display_columns else evidence_df,
                hide_index=True,
                use_container_width=True,
            )


def _coerce_builder_widget_value(value: Any, input_type: str) -> Any:
    if input_type == "checkbox":
        return bool(value)
    if isinstance(value, str):
        return value.strip()
    return value


def _render_field_widget(
    state: dict[str, Any],
    state_id: str,
    input_type: str,
    metadata: dict[str, Any],
    *,
    default_language: str,
) -> dict[str, Any]:
    """Render a single builder input for *state_id* and update state.

    Used for both top-level fields and nested-object sub-fields; the state key
    for a sub-field is the ``parent#child`` compound id.
    """
    key = _builder_key(state_id)
    if input_type == "language_text":
        value = st.text_input(
            f"{state_id} value",
            key=key,
            placeholder=str(metadata.get("example_value") or ""),
            label_visibility="collapsed",
        )
        if value:
            state = update_builder_value(
                state, state_id, value, language=default_language
            )
        else:
            state = update_builder_value(state, state_id, "")
    elif input_type == "quantity":
        value_col, unit_col = st.columns([1, 0.7])
        value = value_col.text_input(
            f"{state_id} quantity value",
            key=key,
            placeholder="1.0",
            label_visibility="collapsed",
        )
        unit_code = unit_col.text_input(
            f"{state_id} unitCode",
            key=_builder_key(state_id, "unit"),
            placeholder="LTR",
            label_visibility="collapsed",
        )
        if value or unit_code:
            state = update_builder_value(state, state_id, value, unit_code=unit_code)
        else:
            state = update_builder_value(state, state_id, "")
    elif input_type == "checkbox":
        value = st.checkbox(
            f"{state_id} value",
            key=key,
            label_visibility="collapsed",
        )
        if value:
            state = update_builder_value(state, state_id, value)
        else:
            state = update_builder_value(state, state_id, "")
    elif input_type == "url":
        value = st.text_input(
            f"{state_id} URL",
            key=key,
            placeholder=str(metadata.get("example_value") or "https://"),
            label_visibility="collapsed",
        )
        if value:
            state = update_builder_value(state, state_id, value)
        else:
            state = update_builder_value(state, state_id, "")
    elif input_type == "code":
        options = metadata.get("options") or []
        labels = ["— none —"] + [str(opt.get("label") or opt.get("value")) for opt in options]
        values = [""] + [str(opt.get("value")) for opt in options]
        selected_label = st.selectbox(
            f"{state_id} code",
            labels,
            key=key,
            label_visibility="collapsed",
        )
        selected_value = values[labels.index(selected_label)] if selected_label in labels else ""
        if selected_value:
            state = update_builder_value(state, state_id, selected_value)
        else:
            state = update_builder_value(state, state_id, "")
    else:
        value = st.text_input(
            f"{state_id} value",
            key=key,
            placeholder=str(metadata.get("example_value") or ""),
            label_visibility="collapsed",
        )
        value = _coerce_builder_widget_value(value, input_type)
        if value not in ("", None):
            state = update_builder_value(state, state_id, value)
        else:
            state = update_builder_value(state, state_id, "")
    return state


def _render_manual_field(
    state: dict[str, Any],
    metadata: dict[str, Any],
    *,
    default_language: str,
    hard_mapping_index: dict[str, tuple[bool, list[str]]],
) -> tuple[dict[str, Any], str]:
    property_id = metadata["term_id"]
    input_type = infer_input_type(
        metadata,
        metadata.get("input_type_override"),
    )
    status, status_reasons = compute_field_status(
        metadata,
        value_present=_value_present(state, metadata),
        hard_mapping_index=hard_mapping_index,
    )
    _render_field_header(metadata, status=status, status_reasons=status_reasons)
    if not metadata.get("supported_in_v0_10", True):
        st.info(
            "Planned for a later release: "
            + str(metadata.get("planned_reason") or "requires governed modelling")
        )
        return state, status

    if input_type == "object":
        object_fields = metadata.get("object_fields") or []
        if not object_fields:
            st.info("This object has no simple sub-fields available to author.")
            return state, status
        object_type = metadata.get("object_type") or "object"
        st.caption(
            f"Nested {object_type} object — fill any sub-field to include it in "
            "the prototype."
        )
        for sub in object_fields:
            sub_id = sub.get("property_id")
            if not sub_id:
                continue
            sub_type = sub.get("input_type_override") or sub.get("input_type") or "text"
            compound_id = object_subfield_key(property_id, sub_id)
            help_text = sub.get("help_text") or ""
            st.markdown(f"**{sub_id}**" + (f" — {help_text}" if help_text else ""))
            state = _render_field_widget(
                state,
                compound_id,
                sub_type,
                sub,
                default_language=default_language,
            )
        return state, status

    state = _render_field_widget(
        state,
        property_id,
        input_type,
        metadata,
        default_language=default_language,
    )
    return state, status


def render_manual_jsonld_builder() -> None:
    try:
        dataset = load_webvoc_explorer_dataset()
        manifest = _load_builder_manifest()
    except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError) as exc:
        st.error(f"Manual JSON-LD Builder could not load local sources: {exc}")
        return

    property_metadata = _property_metadata_index(dataset, manifest)
    categories = [
        item["label"]
        for item in manifest.get("product_categories", [])
        if isinstance(item, dict) and item.get("label")
    ]
    root_classes = [
        item["label"]
        for item in manifest.get("root_classes", [])
        if isinstance(item, dict) and item.get("label")
    ]
    language_options = manifest.get("default_language_options", ["en", "nl", "de", "fr"])

    with st.container(border=True):
        render_section_header(
            1,
            "Create JSON-LD Prototype",
            "Manually select GS1 Web Vocabulary properties, enter values, and "
            "preview prototype JSON-LD live. This is a review and authoring tool, "
            "not a GDSN XML converter.",
        )
        st.warning(
            "⚠️ Prototype output only. "
            "This JSON-LD is entered manually, not generated from GDSN XML. "
            "It is not BMS/XPath traceable unless separately linked to governed "
            "mapping evidence. It is not an official GS1 validation result."
        )

    control_column, form_column, output_column = st.columns([0.86, 1.25, 1.05])
    with control_column:
        with st.container(border=True):
            render_section_header(
                2,
                "Builder controls",
                "Choose the root class, category, language, and thematic group.",
            )
            root_class = st.selectbox(
                "Root class",
                root_classes or ["Product"],
                help="v0.10 supports Product only.",
            )
            product_category = st.selectbox(
                "Product category",
                categories or ["General Product"],
                help="Controls which thematic groups are offered.",
            )
            default_language = st.selectbox(
                "Default language",
                language_options,
                help="Used for language-tagged Web Vocabulary values.",
            )
            st.checkbox(
                "Product is for sale (form helper only — no JSON-LD emitted)",
                help=(
                    "This is a form-scoping helper only. v0.10 does not emit "
                    "offer or pricing JSON-LD for this flag."
                ),
            )

            groups = get_builder_groups(manifest, product_category)
            group_labels = [group["label"] for group in groups]
            selected_group_label = st.selectbox(
                "Thematic group",
                group_labels,
                help="Select which manifest-driven field group to edit.",
            )
            selected_group = next(
                group for group in groups if group["label"] == selected_group_label
            )

    state = build_empty_builder_state(root_class=root_class)
    state["product_category"] = product_category
    state["default_language"] = default_language
    state["selected_groups"] = [selected_group["key"]]
    state["values"] = dict(st.session_state.get("manual_builder_values", {}))
    hard_mapping_index = _load_hard_mapping_index()

    # Section navigation: a coverage overview across every group in the
    # selected category, using already-persisted values, so the reviewer can
    # see where required fields are still missing before switching groups.
    with st.container(border=True):
        render_section_header(
            3,
            "Coverage overview",
            "Field status by thematic group in the selected category. "
            "Switch groups with the selector above.",
        )
        overview_rows = []
        for group in groups:
            group_fields = get_builder_fields(manifest, group)
            group_statuses = []
            for field in group_fields:
                metadata = _metadata_for_field(field, property_metadata)
                status, _ = compute_field_status(
                    metadata,
                    value_present=_value_present(state, metadata),
                    hard_mapping_index=hard_mapping_index,
                )
                group_statuses.append(status)
            counts = summarize_field_statuses(group_statuses)
            overview_rows.append(
                {
                    "Group": group["label"],
                    "Fields": len(group_fields),
                    "Filled": counts["filled"],
                    "Missing (required)": counts["missing"],
                    "Flagged for review": (
                        counts["review_required"] + counts["hard_mapping_review"]
                    ),
                    "Active": "→" if group["key"] == selected_group["key"] else "",
                }
            )
        st.dataframe(
            pd.DataFrame(overview_rows),
            hide_index=True,
            use_container_width=True,
        )

    fields = get_builder_fields(manifest, selected_group)
    field_metadata = [
        _metadata_for_field(field, property_metadata) for field in fields
    ]
    field_statuses = [
        compute_field_status(
            metadata,
            value_present=_value_present(state, metadata),
            hard_mapping_index=hard_mapping_index,
        )[0]
        for metadata in field_metadata
    ]
    group_counts = summarize_field_statuses(field_statuses)

    with form_column:
        with st.container(border=True):
            render_section_header(
                4,
                selected_group["label"],
                selected_group.get("description", "Enter values for this group."),
            )
            st.caption(
                f"{group_counts['filled']} filled · "
                f"{group_counts['missing']} missing (required) · "
                f"{group_counts['review_required'] + group_counts['hard_mapping_review']} "
                "flagged for review · "
                f"{len(fields)} field(s) in this group."
            )
            search_col, status_col = st.columns([1.3, 1])
            with search_col:
                search_term = st.text_input(
                    "Search fields in this group",
                    placeholder="Search by label, property, or help text",
                ).strip().lower()
            with status_col:
                status_filter = st.multiselect(
                    "Show only status",
                    options=list(_FIELD_STATUS_LABELS),
                    format_func=lambda s: _FIELD_STATUS_LABELS[s],
                    help="Leave empty to show all fields in this group.",
                )

            for metadata, status in zip(field_metadata, field_statuses):
                if status_filter and status not in status_filter:
                    continue
                if search_term:
                    haystack = " ".join(
                        str(metadata.get(key) or "")
                        for key in ("term_id", "label", "help_text")
                    ).lower()
                    if search_term not in haystack:
                        continue
                with st.container(border=True):
                    state, _ = _render_manual_field(
                        state,
                        metadata,
                        default_language=default_language,
                        hard_mapping_index=hard_mapping_index,
                    )

    jsonld_data = serialize_builder_state_to_jsonld(state, property_metadata)
    warnings = validate_builder_state(state, property_metadata)
    state["validation_warnings"] = warnings
    st.session_state["manual_builder_values"] = dict(state["values"])

    with output_column:
        with st.container(border=True):
            render_section_header(
                5,
                "Prototype JSON-LD Preview",
                "Live preview of the manually entered prototype. "
                "This is not converter output.",
            )
            if warnings:
                for warning in warnings:
                    st.warning(warning)
            st.json(jsonld_data)
            formatted_jsonld = json.dumps(
                jsonld_data,
                indent=2,
                ensure_ascii=False,
            )
            st.code(formatted_jsonld, language="json")

        with st.container(border=True):
            render_section_header(
                6,
                "Export",
                "Download the prototype, or clear the builder to start over.",
            )
            st.caption(
                f"Current group ({selected_group['label']}): "
                f"{group_counts['filled']} filled, "
                f"{group_counts['missing']} missing (required), "
                f"{group_counts['review_required'] + group_counts['hard_mapping_review']} "
                "flagged for review."
            )
            gtin = jsonld_data.get("gtin") or "manual-prototype"
            st.download_button(
                "Download prototype JSON-LD",
                data=prototype_jsonld_bytes(jsonld_data),
                file_name=f"manual_jsonld_prototype_{gtin}.jsonld",
                mime="application/ld+json",
                use_container_width=True,
            )
            st.button(
                "Clear builder",
                on_click=reset_manual_builder,
                use_container_width=True,
            )
