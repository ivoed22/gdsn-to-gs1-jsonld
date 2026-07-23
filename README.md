# GDSN to GS1 JSON-LD

Convert GDSN-like product XML into GS1 Web Vocabulary JSON-LD through a
configurable YAML mapping and a typed canonical product model.

Version 0.38.1 keeps the fully embedded reviewer output clean: converted
candidate evidence nodes are omitted there, while the review-safe output keeps
the complete `schema:additionalProperty` evidence.

Version 0.38.0 presents two explicit JSON-LD variants after conversion: the
review-safe evidence model and a fully embedded experimental reviewer model
that directly asserts every displayed 60%+ candidate for removal or promotion.

Version 0.37.0 added the structured review profile v0.5 for supplier/contact,
target-market, origin, packaging, weight, product naming and image metadata.
Remaining AI candidates are included in online JSON-LD as removable
`schema:PropertyValue` review evidence, never as asserted GS1 predicates.

Version 0.36.0 combined four independent AI mapping reviews into a traceable
consensus layer. Upload-specific candidates now show agreement and conflict
signals without automatically changing the JSON-LD output. Version 0.35.1 added
upload-specific mapping assistance for populated fields
outside the active mapping. A committed catalog contains 288 heuristic
GDSN-to-WebVoc candidates scoring 60% or higher. Matches are shown in the UI
and included in the lossless unmapped JSON report, with 60–<90% explicitly
labelled for review. They are never silently emitted into JSON-LD. Candidate
knowledge is deliberately separate from an executable mapping profile: a new
profile is only needed after mappings have been semantically reviewed and
accepted. See `docs/releases/v0.38.0.md`.

Version 0.35.0 completes the end-product build path (v0.30.0–v0.35.0):
reviewer artifacts — hard-mapping sign-offs, SDR annotations, candidate
reports — can now be saved to and loaded from a git-ignored local
`workspace/` directory, surviving across sessions. Working artifacts
only; governed files are structurally unreachable. See
`docs/releases/v0.35.0.md`.

Version 0.34.0 adds a "GS1 Digital Link" panel to Convert and the HTML
product report: the Digital Link URI form for the GTIN plus a locally
rendered QR code, constructed fully offline — explicitly without
checking or claiming that the link is registered, resolvable, or live.
See `docs/releases/v0.34.0.md`.

Version 0.33.0 overhauls the interaction layer within Streamlit:
candidate filters behind progressive disclosure, SDR annotations as a
data-editor grid, column-configured tables, a dark-mode token set for
the custom CSS layer, and the `use_container_width` deprecation sweep.
No behavior changes. See `docs/releases/v0.33.0.md`.

Version 0.32.0 connects the story: "Continue to Product Passport" carries
a converted product straight into the passport builder (same parser as an
uploaded file — no validation bypass), and every conversion now offers a
self-contained, printable HTML product report (identity + readiness +
evidence + JSON-LD, fully offline, governance negations in the footer) as
a 5th download. See `docs/releases/v0.32.0.md`.

Version 0.31.0 adds a per-product "DPP readiness" scorecard to Convert:
deterministic traceability & structural signals (validation, mapping
coverage, codelist conformance) with an honest not-yet-assessed
DPP-relevance dimension pending the Crosswalk — no invented score, no
compliance claim. See `docs/releases/v0.31.0.md`.

Version 0.30.0 consolidates nine workflows into five (Convert, Explore,
Create JSON-LD Prototype, Mapping Governance, Product Passport) with
direct navigation and a lighter landing page — the first version of the
approved end-product build path toward "from GDSN message to Digital
Product Passport, traceable at every step". Behavior-preserving; see
`docs/releases/v0.30.0.md`. The Crosswalk track (now v0.36.0+) remains
blocked on CIRPASS/sector-vocabulary sourcing.

Version 0.29.0 adds the smallest useful slice of the future "Standards-
review workflow": Standards Review can record a proposed reviewer,
decision date, and target status per open SDR and download the
annotation, without applying any status transition or writing to the
governed backlog JSON. See `docs/releases/v0.29.0.md`.

