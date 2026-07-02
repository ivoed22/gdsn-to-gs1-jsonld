"""Explore GS1 Web Vocabulary workflow."""

from __future__ import annotations

import json
from dataclasses import asdict

import pandas as pd
import streamlit as st

from app.ui import render_section_header
from app.workflow_shared import REPOSITORY_ROOT
from gdsn_to_gs1_jsonld.webvoc_explorer import (
    COVERAGE_STATUSES,
    PROPERTY_GROUPS,
    build_explorer_dataset,
    filter_properties,
    property_to_row,
)


@st.cache_data(show_spinner=False)
def load_webvoc_explorer_dataset() -> object:
    return build_explorer_dataset(
        webvoc_path=REPOSITORY_ROOT / "webvoc" / "current" / "gs1Voc.jsonld",
        catalog_path=(
            REPOSITORY_ROOT
            / "mapping_catalog"
            / "gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_3_webvoc_validated.csv"
        ),
        backlog_path=(
            REPOSITORY_ROOT
            / "docs"
            / "standards-decisions"
            / "standards_review_backlog.json"
        ),
        metadata_path=REPOSITORY_ROOT / "webvoc" / "current" / "metadata.json",
        linktypes_path=REPOSITORY_ROOT / "webvoc" / "current" / "linktypes.json",
    )


def render_webvoc_explorer() -> None:
    try:
        dataset = load_webvoc_explorer_dataset()
    except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError) as exc:
        st.error(f"Web Vocabulary Explorer could not load local sources: {exc}")
        return

    with st.container(border=True):
        render_section_header(
            1,
            "Explore GS1 Web Vocabulary",
            "Browse the local GS1 Web Vocabulary snapshot and compare vocabulary "
            "terms with GDSN mapping coverage.",
        )
        summary = dataset.summary
        metric_columns = st.columns(5)
        metric_columns[0].metric(
            "WebVoc version",
            summary.get("webvoc_version") or "unknown",
        )
        metric_columns[1].metric("Classes", summary["class_count"])
        metric_columns[2].metric("Properties", summary["property_count"])
        metric_columns[3].metric("Mapped properties", summary["mapped_property_count"])
        metric_columns[4].metric(
            "Standards review",
            summary["standards_review_property_count"],
        )
        with st.expander("Class reference"):
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Class": item.term_id,
                            "Label": item.label,
                            "Description": item.comment,
                            "subClassOf": ", ".join(item.sub_class_of),
                            "Status": item.term_status,
                        }
                        for item in dataset.classes
                    ]
                ),
                hide_index=True,
                use_container_width=True,
            )

    properties = list(dataset.properties)
    all_domains = sorted(
        {
            domain
            for property_item in properties
            for domain in property_item.domain
            if domain
        }
    )

    with st.container(border=True):
        render_section_header(
            2,
            "Filter vocabulary coverage",
            "Narrow by review group, domain, coverage status, and term text. "
            "The Explorer is read-only and does not write mappings.",
        )
        top_left, top_mid, top_right = st.columns([1.2, 1, 1])
        with top_left:
            selected_group = st.selectbox(
                "Group",
                ["All groups", *PROPERTY_GROUPS],
                help="Pragmatic grouping for GS1/GDSN mapping review.",
            )
        with top_mid:
            selected_domain = st.selectbox(
                "Domain",
                ["All domains", *all_domains],
                help="Optional Web Vocabulary domain/root selector.",
            )
        with top_right:
            selected_coverage = st.selectbox(
                "Coverage status",
                ["All statuses", *COVERAGE_STATUSES],
            )
        search = st.text_input(
            "Search properties",
            placeholder="Search property, label, comment, BMS field, or XPath evidence",
        )
        check_left, check_right = st.columns(2)
        with check_left:
            only_mapped = st.checkbox("Show only mapped")
        with check_right:
            only_standards_review = st.checkbox("Show only standards review")

    filtered_properties = filter_properties(
        properties,
        group=selected_group,
        coverage_status=selected_coverage,
        search=search,
        only_mapped=only_mapped,
        only_standards_review=only_standards_review,
    )
    if selected_domain != "All domains":
        filtered_properties = [
            item for item in filtered_properties if selected_domain in item.domain
        ]

    with st.container(border=True):
        render_section_header(
            3,
            "Review vocabulary properties",
            "Inspect local WebVoc terms with catalog coverage, BMS/XPath evidence, "
            "and SDR indicators.",
        )
        st.caption(
            f"{len(filtered_properties)} of {len(properties)} properties shown. "
            "Coverage comes from the local mapping catalog."
        )
        visible_columns = {
            "Group",
            "Property",
            "Label",
            "Domain",
            "Range",
            "Coverage",
            "BMS/XPath evidence",
            "SDR indicator",
        }
        table_rows = [
            {
                key: value
                for key, value in property_to_row(property_item).items()
                if key in visible_columns
            }
            for property_item in filtered_properties
        ]
        st.dataframe(
            pd.DataFrame(table_rows),
            hide_index=True,
            use_container_width=True,
        )

        if filtered_properties:
            selected_property_id = st.selectbox(
                "Selected property detail",
                [item.term_id for item in filtered_properties],
                format_func=lambda term: next(
                    (
                        f"{item.term_id} - {item.label}"
                        for item in filtered_properties
                        if item.term_id == term
                    ),
                    term,
                ),
            )
            selected_property = next(
                item
                for item in filtered_properties
                if item.term_id == selected_property_id
            )
            with st.expander("Property detail", expanded=True):
                detail_left, detail_right = st.columns([1.1, 1])
                with detail_left:
                    st.markdown("**Term**")
                    st.code(selected_property.term_id)
                    st.markdown("**Full IRI**")
                    st.code(selected_property.full_iri)
                    st.markdown("**Label**")
                    st.write(selected_property.label or "No label available")
                    st.markdown("**Description**")
                    st.write(selected_property.comment or "No description available")
                with detail_right:
                    st.markdown("**Domain / Range**")
                    st.write(", ".join(selected_property.domain) or "Not specified")
                    st.write(", ".join(selected_property.range) or "Not specified")
                    st.markdown("**subPropertyOf**")
                    st.write(
                        ", ".join(selected_property.sub_property_of)
                        or "Not specified"
                    )
                    st.markdown("**Coverage status**")
                    st.code(selected_property.coverage_status)
                    st.markdown("**Link type**")
                    st.write("Yes" if selected_property.is_link_type else "No")

                st.markdown("**GDSN mapping evidence**")
                if selected_property.evidence:
                    st.dataframe(
                        pd.DataFrame(
                            [
                                asdict(evidence)
                                for evidence in selected_property.evidence
                            ]
                        ),
                        hide_index=True,
                        use_container_width=True,
                    )
                else:
                    st.info("No mapping catalog evidence is linked to this property.")

                st.markdown("**SDR/governance notes**")
                if selected_property.governance:
                    st.dataframe(
                        pd.DataFrame(
                            [
                                asdict(reference)
                                for reference in selected_property.governance
                            ]
                        ),
                        hide_index=True,
                        use_container_width=True,
                    )
                else:
                    st.info("No open SDR reference is linked to this property.")

    with st.container(border=True):
        render_section_header(
            4,
            "Manual JSON-LD Builder",
            "Use the Create JSON-LD Prototype workflow to author range-aware "
            "manual product markup.",
        )
        st.info(
            "The Explorer remains read-only. Manual prototypes are entered in a "
            "separate workflow and are not GDSN/BMS/XPath traceable unless "
            "linked to governed mapping evidence."
        )
