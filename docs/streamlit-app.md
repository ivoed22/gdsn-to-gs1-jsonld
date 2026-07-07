# Streamlit app

Start the app with:

```bash
streamlit run app/streamlit_app.py
```

Since v0.30.0 the app has five directly navigable workflows (landing page:
hero → workbench status → "Choose a workflow" cards):

- `Convert GDSN XML` — Single XML and Bulk ZIP tabs. A "Mapping profile"
  expander selects the consolidated registry (default) or an archived
  profile for reference/comparison; switching clears previous results.
- `Explore GS1 Web Vocabulary` — read-only vocabulary/coverage explorer.
- `Create JSON-LD Prototype` — the manual builder, with the Builder
  Manifest Expansion Analysis (Track C) as a second tab.
- `Mapping Governance` — Generate Mapping Candidates and Standards Review
  (SDR annotations, vocabulary freshness) as tabs in one review lifecycle.
- `Product Passport` — source inventory/structural validation and the
  prototype Passport Builder as tabs.

The sidebar shows the app version, workspace status, source snapshots, and
one governance block. Uploaded XML bytes are passed directly to the package
and are not intentionally written to disk. The Bulk ZIP tab ignores non-XML
files and uses the shared batch converter to produce `batch_summary.json`,
`batch_summary.xlsx`, and a batch export ZIP.

**v0.21.0**: Single XML conversion's "Review mapping & evidence" step gained
an "Open codelist validation (Track D)" expander showing per-field
valid/unknown/deprecated/missing/source_unavailable status against the
v0.20.0 codelist registry. Diagnostic only — it never blocks conversion and
adds no new download. See `docs/codelist-registry.md`.

**v0.22.0**: The Bulk ZIP workflow gained the same codelist validation
expander, aggregated across the whole batch: five status metrics summed
over every file, plus a table of files that had at least one non-valid
codelist entry. Diagnostic only — never blocks a file or changes the
export ZIP.

**v0.27.0**: The landing page (shown before any workflow is opened) gains
a "Workbench status" panel with six at-a-glance metrics — WebVoc
coverage, registry accepted count, open SDRs, codelists imported, builder
fields authored, and hard-mapping reviews recorded this session. Every
number is read from an existing workflow's own data source; see
`docs/releases/v0.27.0.md`.

**v0.30.0**: Nine workflows consolidated into the five above; two-stage
route→child navigation replaced by direct workflow cards; landing page
reduced to hero + workbench status + navigation; mapping-profile
selection moved from the sidebar into Convert. Behavior-preserving; see
`docs/releases/v0.30.0.md`.

**v0.31.0**: Convert (Single XML) step 3 gains a "DPP readiness"
scorecard — traceability & structural signals from the conversion
(structural validation, mapping coverage, codelist conformance) plus an
honest not-yet-assessed DPP-relevance dimension pending the Crosswalk.
No numeric score is invented and no compliance is claimed; see
`docs/releases/v0.31.0.md`.

**v0.32.0**: Convert gains a "Continue to Product Passport" bridge (the
converted JSON-LD is offered as a pre-selected input mode in the passport
builder, parsed exactly like an uploaded file) and a 5th download: a
self-contained, printable HTML product report (identity + readiness +
evidence + JSON-LD, offline, governance negations in the footer). See
`docs/releases/v0.32.0.md`.

**v0.33.0**: UI overhaul within Streamlit — candidate filters behind a
collapsed "Filters" expander, SDR annotations as a data-editor grid,
column config on the big tables, a prefers-color-scheme dark token set
for the custom CSS layer, and the `use_container_width` deprecation
sweep. No behavior changes; see `docs/releases/v0.33.0.md`.

**v0.34.0**: Convert step 3 gains a "GS1 Digital Link" panel — the URI
form for the GTIN plus a locally rendered QR code, both constructed
offline, with an explicit caveat that nothing is checked or claimed
about the link being registered, resolvable, or live. The HTML product
report embeds the same section. See `docs/releases/v0.34.0.md`.

**v0.35.0**: Reviewer artifacts (hard-mapping sign-offs, SDR review
annotations, candidate reports) can be saved to and loaded from a
git-ignored local `workspace/` directory, so they survive across
sessions. Working artifacts only — governed files are structurally
unreachable from the workspace module. See `docs/releases/v0.35.0.md`.