Version 0.28.0 lets Generate Mapping Candidates load a previously
generated candidate report (from this workflow's own download, or the
CLI's `--full-scope` sweep) instead of re-running the ~7-minute scan.
Course-corrected after investigation found `--full-scope` isn't actually
a separate, more-expensive code path from the UI's existing "All
properties" option — both call the same function. See
`docs/releases/v0.28.0.md`.

Version 0.27.0 adds a "Workbench status" panel to the landing page — the
first of three "bigger scope" versions in this batch: six at-a-glance
metrics (WebVoc coverage, registry accepted count, open SDRs, codelists
imported, builder fields authored, session hard-mapping reviews), each
read from an existing workflow's own data source. No new data or
computation. See `docs/releases/v0.27.0.md`.

Version 0.26.0 adds a cross-workflow deep link — the last of five "quick
win" versions in this batch: Generate Mapping Candidates' candidate detail
gains a "View in Explorer" button that jumps straight to that WebVoc
property's Explorer detail view (filters reset, search and selection
pre-filled), instead of requiring a manual re-search. Pure session-state
wiring via a new `workflow_shared.navigate_to_webvoc_property` callback —
no new data or computation.

Version 0.25.0 removes the last hand-edit-JSON-externally step from the
Mapping Candidates workflow: a new "Author hard-mapping review sign-off"
section lets a reviewer set a Reviewer/Date/Decision/Notes per
hard-mapping-lane candidate and download a sign-off file matching
`load_reviewed_hard_mappings`' schema exactly, via a new
`mapping_promotion.build_hard_mapping_signoff` helper. Convenience only —
promotion logic, the sign-off schema, and governed files are untouched.

Version 0.24.0 surfaces the previously CLI-only `check-webvoc-updates`
capability in the UI, but strictly offline: Standards Review gains a
"Vocabulary freshness check" section where a reviewer uploads a candidate
`gs1Voc.jsonld` and sees new/removed/changed terms against the pinned
local snapshot. The new `compare_webvoc_snapshot_bytes` function has no
network code path at all — the existing CLI command's optional live fetch
is unchanged and stays a separate, explicit CLI operation.

Version 0.23.0 lets the Manual JSON-LD Builder's `gs1:allergenType` field
switch from its hand-curated 14-value EU subset to the full 385 values the
local Web Vocabulary snapshot defines for `AllergenTypeCode`, via a "show
full code list" checkbox (default view unchanged). The mechanism is
generic (`webvoc_explorer.group_individuals_by_class`, keyed off each
property's own WebVoc range class), so it applies to any current/future
`code` field with a smaller curated subset. See `docs/releases/v0.23.0.md`
for what else was checked (and found not to need a change).

Version 0.22.0 extends v0.21.0's codelist validation to the Bulk ZIP
workflow: the same "Open codelist validation (Track D)" panel now
appears after a batch conversion, aggregating status counts across every
file and listing which files had a non-valid entry. `convert_batch_zip`
gains the same fully opt-in `codelist_registry` parameter as
`convert_xml_to_jsonld`; no converter/batch behavior change, no new
download.

Version 0.21.0 wires v0.20.0's codelist validation into the UI: the
Convert GDSN XML workflow shows a read-only "Open codelist validation
(Track D)" panel (status counts, table, per-entry detail with a status
badge) inside the existing Review-mapping step. No converter behavior
change; still exactly 4 downloads.

Version 0.20.0 unblocks Track D: the user provided the official public GDSN
and Shared Common Code Lists workbook (595 codelists, 14,564 values),
imported via new `codelist_importer.py` into a committed, deterministic
registry. New `codelist_registry.py` validates a code value as
valid/unknown/deprecated/missing/source_unavailable against a curated,
independently verified field-to-codelist table (not the mapping catalog's
`code_list` column, which has pre-existing data-entry inconsistencies).
`convert_xml_to_jsonld` gains a fully opt-in `codelist_registry` parameter
— not passing it is byte-identical to every prior version; passing one only
adds a new diagnostic `codelist_validation` list, never blocking
conversion.

