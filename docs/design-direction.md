# UI Design Direction

## Current UI summary

The Streamlit app is a single-screen conversion tool with a persistent result
state. It is functionally clear and compact, but most content is rendered as a
flat sequence of default Streamlit elements.

## Main screens and components

- **Main screen:** page title, description, privacy notice, XML uploader,
  conversion action, validation state, product ID, JSON-LD preview, mapping
  report, downloads, and reset action.
- **Sidebar:** mapping-profile selector, app version, active mapping file, and
  supported field groups.
- **States:** no file, file ready, conversion failure, valid result, result with
  warnings, result with validation errors, and persisted result after reruns or
  downloads.
- **Reusable UI:** `clear_results()` is the only shared UI-related function.
  Conversion, validation, reporting, and byte generation remain in the package.

## Current layout problems

- The title, explanatory text, and privacy message compete for attention.
- Upload and conversion controls are not visually grouped as one workflow.
- Sidebar metadata and supported scope form one undifferentiated text block.
- Result sections use the same visual weight despite different purposes.
- Four download actions create a long, uneven vertical list.
- Wide layouts leave previews visually disconnected; narrow layouts have no
  explicit spacing strategy.
- Button width and hierarchy are inconsistent.
- Empty and result states are clear in words but not in page structure.
- There is no small token layer to keep future visual changes consistent.

## Proposed visual direction

Use a restrained, professional standards-tool aesthetic: neutral surfaces,
deep navy text, a precise blue accent, compact metadata, clear section labels,
and subtle borders and shadows. The interface should feel dependable and
technical without becoming dense or decorative.

The page should read in three steps:

1. Understand the purpose and privacy boundary.
2. Choose a profile, upload XML, and convert.
3. Review the status, structured output, traceability report, and downloads.

## Design principles

- Prioritize content hierarchy over decoration.
- Group controls and outputs by task.
- Use one primary action per workflow stage.
- Keep warnings and limitations visible.
- Reuse a small set of spacing, radius, color, and surface tokens.
- Prefer native Streamlit layout primitives; use minimal scoped CSS.
- Preserve all rerun and `session_state` behavior.

## Component opportunities

- Shared CSS/token injection function.
- Compact product header with an eyebrow, title, and version/status chips.
- Workflow panel for upload and conversion.
- Grouped sidebar sections for configuration and profile scope.
- Reusable section heading with short supporting text.
- Result summary panel separating status from detailed reports.
- Two-column download grid on wider screens, naturally stacking on narrow
  screens.

## Accessibility notes

- Maintain strong text and border contrast.
- Preserve visible keyboard focus rings.
- Do not rely on color alone for success, warning, or error meaning.
- Keep labels visible and descriptive.
- Use native buttons, uploader, selectbox, and expander semantics.
- Disable non-essential motion when reduced motion is requested.

## Responsive considerations

- Set a readable maximum content width while retaining Streamlit's wide mode.
- Use columns only where they can stack naturally.
- Avoid fixed component heights and horizontal scrolling for controls.
- Keep code and data previews full-width within their section.
- Reduce outer padding and card padding on small screens.

## What not to change

- Conversion, mapping, validation, CLI, and reporting logic.
- Generated JSON-LD or report content.
- Versioned mapping YAML files.
- Upload persistence or `session_state` keys.
- The number and behavior of existing actions and downloads.
- Existing Streamlit testing expectations.
