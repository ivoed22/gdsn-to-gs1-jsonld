# SDR-006 — YAML and Catalog Governance

## Status

Open

GitHub issue: [#9](https://github.com/ivoed22/gdsn-to-gs1-jsonld/issues/9)

## Summary

The catalog defines `certification_documents[]`, while executable YAML uses a
filtered generic `referenced_documents[]` object. The relationship between
these governance views is not defined.

## Affected mappings

| Field | Current target | Current status | Warning category | Blocks release? |
| ----- | -------------- | -------------- | ---------------- | --------------- |
| `certification_documents[].file_name` | `schema:name` | High-confidence catalog row, not matched to same YAML object | `yaml_catalog_mismatch` | No |
| `certification_documents[].document_url` | `schema:url` / `gs1:certificationInfo` candidate | High-confidence catalog row, not matched to same YAML object | `yaml_catalog_mismatch` | No |

## Current behaviour

YAML filters both DPP and certification files into generic referenced-document
objects. The catalog separately describes certification-document candidates.

## Why this needs review

Treating the objects as aliases could hide distinct semantics; treating them
as unrelated duplicates coverage. The project needs rules for catalog
authority, aliases, implementation scope, and intentionally unimplemented
rows.

## Options

### Option A — Declare explicit canonical aliases

- Description: govern certification documents as a typed subset of referenced documents.
- Advantages: removes duplicate implementation expectations.
- Disadvantages: alias rules add catalog complexity.
- Converter output: unchanged.
- Web Vocabulary conformance: unchanged.
- GDSN traceability: retained if aliases preserve source evidence.
- Governance: needs a formal alias mechanism.

### Option B — Implement separate YAML object mappings

- Description: create distinct certification and generic document objects.
- Advantages: mirrors catalog boundaries.
- Disadvantages: possible duplicate source records and output.
- Converter output: structural change.
- Web Vocabulary conformance: still depends on SDR-002.
- GDSN traceability: clear but duplicated unless filtering is exclusive.
- Governance: needs precedence and filtering rules.

### Option C — Mark catalog rows intentionally covered/out of scope

- Description: add explicit implementation-scope metadata without semantic changes.
- Advantages: simple quality-check interpretation.
- Disadvantages: may defer the underlying object-model decision.
- Converter output: unchanged.
- Web Vocabulary conformance: unchanged.
- GDSN traceability: unchanged.
- Governance: requires controlled status vocabulary and approval.

## Recommended direction

Define an alias/coverage policy combining Option A and Option C. Do not add a
second YAML object until SDR-002 decides whether the semantics are truly
distinct.

## Decision needed from

- Internal project owner
- Mapping catalog governance group
- GS1 Architecture group

## Follow-up actions

- Define catalog authority and implementation-coverage rules.
- Decide whether canonical aliases are permitted.
- Add an explicit status for intentionally covered rows if accepted.
- Update quality-check behavior only after the governance rule is documented.

## Links

- [v0.6.1 warning cleanup](../warning-cleanup-v0.6.1.md)
- [Web Vocabulary conformance review](../web-vocabulary-conformance-review.md)
- [Web Vocabulary update monitor](../webvoc-update-monitor.md)
- `mapping_quality_report/mapping_quality_report.json`