Version 0.19.0 adds a read-only "Builder Manifest Expansion Analysis"
workflow (Track C): classifies the 371 WebVoc properties not yet authorable
in the Manual Builder manifest into `ready_now` / `needs_codelist_curation`
/ `needs_hard_mapping_review` / `not_ready_no_evidence`, using the mapping
registry's governance catalog and Track B's hard-mapping detection. DPP
relevance is reported as not-yet-assessed for every candidate — that
judgment is the Crosswalk's job (now v0.30.0+). No automatic manifest
expansion; the builder manifest is unchanged.

Version 0.18.0 adds navigation and status aids to the Manual JSON-LD
Prototype Builder (183 fields / 19 groups): a coverage overview across
groups, per-field status chips (filled/missing/review-required/
hard-mapping-review/codelist-pending/blocked, via new
`builder_status.py`), search/filter, evidence expanders, and a clearer
export area. Also fixes a real defect: controlled-vocabulary (`code`)
fields were silently showing only "— none —" instead of their real
manifest-defined options. Serializer/validator/state model unchanged.

Version 0.17.0 adds a browser-based visual smoke test
(`scripts/visual_smoke.py`, Playwright + Chromium): boots the app headless,
walks the landing page and all seven workflows, and asserts no viewport
overflow, readable active buttons, visible warnings, and no compliance
claims without negation — catching the CSS/layout regressions the
AppTest-based test suite can't see. No app behavior changes; new `visual`
optional dependency group; non-blocking CI job while it stabilizes.

Version 0.16.0 extends the Mapping Candidate Generator with full-scope
scoring and review lanes: every candidate now carries a deterministic
`hard_mapping` flag (cross-references reaching outside the current product
message — organization/party, country, or cross-item product references)
and a `review_lane`. Both lanes reach the same `accepted` terminal status —
hard-mapping candidates just need a dedicated extra review sign-off first,
never a permanent block. `--full-scope` scores all 553 WebVoc properties
against the full ~6,067-attribute GDSN reference (~7 minutes; local/offline,
not part of CI). Still fully review-only: nothing writes mapping YAML, the
registry, or the catalog.

Version 0.15.0 consolidates the mapping foundation: one authoritative
artifact, `mapping/mapping_registry.yaml`, merges the executable mapping
profile with the governance review catalog (per-field governance blocks +
a full catalog review list). The three older profiles are archived — kept on
disk, selectable only for reference/comparison behind a warning. Converter
output is unchanged and test-proven byte-identical. New policy test suites
enforce that no compliance claims and no DPP Keystone (dppk) terms ever
appear in generated or recommended output.

Version 0.14.0 splits `app/streamlit_app.py` (2,500 lines) into
`app/workflow_shared.py` plus one `app/workflows/*.py` module per workflow
behind a thin router. Strictly no user-facing behavior change: converter,
mapping YAML, catalog, and WebVoc snapshots are untouched, and all 197 tests
(including AppTest navigation) stay green.

Version 0.13.5 is release-hygiene and developer-environment maintenance: it
adopts a tag-per-meaningful-change release cadence (with an `## Unreleased`
CHANGELOG section and a documented "Release process"), re-sequences the roadmap
foundation-first, and routes pytest's temp directory to a git-ignored repo-local
path so local test runs are clean (`197 passed`). No user-facing behavior
changes; converter, mapping YAML, catalog, and WebVoc snapshots are untouched.

Version 0.13.4 bundles workspace UI fixes (wider workspace, equal-size cards,
readable active button) with a large expansion of the Manual JSON-LD Prototype
Builder — from ~40 to 183 fields across 19 groups, including nested objects,
controlled-code dropdowns, and full nutrition, all sourced from the local Web
Vocabulary snapshot. UI/config and the manual Builder serializer only; the
converter, mapping YAML, catalog, and WebVoc snapshots are unchanged, and manual
output stays prototype (not BMS/XPath traceable).

Version 0.13.3 adds guided route navigation: the landing page starts with three
primary routes — Create GS1 JSON-LD, Vocabulary & Mapping, and the Product
Passport Bridge — and reveals only the child workflows for the chosen route
(progressive disclosure). Convert GDSN XML remains the default. All seven
workflows stay reachable; no behaviour changes, no mock data, no compliance
claims.

