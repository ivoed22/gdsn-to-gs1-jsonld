# SDR-001 — Nutrient Modelling

## Status

Open

GitHub issue: [#4](https://github.com/ivoed22/gdsn-to-gs1-jsonld/issues/4)

## Summary

The current profile extracts nutrient data reliably, but its generic target
properties are not validated in GS1 Web Vocabulary 1.17.

## Affected mappings

| Field | Current target | Current status | Warning category | Blocks release? |
| ----- | -------------- | -------------- | ---------------- | --------------- |
| `nutrients[].preparation_state` | `gs1:preparationStateCode` | Experimental target | `nutrient_modelling` | No |
| `nutrients[].nutrient_type` | `gs1:nutrientTypeCode` | Experimental target | `nutrient_modelling` | No |
| `nutrients[].quantity_contained` | `gs1:quantityContained` | Experimental target | `nutrient_modelling` | No |

## Current behaviour

The converter emits a generic `gs1:nutrientDetail` object containing
preparation state, nutrient type, value, and unit. GDSN extraction remains
traceable to the catalogued BMS/XPath evidence.

## Why this needs review

The issue is the target semantic model, not XML parsing. Web Vocabulary uses
specific nutrient properties and `gs1:NutritionMeasurementType`; replacing the
generic object requires a governed modelling decision and migration policy.

## Options

### Option A — Keep the experimental generic model

- Description: retain current output and label it experimental.
- Advantages: preserves compatibility and generic source fidelity.
- Disadvantages: does not improve Web Vocabulary conformance.
- Converter output: unchanged.
- Web Vocabulary conformance: remains partial.
- GDSN traceability: unchanged and strong.
- Governance: requires an explicit experimental-use policy.

### Option B — Map to specific GS1 nutrient properties

- Description: select target properties per nutrient code and use validated measurement structures.
- Advantages: strongest alignment with the current vocabulary.
- Disadvantages: requires a code-to-property mapping and broader test corpus.
- Converter output: breaking structural change.
- Web Vocabulary conformance: potentially improved after review.
- GDSN traceability: retained if each generated property records its source.
- Governance: needs Web Vocabulary and food-sector approval.

### Option C — Preserve a canonical nutrient layer and add a reviewed projection

- Description: keep generic canonical extraction but generate a versioned, specific JSON-LD projection.
- Advantages: separates source fidelity from target-vocabulary evolution.
- Disadvantages: introduces profile/version complexity.
- Converter output: changed only in a future versioned profile.
- Web Vocabulary conformance: can be assessed per projection.
- GDSN traceability: strong.
- Governance: requires profile lifecycle and fallback rules.

## Recommended direction

Develop Option C and validate its projection using Option B evidence. Keep the
current mapping unchanged until representative nutrient codes and expected
outputs are reviewed.

## Decision needed from

- GS1 Web Vocabulary owner
- Food-sector experts
- GDSN/GSMP group
- Internal project owner

## Follow-up actions

- Inventory nutrient codes in representative GDSN samples.
- Draft code-to-property candidates.
- Confirm measurement and preparation-state patterns.
- Define compatibility and migration requirements.

## Links

- [v0.6.1 warning cleanup](../warning-cleanup-v0.6.1.md)
- [Web Vocabulary conformance review](../web-vocabulary-conformance-review.md)
- [Web Vocabulary update monitor](../webvoc-update-monitor.md)
- `mapping_quality_report/mapping_quality_report.json`
