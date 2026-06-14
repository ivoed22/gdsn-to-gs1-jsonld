# SDR-003 — Image Representation

## Status

Open

GitHub issue: [#5](https://github.com/ivoed22/gdsn-to-gs1-jsonld/issues/5)

## Summary

`gs1:productImage` is not found in the local Web Vocabulary snapshot, while
the source image selection also depends on GDSN referenced-file filtering.

## Affected mappings

| Field | Current target | Current status | Warning category | Blocks release? |
| ----- | -------------- | -------------- | ---------------- | --------------- |
| `product_image_url` | `gs1:productImage` | Candidate needing review | `image_modelling` | No |

## Current behaviour

The converter selects `PRODUCT_IMAGE` referenced-file URLs and emits them as
`gs1:productImage`.

## Why this needs review

A technically valid URL does not establish the right target property. The
choice must cover image role, multiplicity, preferred image semantics, and the
relationship between Web Vocabulary and Digital Link.

## Options

### Option A — Keep the experimental GS1 property

- Description: retain current output with an explicit warning.
- Advantages: backward compatible.
- Disadvantages: target term is not validated.
- Converter output: unchanged.
- Web Vocabulary conformance: not established.
- GDSN traceability: unchanged.
- Governance: experimental use must remain visible.

### Option B — Use `schema:image`

- Description: adopt the established Schema.org fallback.
- Advantages: broadly understood web property.
- Disadvantages: output is explicitly mixed-vocabulary.
- Converter output: property change.
- Web Vocabulary conformance: no longer claimed for this field.
- GDSN traceability: unchanged.
- Governance: needs an external-vocabulary policy.

### Option C — Use a governed GS1 link relation

- Description: express image resources through an approved relation.
- Advantages: web-native and potentially role-aware.
- Disadvantages: requires relation selection and linked-resource rules.
- Converter output: structural change.
- Web Vocabulary conformance: depends on approved relation.
- GDSN traceability: retained in mapping evidence.
- Governance: needs Digital Link/Web Vocabulary coordination.

## Recommended direction

Review Option B as the conservative fallback and Option C as the strategic
target. Do not change the released mapping before image roles and compatibility
are agreed.

## Decision needed from

- GS1 Web Vocabulary owner
- GS1 Digital Link owner
- GDSN/GSMP group

## Follow-up actions

- Confirm official image-related vocabulary and linktypes.
- Validate `PRODUCT_IMAGE` code filtering.
- Define preferred/multiple image behavior.

## Links

- [v0.6.1 warning cleanup](../warning-cleanup-v0.6.1.md)
- [Web Vocabulary conformance review](../web-vocabulary-conformance-review.md)
- [Web Vocabulary update monitor](../webvoc-update-monitor.md)
- `mapping_quality_report/mapping_quality_report.json`