Version 0.13.2 is a UI/UX polish release: a wider main workspace, a sidebar
reframed as compact workspace status/context, themed landing navigation
(Recommended path → Vocabulary & Mapping → JSON-LD Prototyping → Product
Passport Bridge) with Convert as the recommended start, shorter card copy, and a
labelled core-conversion traceability rail. No behaviour changes, no mock data,
no fabricated coverage or compliance claims; all seven workflows remain
reachable and every governance warning is preserved.

Version 0.13.1 presents the Convert GDSN XML (Single XML) path as a guided
four-step flow — Upload → Mapping → Validate → Export — wired to the real
converter. No new features, no mock data, no fabricated coverage or compliance
claims; all seven workflows remain reachable and every governance warning is
preserved.

Version 0.13.0 adds the Product Passport Builder in minimal-schema prototype
mode: it wraps GS1 Web Vocabulary JSON-LD (from the converter, the Manual
JSON-LD Prototype Builder, or pasted/uploaded input) into a prototype Product
Passport JSON-LD envelope and validates it against the built-in minimal schema.
Prototype/reference only; structural validation only; not official GS1
validation, not EU DPP regulatory compliance, and not production-ready.

Version 0.12.1 hardens the Product Passport Bridge: `jsonschema` is now an
explicit dependency (with a clearly-flagged fallback), the source manifest is
enforced against its JSON Schema, the workflow narrative covers all six
workflows, placeholder schemas are no longer offered as selectable validation
targets, structural-check wording avoids implying compliance, and CI runs
`compileall` plus a CLI smoke matrix. Prototype/reference only; no official GS1
validation or production compliance is claimed.

Version 0.12.0 adds the Product Passport Bridge — a prototype/reference
workflow that inventories public Digital Product Passport (DPP) reference
sources and validates prototype Product Passport JSON against local JSON
Schemas. Prototype/reference only; no official GS1 validation or production
compliance is claimed.

Version 0.11.0 added a Mapping Candidate Generator — a deterministic,
offline tool that proposes possible GDSN/BMS/XPath source fields for GS1
Web Vocabulary properties with confidence scoring and review reasons.
Candidates are review support only; no mappings are automatically accepted
or written.

Version 0.10.0 added a Manual JSON-LD Prototype Builder for authoring
range-aware GS1 Web Vocabulary product markup by hand.

## Mapping profiles

- `mapping/mapping_mvp.yaml`: v0.1.0 product identity and presentation fields
- `mapping/mapping_v0_2.yaml`: v0.1.0 fields plus ingredients, allergens, and
  nutrients
- `mapping/mapping_v0_3.yaml`: v0.2.0 fields plus certifications and
  DPP/certification document links

## MVP outputs

Each CLI conversion creates:

- `product_{GTIN}.jsonld`
- `mapping_report_{GTIN}.xlsx`
- `validation_report_{GTIN}.json`
- `unmapped_fields_{GTIN}.json`

When GTIN is unavailable, filenames use `unknown`.

## Installation

Python 3.11 or newer is required.

```bash
python -m venv .venv
python -m pip install -e ".[dev,app]"
```

For Streamlit Community Cloud, `requirements.txt` contains all runtime
dependencies and the app adds `src/` to its import path.

## CLI

```bash
gdsn-to-gs1-jsonld convert examples/input/example_product.xml \
  --mapping mapping/mapping_v0_3.yaml \
  --output output_v0_3/
```

You can also run the module directly:

```bash
python -m gdsn_to_gs1_jsonld.cli convert examples/input/example_product.xml \
  --mapping mapping/mapping_v0_3.yaml \
  --output output_v0_3/
```

Convert all XML files in the synthetic sample corpus:

```bash
gdsn-to-gs1-jsonld convert-samples \
  --input-dir examples/input/samples \
  --mapping mapping/mapping_v0_3.yaml \
  --output-dir examples/output/samples
```

The command creates per-product conversion reports plus
`sample_conversion_summary.json` and `sample_conversion_summary.xlsx`.
Failures identify the sample, processing stage, and exception message.

Convert XML files from a ZIP batch:

