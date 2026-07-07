# Visual smoke tests

## Purpose

`streamlit.testing.v1.AppTest` (used throughout `tests/test_streamlit_app.py`)
verifies widget structure and text content, but it never renders CSS or a
real browser layout. It cannot catch a broken active-button color, cards
that overflow the viewport, or a warning that's technically present but
visually hidden. `scripts/visual_smoke.py` closes that gap with a real
headless browser (Playwright + Chromium).

This is read-only browsing plus assertions — it makes no app behavior
changes.

## What it checks

Boots the app and walks the direct navigation across all five workflows
(v0.30.0 consolidation) plus the landing page, asserting on every screen:

- No horizontal overflow at a 1280px desktop viewport.
- The active workflow button is readable (text color differs from its
  background, not fully transparent).
- No positive compliance claim appears without a negation ("not official GS1
  validation", "No production compliance", etc. — same check as
  `tests/test_no_claims.py`, applied to rendered page text).
- At least one warning/info alert is visible per workflow (every workflow
  carries a governance or scope note).
- The app version and all five workflow cards are visible on the landing
  page.

It also drives one real interaction (selecting `gs1:gtin` and clicking
"Generate Candidates") so the Mapping Governance screenshot shows the
promotion-lane state, not just the empty controls form.

Each screen is captured as a full-page PNG screenshot.

## Running locally

```bash
pip install -e ".[visual]"
playwright install --with-deps chromium   # one-time browser download

python scripts/visual_smoke.py
# Screenshots land in tests/visual/baselines/ (git-ignored — see below)
```

Options: `--port <port>` (default 8577), `--output-dir <path>`.

## Why screenshots aren't committed

`tests/visual/baselines/` is git-ignored. This version captures and asserts
on live layout; it does not yet do pixel-diff comparison against a
previously committed baseline (that's a natural follow-up once this harness
has proven stable). Committing PNGs now would only bloat the repository
without buying regression detection. In CI, screenshots are uploaded as a
build artifact (`visual-smoke-screenshots`) on every run instead, so they're
inspectable without living in git history.

## CI status: non-blocking

The `visual-smoke` job runs on every push/PR with `continue-on-error: true`
— a failure is visible but does not fail the overall CI run. This is
deliberate while the harness stabilizes: headless-browser interaction with a
live Streamlit session is inherently more timing-sensitive than
`AppTest`'s in-process runner. Once a run of observation shows it's not
flaky, remove `continue-on-error` from `.github/workflows/tests.yml` to make
it a real gate.

## Extending

`SCREENS` in `scripts/visual_smoke.py` is a list of
`(workflow_index, screen_name)` tuples, matching the order of
`WORKFLOW_MODES` in `app/workflow_shared.py`. Add a tuple there for any new
workflow; no other wiring is needed unless the new screen needs a specific
interaction first (see the `mapping_governance` special case in the script
for the pattern).
