# UI Implementation Plan

## Commit 1: design docs and UI rules

**Goal:** Document the current interface, visual direction, tokens, and
guardrails.

**Files likely to change:** `DESIGN.md`, `docs/design-direction.md`,
`docs/UI_IMPLEMENTATION_PLAN.md`.

**Verify:** Required components, states, accessibility, and responsive guidance
are covered.

**Do not touch:** Application code, tests, converter code, mappings, or output.

## Commit 2: design tokens and shared styling utilities

**Goal:** Add a small Streamlit-specific helper for tokens and minimal CSS, then
apply it to the page foundation.

**Files likely to change:** `app/streamlit_app.py`, optionally one small module
under `app/`, and `docs/UI_CHANGES.md`.

**Verify:** AppTest behavior, keyboard focus, narrow-screen stacking, and
session-state persistence.

**Do not touch:** Conversion flow, state keys, package code, mappings, or CLI.

## Commit 3: main screen layout polish

**Goal:** Refine header, input workflow, sidebar grouping, and primary action.

**Files likely to change:** Streamlit UI files and `docs/UI_CHANGES.md`.

**Verify:** Upload, profile change, conversion, and empty state.

**Do not touch:** Result content, report generation, or conversion behavior.

## Commit 4: result and report cards

**Goal:** Give validation, identity, JSON-LD, mapping preview, and downloads a
consistent report hierarchy.

**Files likely to change:** Streamlit UI files and `docs/UI_CHANGES.md`.

**Verify:** All four downloads, persisted results after rerun, and long report
content.

**Do not touch:** Report bytes, generated filenames, or output schemas.

## Commit 5: states and accessibility polish

**Goal:** Refine loading, empty, error, warning, success, hover, disabled, and
focus states.

**Files likely to change:** Streamlit UI files, focused UI tests if essential,
and `docs/UI_CHANGES.md`.

**Verify:** Keyboard use, contrast, reduced motion, conversion errors, and
validation variants.

**Do not touch:** Validation rules or exception behavior.

## Commit 6: responsive cleanup

**Goal:** Review phone, tablet, and desktop layout and remove remaining spacing
or overflow issues.

**Files likely to change:** Shared styling helper, Streamlit UI files, and
`docs/UI_CHANGES.md`.

**Verify:** Narrow and wide viewport screenshots plus the full test suite.

**Do not touch:** Application flow, dependencies, converter package, mappings,
or generated output.
