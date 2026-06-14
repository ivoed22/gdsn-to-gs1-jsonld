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

- [ ] Blue header/hero is immediately visible at the top of the app.
- [ ] Version shows `v0.5.0` in both the hero and sidebar.
- [ ] Step 1 appears as a white card with a blue top edge and numbered badge.
- [ ] Sidebar version, conversion settings, and supported groups are visibly
  separated.
- [ ] Keyboard focus is visible on convert, download, and reset actions.
- [ ] Success or validation status appears in a distinct status card.
- [ ] JSON-LD and mapping previews are comfortable to scan.
- [ ] Four downloads appear as labelled cards in a two-column grid after
  conversion.
- [ ] Hero, cards, and download grid remain usable at a mobile/narrow width.
- [ ] Results remain visible after reruns and download interactions.
- [ ] Changing the mapping profile clears stale results.

## Manual screenshot

No screenshot tooling is required. With the app open, capture one desktop image
after conversion that includes the hero, Step 2 status, and Step 3 download
grid. Capture a second image with the browser narrowed to approximately 390 CSS
pixels to confirm that columns stack and controls remain usable.

## Known limitations

- Streamlit controls retain framework-defined markup and some theme behavior.
- The CSS uses stable Streamlit `data-testid` hooks for the main container,
  sidebar, and bordered containers; these should be rechecked after major
  Streamlit upgrades.
- Automated tests verify behavior, not pixel-level presentation.
- A human visual review is still required across common browser widths and
  operating-system font rendering.
