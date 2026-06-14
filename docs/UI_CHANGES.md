# UI Changes

## Changed UI files

- `app/ui.py`
- `app/streamlit_app.py`
- `DESIGN.md`
- `docs/design-direction.md`
- `docs/UI_IMPLEMENTATION_PLAN.md`
- `docs/UI_CHANGES.md`

## What changed visually

- Added a compact header with clearer purpose, version, privacy context, and
  traceability cues.
- Introduced shared spacing, radius, color, surface, and interaction tokens.
- Added a restrained page background, bordered panels, and subtle depth.
- Grouped the sidebar into conversion settings and profile coverage.
- Grouped upload, result review, mapping preview, and downloads into numbered
  workflow sections.
- Added short descriptions to product identity, JSON-LD, and mapping previews.
- Arranged download actions in a balanced two-column grid on wider screens.
- Made primary, secondary, and download actions consistently full-width.
- Added visible focus styling, reduced-motion support, and narrow-screen
  padding adjustments.
- Added a native spinner during conversion.

## What was intentionally not changed

- Converter, mapping, validation, CLI, and reporting logic.
- Mapping YAML files and generated JSON-LD structure.
- Session-state keys, rerun behavior, result persistence, or reset behavior.
- Mapping-profile options or their default selection.
- Download count, contents, filenames, or formats.
- Production dependencies.

## Manual review checklist

- [ ] Header hierarchy reads clearly at desktop and phone widths.
- [ ] Sidebar groups are easy to scan and the active mapping remains visible.
- [ ] Upload and convert flow is obvious with and without a selected file.
- [ ] Keyboard focus is visible on convert, download, and reset actions.
- [ ] Success, warning, and error messages remain distinct and readable.
- [ ] JSON-LD and mapping previews are comfortable to scan.
- [ ] Four downloads align as two columns and stack acceptably when narrow.
- [ ] Results remain visible after reruns and download interactions.
- [ ] Changing the mapping profile clears stale results.

## Known limitations

- Streamlit controls retain framework-defined markup and some theme behavior.
- The CSS uses stable Streamlit `data-testid` hooks for the main container,
  sidebar, and bordered containers; these should be rechecked after major
  Streamlit upgrades.
- Automated tests verify behavior, not pixel-level presentation.
- A human visual review is still required across common browser widths and
  operating-system font rendering.