```bash
gdsn-to-gs1-jsonld convert-batch \
  --input-zip path/to/input.zip \
  --mapping mapping/mapping_v0_3.yaml \
  --output-dir batch_output/ \
  --max-files 100 \
  --max-file-size-mb 10 \
  --max-total-size-mb 100
```

The command ignores non-XML files, rejects unsafe ZIP paths, converts XML files
independently, and writes `batch_summary.json`, `batch_summary.xlsx`, and
`batch_export.zip`. See
[bulk XML batch conversion](docs/bulk-xml-batch-conversion.md).

Validate the mapping catalog:

```bash
gdsn-to-gs1-jsonld check-catalog \
  --catalog mapping_catalog/gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_3_webvoc_validated.csv
```

Compare an executable YAML profile with the catalog and create reports:

```bash
gdsn-to-gs1-jsonld check-mapping \
  --mapping mapping/mapping_v0_3.yaml \
  --catalog mapping_catalog/gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_3_webvoc_validated.csv \
  --output mapping_quality_report/
```

Warnings are non-failing by default. Add `--strict` to either quality command
to make warnings produce exit code 1.

Check the committed Web Vocabulary snapshot without network access:

```bash
gdsn-to-gs1-jsonld check-webvoc-updates \
  --snapshot-dir webvoc/current \
  --output webvoc_update_report/ \
  --no-network
```

Revalidate the mapping catalog against that snapshot:

```bash
gdsn-to-gs1-jsonld revalidate-mapping-catalog \
  --catalog mapping_catalog/gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_3_webvoc_validated.csv \
  --webvoc-dir webvoc/current \
  --output mapping_catalog_revalidation/
```

Normal conversion never fetches external vocabulary resources. See the
[Web Vocabulary update monitor](docs/webvoc-update-monitor.md) for controlled
online comparison and snapshot refresh.

Export the maintained standards-review backlog without network access:

```bash
gdsn-to-gs1-jsonld export-standards-backlog \
  --warning-review docs/warning-cleanup-v0.6.1.md \
  --output docs/standards-decisions/ \
  --format all
```

The command refreshes JSON and CSV backlog files. Detailed
[standards decision records](docs/standards-decisions/index.md) remain
human-maintained review documents.

Export the read-only Web Vocabulary Explorer dataset:

```bash
gdsn-to-gs1-jsonld export-webvoc-explorer \
  --webvoc webvoc/current/gs1Voc.jsonld \
  --catalog mapping_catalog/gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_3_webvoc_validated.csv \
  --backlog docs/standards-decisions/standards_review_backlog.json \
  --output-dir webvoc_explorer_output/
```

The command writes property JSON/CSV and summary JSON/XLSX files without
network access. See the [Web Vocabulary Explorer](docs/webvoc-explorer.md).

Import public reference source data into normalized offline JSON and CSV:

```bash
gdsn-to-gs1-jsonld import-reference-data \
  --gdsn-xlsx reference_data/raw_public/GDSN_Attributes_with_BMSId_xPath_3.1.36_June_5_2026.xlsx \
  --webvoc webvoc/current/gs1Voc.jsonld \
  --source-manifest reference_data/source_manifest.json \
  --output-dir reference_data/normalized/
```

The command checks manifest hashes and writes normalized GDSN/WebVoc reference
data plus `source_data_summary.json`. See the
[source data inventory](docs/source-data-inventory.md) and
[reference data import](docs/reference-data-import.md) notes.

Generate mapping candidates for GS1 Web Vocabulary properties:

```bash
gdsn-to-gs1-jsonld generate-mapping-candidates \
  --webvoc-properties reference_data/normalized/webvoc_properties_1_17.csv \
  --gdsn-reference reference_data/normalized/gdsn_attributes_bms_xpath_3_1_36.csv \
  --catalog mapping_catalog/gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_3_webvoc_validated.csv \
  --mapping mapping/mapping_v0_3.yaml \
  --standards-backlog docs/standards-decisions/standards_review_backlog.json \
  --output-dir mapping_candidate_reports/
```

Candidates are review support only; no mappings are accepted or written.
See [Mapping Candidate Generator](docs/mapping-candidate-generator.md).

Inventory Product Passport reference sources (prototype/reference only):

