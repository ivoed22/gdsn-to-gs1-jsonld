# UI Changes

## Run locally

From the repository root:

```bash
python -m streamlit run app/streamlit_app.py
```

Stop any older Streamlit process first, run the command from the current
checkout, and hard-refresh the browser if it still has an older app session.

## Changed UI files

- `app/ui.py`
- `app/streamlit_app.py`
- `DESIGN.md`
- `docs/design-direction.md`
- `docs/UI_IMPLEMENTATION_PLAN.md`
- `docs/UI_CHANGES.md`

## What changed visually

- Added a premium dashboard composition pass:
  - the hero is shorter and now includes a compact conversion pipeline panel;
  - three workflow overview cards explain upload, mapping, and review before
    the user reaches Step 1;
  - the upload control has a clearer dropzone and a purpose-built empty state;
  - profile coverage is shown as compact badges instead of a long bullet list;
  - product identity is presented as a dedicated dashboard card;
  - JSON-LD and mapping previews use labelled expandable report areas.
- Added a clearly visible blue gradient hero with a large product title,
  version chip, privacy context, and traceability cues.
- Introduced shared spacing, radius, color, surface, and interaction tokens.
- Added a muted page background with high-contrast white panels, blue top
  accents, stronger borders, and visible depth.
- Grouped the sidebar into a version block, bordered conversion settings, and
  an expandable profile-coverage section.
- Grouped upload, result review, mapping preview, and downloads into cards with
  prominent numbered step badges.
- Added short descriptions to product identity, JSON-LD, and mapping previews.
- Added a dedicated success, warning, or error summary card after conversion.
- Arranged downloads as four individually labelled cards in a two-column grid
  on wider screens.
- Made primary, secondary, and download actions consistently full-width.
- Strengthened primary and download button styling while retaining visible
  focus, reduced-motion support, and narrow-screen padding.
- Added a native spinner during conversion.
- Updated the visible app version from `v0.3.0-dev` to `v0.5.0`.

## What was intentionally not changed

- Converter, mapping, validation, CLI, and reporting logic.
- Mapping YAML files and generated JSON-LD structure.
- Session-state keys, rerun behavior, result persistence, or reset behavior.
- Mapping-profile options or their default selection.
- Download count, contents, filenames, or formats.
- Production dependencies.

## Manual review checklist

- [ ] Compact blue hero and right-side conversion pipeline are visible.
- [ ] Three workflow overview cards appear above Step 1.
- [ ] Version shows `v0.5.0` in both the hero and sidebar.
- [ ] Step 1 has a styled upload dropzone and polished empty state.
- [ ] Sidebar version, conversion settings, and supported groups are visibly
  separated and coverage appears as compact badges.
- [ ] Keyboard focus is visible on convert, download, and reset actions.
- [ ] Success or validation status appears in a distinct status card.
- [ ] Product identity is shown as a dedicated card.
- [ ] JSON-LD and mapping previews are labelled and expandable.
- [ ] Four downloads appear as labelled cards in a two-column grid after
  conversion.
- [ ] Hero, workflow cards, and download grid stack cleanly at a narrow width.
- [ ] Results remain visible after reruns and download interactions.
- [ ] Changing the mapping profile clears stale results.

## Manual screenshot

No screenshot tooling is required. With the app open, capture one desktop image
after conversion that includes the compact hero and pipeline, workflow row,
Step 2 status, and Step 3 download grid. Capture a second image with the browser
narrowed to approximately 390 CSS pixels to confirm that the hero, workflow
cards, and columns stack while controls remain usable.

## Known limitations

- Streamlit controls retain framework-defined markup and some theme behavior.
- The CSS uses stable Streamlit `data-testid` hooks for the main container,
  sidebar, and bordered containers; these should be rechecked after major
  Streamlit upgrades.
- Automated tests verify behavior, not pixel-level presentation.
- A human visual review is still required across common browser widths and
  operating-system font rendering.
