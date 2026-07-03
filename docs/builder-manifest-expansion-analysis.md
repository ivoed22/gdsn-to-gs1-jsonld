# Builder Manifest Expansion Analysis (Track C, v0.19.0)

## Purpose

The Manual JSON-LD Prototype Builder manifest authors 183 of the 553 GS1 Web
Vocabulary properties. This analysis answers, for the other 371: **which are
mature enough to add next, and why** — without ever touching the manifest
itself. Adding a field remains a separate, deliberate decision a human
makes after reviewing this output.

It is read-only review support, in the same spirit as the Mapping Candidate
Generator (v0.11.0) and Track B's promotion lanes (v0.16.0): score/classify,
export a proposal, change nothing automatically.

## Inputs

- `reference_data/normalized/webvoc_properties_1_17.csv` — the full 553
  WebVoc properties.
- `builder_manifest/product_builder_v0_10.yaml` — which property ids are
  already authorable (183).
- `mapping/mapping_registry.yaml` — the consolidated governance catalog
  (v0.15.0), keyed by `jsonld_property`, for evidence of a governed GDSN
  mapping.
- `reference_data/normalized/gdsn_attributes_bms_xpath_3_1_36.csv` — for
  hard-mapping detection via the exact same
  `detect_hard_mapping` rules the Mapping Candidate Generator uses (v0.16.0
  Track B), applied to whichever GDSN attribute is cited as evidence.

## Readiness phases (fixed vocabulary)

| Phase | Meaning |
|---|---|
| `ready_now` | Has governed mapping evidence; not hard-mapping; not controlled-vocabulary shaped. |
| `needs_codelist_curation` | Has evidence, but the property looks controlled-vocabulary shaped (same code-list heuristic the Mapping Candidate Generator uses) — manifest `options` would need curating first, the same work existing `code`-type builder fields already require. |
| `needs_hard_mapping_review` | Has evidence, but that evidence's GDSN attribute is a Track B hard mapping (a cross-reference reaching outside the current product message) and needs the same dedicated review as any other hard mapping before being trusted. |
| `not_ready_no_evidence` | No governed mapping evidence at all. Nothing here invents evidence to promote a property regardless of how useful it might be. |

On the current committed reference data: 5 `ready_now`, 0
`needs_codelist_curation`, 0 `needs_hard_mapping_review`, 366
`not_ready_no_evidence`. The small `ready_now` count directly reflects how
small the governed mapping registry still is (28 accepted GDSN attributes) —
this analysis does not manufacture readiness beyond what's actually
governed.

## DPP relevance is never assessed here

Every candidate reports `dpp_relevance: "not_yet_assessed_pending_crosswalk"`.
Judging whether a property matters for a Digital Product Passport is the
GS1-first DPP Crosswalk's job (v0.20.0+, not built yet — see
`docs/roadmap.md`). Reporting anything else here would be exactly the kind
of invented data this project does not produce.

## CLI usage

```bash
gdsn-to-gs1-jsonld analyze-builder-expansion \
  --webvoc-properties reference_data/normalized/webvoc_properties_1_17.csv \
  --builder-manifest builder_manifest/product_builder_v0_10.yaml \
  --mapping-registry mapping/mapping_registry.yaml \
  --gdsn-reference reference_data/normalized/gdsn_attributes_bms_xpath_3_1_36.csv \
  --output-dir builder_expansion_reports/
```

Writes `builder_manifest_expansion_analysis.json`: summary counts plus one
entry per not-yet-authorable property (WebVoc term id, label, range, source
mapping status, codelist/hard-mapping dependency flags and reasons, DPP
relevance marker, readiness phase, reason).

## Streamlit workflow

"Builder Manifest Expansion Analysis" (marker: EXP) lives under the
**Vocabulary & Mapping** route, alongside Explore, Generate Mapping
Candidates, and Standards Review — it's a review/governance tool, not an
authoring one. It shows:

1. A coverage summary (authored / total / not-yet-authorable, plus counts
   per readiness phase).
2. A readiness-phase filter (defaults to `ready_now`).
3. A candidate table and per-candidate detail (status badge, reason,
   hard-mapping reasons where applicable, source mapping status).
4. A JSON download of the full analysis.

There is no "add to manifest" button anywhere in this workflow.

## What it does NOT do

- Does NOT modify the builder manifest, mapping registry, mapping catalog,
  or Web Vocabulary snapshots.
- Does NOT assess or claim DPP relevance for any property.
- Does NOT enforce or validate codelists — `codelist_dependency` is a
  heuristic flag about authoring effort, not a validation result.
- Does NOT claim official GS1 validation or production compliance.
- Does NOT promote a hard-mapping-flagged property's evidence as
  trustworthy — it is explicitly routed to `needs_hard_mapping_review`.