```bash
gdsn-to-gs1-jsonld inventory-product-passport-sources \
  --manifest product_passport/reference_sources/source_manifest.json \
  --output-dir product_passport/reference_sources/normalized/
```

Validate a prototype Product Passport JSON against a local schema (structural
validation only; no official GS1 validation or production compliance):

```bash
gdsn-to-gs1-jsonld validate-product-passport \
  --input product_passport/examples/minimal_product_passport.json \
  --schema product_passport/reference_sources/raw_public/schemas/dpp_minimal.schema.json \
  --output-dir product_passport/validation_reports/
```

See [Product Passport Bridge](docs/product-passport-bridge.md).

## Streamlit

```bash
streamlit run app/streamlit_app.py
```

The app defaults to Certifications & Documents v0.3.0 and can switch to the
Food v0.2.0 or MVP v0.1.0 profiles. It now starts with six workflow modes:

- `Convert GDSN XML`, with `Single XML` and `Bulk ZIP` tabs
- `Explore GS1 Web Vocabulary`, a read-only local vocabulary and coverage
  explorer
- `Create JSON-LD Prototype`, a manual Web Vocabulary markup form with live
  JSON-LD preview
- `Standards Review`, a compact read-only view of open SDR/backlog status
- `Generate Mapping Candidates`, a review-only candidate report pairing WebVoc
  properties with GDSN/BMS/XPath source fields (no mappings are accepted or
  written)
- `Validate Product Passport Sources` (marker: PP), a prototype/reference
  workflow for inventorying DPP reference sources and structural schema
  validation (no official GS1 validation or production compliance claimed)

## Mapping

Mapping YAML is the executable converter configuration. The catalog under
`mapping_catalog/` is the BMS/XPath and vocabulary traceability layer. Version
0.3.0 uses GDSN 3.1.36 catalog rows and locally validated Web Vocabulary terms
as design inputs. Version 0.4.0 checks catalog governance and YAML/catalog
alignment without generating YAML or changing converter output.

## Sample testing

The files under `examples/input/samples/` are synthetic and contain no real
company data. Place private real-world GDSN XML files in a separate local
directory and point `convert-samples` at that directory. Review the validation
and unmapped reports before sharing outputs because source XML may contain
confidential data.

The converter does not perform full GDSN XSD validation. Unmapped fields show
which populated XML elements were outside the selected profile; they do not
prove that the source XML is invalid.

## Strategic relevance

This project demonstrates a practical bridge from GS1 product data exchange to
machine-readable structured data using GDSN, BMS/XPath, and GS1 Web
Vocabulary.

- [Internal positioning](docs/internal-positioning.md)
- [Open governance questions](docs/open-governance-questions.md)
- [Web Vocabulary conformance review](docs/web-vocabulary-conformance-review.md)
- [Web Vocabulary Explorer](docs/webvoc-explorer.md)
- [Manual JSON-LD Prototype Builder](docs/manual-jsonld-builder.md)
- [Public source data inventory](docs/source-data-inventory.md)
- [Reference data import](docs/reference-data-import.md)
- [Standards decision register](docs/standards-decisions/index.md)
- [Strategic next steps](docs/strategic-next-steps.md)
- [Product Passport Bridge](docs/product-passport-bridge.md)

## For GS1 stakeholders

These concise documents explain the demonstration, its practical output, and
its relevance to standards, AI, and machine-readable product data:

- [Stakeholder one-pager](docs/stakeholder-one-pager.md)
- [Five-minute demo story and speaker notes](docs/demo-story.md)
- [Before and after example](docs/before-after-example.md)
- [Why this matters for AI](docs/ai-relevance.md)

## Development

```bash
python -m pytest
```

See [`docs/`](docs/index.md) for architecture, mapping, output, app, and roadmap
notes.

## Roadmap

Later releases may accept or defer registered standards decisions, add manual
JSON-LD authoring linked to mapping evidence, broaden food coverage, add
certification verification, validation profiles, and production batch
operations beyond the current ZIP upload workflow.

## Disclaimer

This is an experimental converter. Generic DPP/document links require
standards review. No certificate verification, URL dereferencing, full GDSN
coverage, or full GDSN XSD validation is provided.
