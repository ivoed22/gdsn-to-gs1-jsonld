"""Workbench status dashboard (v0.27.0).

Aggregates read-only health metrics that already exist inside individual
workflows -- WebVoc coverage, mapping registry status counts, open SDR
count, codelist coverage, and builder-authored field count -- into one
at-a-glance panel on the landing page, so a reviewer doesn't have to open
every workflow individually to see overall project health. No new data
source and no new computation: every number here is read from an
already-committed local file using the same loaders each source workflow
already uses.
"""

from __future__ import annotations

import json

import streamlit as st

from app.workflow_shared import REPOSITORY_ROOT
from gdsn_to_gs1_jsonld.builder_expansion_analysis import authored_property_ids
from gdsn_to_gs1_jsonld.jsonld_builder import load_builder_manifest
from gdsn_to_gs1_jsonld.mapping_registry import registry_summary
from gdsn_to_gs1_jsonld.webvoc_explorer import build_explorer_dataset


@st.cache_data(show_spinner=False)
def _load_webvoc_summary() -> dict:
    dataset = build_explorer_dataset(
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
    return dataset.summary


@st.cache_data(show_spinner=False)
def _load_registry_summary() -> dict:
    return registry_summary(
        registry_path=REPOSITORY_ROOT / "mapping" / "mapping_registry.yaml"
    )


@st.cache_data(show_spinner=False)
def _load_codelist_summary() -> dict | None:
    path = (
        REPOSITORY_ROOT
        / "reference_data"
        / "normalized"
        / "gdsn_codelists_r3_1_36_summary.json"
    )
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
def _load_builder_authored_count() -> int:
    manifest = load_builder_manifest(
        REPOSITORY_ROOT / "builder_manifest" / "product_builder_v0_10.yaml"
    )
    return len(authored_property_ids(manifest))


def render_workbench_status_dashboard(open_sdr_count: int) -> None:
    """Read-only, at-a-glance workbench health panel.

    *open_sdr_count* is passed in rather than reloaded here because the
    caller (``app/streamlit_app.py``) already loads the standards backlog
    for the sidebar; reusing it avoids loading the same file twice.
    """
    try:
        webvoc_summary = _load_webvoc_summary()
        registry_summary_data = _load_registry_summary()
        codelist_summary = _load_codelist_summary()
        builder_authored_count = _load_builder_authored_count()
    except (FileNotFoundError, OSError, ValueError) as exc:
        st.warning(f"Workbench status dashboard could not load a local source: {exc}")
        return

    with st.container(border=True):
        st.markdown(
            """
            <p class="section-kicker">At a glance</p>
            <h2>Workbench status</h2>
            <p class="app-summary">
              Every number below comes from an existing read-only workflow;
              nothing is computed only for this panel.
            </p>
            """,
            unsafe_allow_html=True,
        )

        property_count = webvoc_summary.get("property_count") or 0
        mapped_count = webvoc_summary.get("mapped_property_count") or 0
        coverage_pct = (
            f"{(mapped_count / property_count * 100):.0f}%"
            if property_count
            else "—"
        )
        accepted_count = registry_summary_data["catalog_by_status"].get(
            "accepted", 0
        )

        columns = st.columns(6)
        columns[0].metric(
            "WebVoc coverage",
            coverage_pct,
            help=(
                f"{mapped_count} of {property_count} properties mapped or "
                "high-confidence (Explore GS1 Web Vocabulary)."
            ),
        )
        columns[1].metric(
            "Registry accepted",
            accepted_count,
            help=(
                f"{registry_summary_data['catalog_rows']} total catalog "
                "rows (mapping registry)."
            ),
        )
        columns[2].metric(
            "Open SDRs",
            open_sdr_count,
            help="Open standards/governance decisions (Standards Review).",
        )
        columns[3].metric(
            "Codelists imported",
            codelist_summary["codelist_count"] if codelist_summary else "—",
            help=(
                f"{codelist_summary['value_count']} value(s) (Track D "
                "codelist registry)."
                if codelist_summary
                else "Codelist registry not available."
            ),
        )
        columns[4].metric(
            "Builder fields authored",
            builder_authored_count,
            help="Fields authorable in Create JSON-LD Prototype's manifest.",
        )
        # Distinct label from Generate Mapping Candidates' own "Hard-mapping
        # reviews recorded" metric -- this panel renders earlier in the
        # script than that workflow, so on the run where a user clicks
        # "Generate Candidates" this value reflects the *previous* rerun's
        # session state, not the one just computed. It catches up on the
        # next rerun. A distinct label avoids confusing the two.
        promotion_summary = st.session_state.get("promotion_summary")
        columns[5].metric(
            "Hard-mapping reviews (session)",
            (
                promotion_summary.get("hard_mapping_reviewed_count", 0)
                if promotion_summary
                else "—"
            ),
            help=(
                "From this session's Generate Mapping Candidates run."
                if promotion_summary
                else "Generate mapping candidates in this session to "
                "populate this metric."
            ),
        )
