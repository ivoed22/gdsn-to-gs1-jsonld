"""Shared constants, session-state helpers, and loaders used across workflows.

Extracted from app/streamlit_app.py in v0.14.0 (app modularization). Behaviour
is unchanged; this module exists so app/workflows/*.py and app/streamlit_app.py
can share the same route/workflow registry and session-state helpers without
importing from each other.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_DIRECTORY = REPOSITORY_ROOT / "src"


def _ensure_import_paths() -> None:
    """Make local package imports work in Streamlit Cloud script execution."""
    for directory in (REPOSITORY_ROOT, SRC_DIRECTORY):
        directory_path = str(directory)
        if directory_path not in sys.path:
            sys.path.insert(0, directory_path)


_ensure_import_paths()

RESULT_STATE_KEYS = (
    "conversion_result",
    "jsonld_bytes",
    "mapping_report_bytes",
    "validation_report_bytes",
    "unmapped_fields_bytes",
    "output_name_base",
)
BATCH_RESULT_STATE_KEYS = (
    "batch_conversion_report",
    "batch_export_zip_bytes",
)
# Consolidated navigation (v0.30.0): five workflows, direct navigation.
# The v0.13.3 two-stage route->child card navigation was removed together
# with the 9-workflow split it existed to manage: Builder Manifest Expansion
# Analysis lives inside Create JSON-LD Prototype, Generate Mapping
# Candidates + Standards Review merged into Mapping Governance, and the two
# Product Passport workflows merged into one. Every capability remains
# reachable; only the grouping changed.
WORKFLOW_MODES = (
    {
        "key": "convert",
        "title": "Convert GDSN XML",
        "marker": "XML",
        "description": "Convert product XML into GS1 Web Vocabulary JSON-LD.",
        "outcome": "JSON-LD + mapping, validation, and unmapped-field evidence.",
    },
    {
        "key": "explore",
        "title": "Explore GS1 Web Vocabulary",
        "marker": "VOC",
        "description": "Browse local GS1 vocabulary classes and properties.",
        "outcome": "Vocabulary evidence and coverage context (read-only).",
    },
    {
        "key": "prototype",
        "title": "Create JSON-LD Prototype",
        "marker": "LD",
        "description": (
            "Manually author GS1 Web Vocabulary JSON-LD, with manifest "
            "expansion analysis alongside."
        ),
        "outcome": "Prototype JSON-LD with governance warning.",
    },
    {
        "key": "governance",
        "title": "Mapping Governance",
        "marker": "GOV",
        "description": (
            "Generate mapping candidates and review standards decisions "
            "and vocabulary freshness in one place."
        ),
        "outcome": "Review-only reports and sign-offs; nothing is written.",
    },
    {
        "key": "product_passport",
        "title": "Product Passport",
        "marker": "PP",
        "description": (
            "Inspect Product Passport sources, validate prototype JSON, and "
            "build a prototype passport envelope."
        ),
        "outcome": "Source inventory, validation report, or Passport JSON-LD.",
    },
)
DEFAULT_WORKFLOW_MODE = WORKFLOW_MODES[0]["title"]


def clear_results() -> None:
    for key in RESULT_STATE_KEYS:
        st.session_state.pop(key, None)


def clear_batch_results() -> None:
    for key in BATCH_RESULT_STATE_KEYS:
        st.session_state.pop(key, None)


def clear_all_results() -> None:
    clear_results()
    clear_batch_results()


def set_workflow_mode(mode: str) -> None:
    st.session_state["workflow_mode"] = mode


def navigate_to_webvoc_property(property_id: str) -> None:
    """Deep-link to the Explore workflow's detail view for one property (v0.26.0).

    A ``st.button(on_click=...)`` callback, same pattern as
    :func:`set_workflow_mode`: it only sets session-state keys before the
    rerun. It resets Explore's other filters to "show everything" and
    pre-fills its search with *property_id* so the target property is
    reliably the (typically only) match, then pre-selects it in the detail
    selectbox. Explore's own render logic and data are otherwise untouched
    -- this does not fetch or compute anything new.
    """
    st.session_state["workflow_mode"] = "Explore GS1 Web Vocabulary"
    st.session_state["webvoc_explorer_group"] = "All groups"
    st.session_state["webvoc_explorer_domain"] = "All domains"
    st.session_state["webvoc_explorer_coverage"] = "All statuses"
    st.session_state["webvoc_explorer_only_mapped"] = False
    st.session_state["webvoc_explorer_only_standards_review"] = False
    st.session_state["webvoc_explorer_search"] = property_id
    st.session_state["webvoc_explorer_selected_property"] = property_id


def _load_webvoc_metadata() -> dict:
    webvoc_metadata_path = REPOSITORY_ROOT / "webvoc" / "current" / "metadata.json"
    if not webvoc_metadata_path.is_file():
        return {}
    try:
        return json.loads(webvoc_metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _load_open_standards_backlog() -> list[dict]:
    backlog_path = (
        REPOSITORY_ROOT
        / "docs"
        / "standards-decisions"
        / "standards_review_backlog.json"
    )
    if not backlog_path.is_file():
        return []
    try:
        loaded_backlog = json.loads(backlog_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(loaded_backlog, list):
        return []
    return [
        item
        for item in loaded_backlog
        if isinstance(item, dict) and item.get("status") == "open"
    ]


def _backlog_categories(backlog: list[dict]) -> list[str]:
    return sorted(
        {
            str(item["category"]).replace("_", " ")
            for item in backlog
            if item.get("category")
        }
    )
