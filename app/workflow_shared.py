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
        "key": "candidates",
        "title": "Generate Mapping Candidates",
        "marker": "MAP",
        "description": (
            "Suggest possible GDSN/BMS/XPath sources for WebVoc properties."
        ),
        "outcome": "Review-only candidate report; nothing is written.",
    },
    {
        "key": "standards",
        "title": "Standards Review",
        "marker": "SDR",
        "description": "Inspect open standards and governance decisions.",
        "outcome": "Read-only SDR context.",
    },
    {
        "key": "prototype",
        "title": "Create JSON-LD Prototype",
        "marker": "LD",
        "description": "Manually author GS1 Web Vocabulary JSON-LD.",
        "outcome": "Prototype JSON-LD with governance warning.",
    },
    {
        "key": "product_passport",
        "title": "Validate Product Passport Sources",
        "marker": "PP",
        "description": (
            "Inspect local Product Passport reference sources, schemas, and "
            "examples."
        ),
        "outcome": "Source inventory + structural validation report.",
    },
    {
        "key": "product_passport_builder",
        "title": "Build Product Passport Prototype",
        "marker": "PB",
        "description": (
            "Wrap GS1 JSON-LD into a prototype Product Passport envelope."
        ),
        "outcome": "Passport JSON-LD + structural validation report.",
    },
)
DEFAULT_WORKFLOW_MODE = WORKFLOW_MODES[0]["title"]

# Information-architecture grouping for the workflow overview (v0.13.0).
# Cards are rendered under these group headings, in this order, so seven
# Guided route navigation (v0.13.3): three primary routes group the seven
# workflows. Stage 1 shows the route cards; stage 2 shows only the child
# workflow cards for the selected route (progressive disclosure). The routes are
# a UI grouping layer only — every workflow key is unchanged and reachable.
ROUTES = (
    {
        "key": "jsonld_creation",
        "title": "Create GS1 JSON-LD",
        "marker": "JSON-LD",
        "description": (
            "Create GS1 Web Vocabulary JSON-LD from product XML or manual "
            "prototype input."
        ),
        "outcome": "GS1 JSON-LD output.",
        "children": ("convert", "prototype"),
        "child_heading": "Choose how to create JSON-LD",
    },
    {
        "key": "vocabulary_mapping",
        "title": "Vocabulary & Mapping",
        "marker": "MAP",
        "description": (
            "Review vocabulary, mappings, candidate sources and standards "
            "decisions."
        ),
        "outcome": "Review evidence and governance context.",
        "children": ("explore", "candidates", "standards"),
        "child_heading": "Choose a review tool",
    },
    {
        "key": "product_passport_bridge",
        "title": "Product Passport Bridge",
        "marker": "PASS",
        "description": (
            "Work with Product Passport sources and prototype passport output."
        ),
        "outcome": "Source validation or Passport JSON-LD.",
        "children": ("product_passport", "product_passport_builder"),
        "child_heading": "Choose a Product Passport tool",
    },
)
DEFAULT_ROUTE = ROUTES[0]["key"]


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


def set_route(route_key: str) -> None:
    """Select a primary route and open its first child workflow.

    This is a UI navigation grouping only. It changes which child workflow cards
    are shown and makes the route's first child the active workflow, without
    clearing any conversion or result state.
    """
    st.session_state["selected_route"] = route_key
    for route in ROUTES:
        if route["key"] == route_key:
            first_child_key = route["children"][0]
            for mode in WORKFLOW_MODES:
                if mode["key"] == first_child_key:
                    st.session_state["workflow_mode"] = mode["title"]
                    return
            return


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
