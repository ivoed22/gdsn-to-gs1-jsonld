# SDR-005 — Certification Semantics

## Status

Open

## Summary

Certification extraction is traceable, but identifier, issuance-date, and
effective-start targets combine validated GS1 terms with Schema.org fallbacks
and unresolved semantic choices.

## Affected mappings

| Field | Current target | Current status | Warning category | Blocks release? |
| ----- | -------------- | -------------- | ---------------- | --------------- |
| `certifications[].certification_identification` | `schema:identifier` | Experimental semantic fallback | `yaml_catalog_mismatch` | No |
| `certifications[].certificate_issuance_date_time` | `schema:dateIssued` | Catalog coverage review | `yaml_catalog_mismatch` | No |
| `certifications[].effective_start` | `gs1:certificationStartDate` | Validated candidate among catalog choices | `webvoc_term_missing` | No |

## Current behaviour

The converter preserves non-URI certification identifiers with
`schema:identifier`, issuance timestamps with `schema:dateIssued`, and
effective-start dates with `gs1:certificationStartDate`.

## Why this needs review

Source labels do not determine whether a value is a URI, scheme value, local
identifier, or date with reduced precision. Choosing targets requires semantic
rules, not string matching.

## Options

### Option A — Retain documented fallbacks

- Description: keep current targets as explicitly experimental.
- Advantages: source values remain available and compatible.
- Disadvantages: mixed-vocabulary output and unresolved catalog alignment.
- Converter output: unchanged.
- Web Vocabulary conformance: partial.
- GDSN traceability: strong.
- Governance: requires clear fallback policy.

### Option B — Add value-shape-driven target selection

- Description: choose URI, certification value, or identifier based on governed rules.
- Advantages: more semantically precise.
- Disadvantages: transformation logic and ambiguous cases increase.
- Converter output: conditional structural/property changes.
- Web Vocabulary conformance: potentially improved.
- GDSN traceability: must record each rule application.
- Governance: requires authoritative value-shape rules.

### Option C — Define a versioned certification profile

- Description: resolve all certification terms together in a new profile.
- Advantages: coherent model and preserved historical compatibility.
- Disadvantages: broader review and migration effort.
- Converter output: changed only for the new profile.
- Web Vocabulary conformance: assessable as one package.
- GDSN traceability: retained.
- Governance: needs GS1 and project approval.

## Recommended direction

Use Option C, informed by explicit value-shape rules from Option B. Keep
current behavior until the complete certification model is accepted.

## Decision needed from

- GS1 Web Vocabulary owner
- GDSN/GSMP group
- Certification subject-matter experts
- Internal project owner

## Follow-up actions

- Define identifier/value/URI distinctions.
- Confirm issuance and effective-date semantics.
- Review issuing-organization modelling alongside this record.
- Create accepted expected-output examples.

## Links

- [v0.6.1 warning cleanup](../warning-cleanup-v0.6.1.md)
- [Web Vocabulary conformance review](../web-vocabulary-conformance-review.md)
- [Web Vocabulary update monitor](../webvoc-update-monitor.md)
- `mapping_quality_report/mapping_quality_report.json`
