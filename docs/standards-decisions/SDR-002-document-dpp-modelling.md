# SDR-002 — Document and DPP Modelling

## Status

Open

## Summary

The converter can emit document metadata, but the governed relationship from a
product to generic, certification, and DPP documents is unresolved.

## Affected mappings

| Field | Current target | Current status | Warning category | Blocks release? |
| ----- | -------------- | -------------- | ---------------- | --------------- |
| `certification_documents[].referenced_file_type` | `schema:additionalType` fallback | Candidate/experimental | `document_dpp_modelling` | No |
| `referenced_documents[].referenced_file_type` | `schema:additionalType` fallback | Candidate/experimental | `document_dpp_modelling` | No |

## Current behaviour

Filtered GDSN referenced-file information becomes a
`schema:DigitalDocument` under experimental `gs1:referencedDocument`.
File type is preserved with `schema:additionalType`.

## Why this needs review

Stable `dpp` and `certificationInfo` linktypes exist, but link relations are not
automatically equivalent to embedded JSON-LD properties. The product/document
boundary, resolver use, and file-type semantics need coordinated governance.

## Options

### Option A — Retain embedded Schema.org documents

- Description: keep the current object and external-vocabulary properties.
- Advantages: rich metadata and no resolver dependency.
- Disadvantages: experimental parent relationship remains.
- Converter output: unchanged.
- Web Vocabulary conformance: mixed-vocabulary and partial.
- GDSN traceability: strong.
- Governance: requires approval of the extension policy.

### Option B — Use GS1 Digital Link relations

- Description: represent DPP and certification links with stable linktypes.
- Advantages: web-native relationship semantics.
- Disadvantages: may lose embedded metadata or require linked resources.
- Converter output: structural change.
- Web Vocabulary conformance: relation-based, not an embedded-property claim.
- GDSN traceability: must be carried in diagnostics/catalog evidence.
- Governance: needs Digital Link and DPP review.

### Option C — Use a hybrid relation plus document object

- Description: emit a governed relation and retain a linked document resource.
- Advantages: preserves metadata and web-native navigation.
- Disadvantages: more complex identity and duplication rules.
- Converter output: additive or breaking depending on design.
- Web Vocabulary conformance: potentially clearer if terms are approved.
- GDSN traceability: strong with stable document identity.
- Governance: requires architecture rules.

## Recommended direction

Prototype Option C outside the released mapping and compare it with Option B.
Do not replace current output until link relation, object identity, and
file-type rules are accepted.

## Decision needed from

- GS1 Architecture group
- DPP/data spaces workstream
- GS1 Digital Link owner
- Internal project owner

## Follow-up actions

- Define product-to-document relationship use cases.
- Confirm `dpp` and `certificationInfo` applicability.
- Decide URI identity and embedded metadata rules.
- Review relevant GDSN referenced-file code lists.

## Links

- [v0.6.1 warning cleanup](../warning-cleanup-v0.6.1.md)
- [Web Vocabulary conformance review](../web-vocabulary-conformance-review.md)
- [Web Vocabulary update monitor](../webvoc-update-monitor.md)
- `mapping_quality_report/mapping_quality_report.json`
