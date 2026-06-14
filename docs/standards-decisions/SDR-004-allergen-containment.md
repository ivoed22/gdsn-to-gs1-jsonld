# SDR-004 — Allergen Containment

## Status

Open

## Summary

The source containment code is mapped, but `gs1:levelOfContainment` is not
validated; `gs1:allergenLevelOfContainmentCode` is the available candidate.

## Affected mappings

| Field | Current target | Current status | Warning category | Blocks release? |
| ----- | -------------- | -------------- | ---------------- | --------------- |
| `allergens[].level_of_containment` | `gs1:levelOfContainment` | BMS/XPath mapped; target review required | `webvoc_term_missing` | No |

## Current behaviour

The converter preserves the GDSN `levelOfContainmentCode` value inside each
allergen object.

## Why this needs review

The candidate replacement appears technically direct, but its domain, range,
code-list expectations, and compatibility impact must be confirmed before a
released property is replaced.

## Options

### Option A — Keep current experimental output

- Description: retain the current property and warning.
- Advantages: no compatibility impact.
- Disadvantages: unresolved vocabulary term remains.
- Converter output: unchanged.
- Web Vocabulary conformance: partial.
- GDSN traceability: strong.
- Governance: warning remains mandatory.

### Option B — Replace with `gs1:allergenLevelOfContainmentCode`

- Description: use the validated candidate property.
- Advantages: clearer vocabulary alignment.
- Disadvantages: property change for consumers.
- Converter output: breaking field-name change.
- Web Vocabulary conformance: improved if range usage is confirmed.
- GDSN traceability: unchanged.
- Governance: requires food/Web Vocabulary approval.

### Option C — Version the allergen projection

- Description: introduce the replacement only in a new mapping profile.
- Advantages: preserves historical compatibility.
- Disadvantages: maintains parallel profiles.
- Converter output: unchanged for old profiles; changed for the new profile.
- Web Vocabulary conformance: explicit per version.
- GDSN traceability: unchanged.
- Governance: needs deprecation guidance.

## Recommended direction

Confirm Option B semantically, then deliver it through Option C so historical
profiles remain stable.

## Decision needed from

- GS1 Web Vocabulary owner
- Food-sector experts
- Internal project owner

## Follow-up actions

- Confirm property domain and range.
- Validate code values against representative samples.
- Define mapping-version and migration notes.

## Links

- [v0.6.1 warning cleanup](../warning-cleanup-v0.6.1.md)
- [Web Vocabulary conformance review](../web-vocabulary-conformance-review.md)
- [Web Vocabulary update monitor](../webvoc-update-monitor.md)
- `mapping_quality_report/mapping_quality_report.json`
