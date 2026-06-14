# Mapping quality checks

Version 0.4.0 adds read-only governance checks for the mapping catalog and
executable YAML profiles. The checks do not generate mappings or change
conversion behavior.

## Catalog check

```bash
gdsn-to-gs1-jsonld check-catalog \
  --catalog mapping_catalog/gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_3_webvoc_validated.csv
```

The command checks required columns, mapped/candidate row completeness,
official high-confidence BMS IDs, allowed confidence values, known mapping
statuses, JSON-LD targets, and Web Vocabulary review metadata.

## YAML/catalog check

```bash
gdsn-to-gs1-jsonld check-mapping \
  --mapping mapping/mapping_v0_3.yaml \
  --catalog mapping_catalog/gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_3_webvoc_validated.csv \
  --output mapping_quality_report/
```

The comparison includes simple fields, object mappings, and object child
fields. It reports YAML fields missing from the catalog, property differences,
mapped or high-confidence catalog fields missing from YAML, experimental
mappings, review items, and Web Vocabulary issues.

## Severity and exits

- `error`: malformed or missing inputs, missing required columns, or ambiguous
  duplicate critical catalog keys
- `warning`: incomplete governance, unknown values, coverage gaps, or
  vocabulary review findings
- `info`: aligned or explicitly documented experimental mappings

The default exit code is 0 when there are no errors. `--strict` makes warnings
fail with exit code 1.

## Reports

When `--output` is provided, the command writes:

- `mapping_quality_report.json`
- `mapping_quality_report.xlsx`

The JSON contains summary counts, findings, YAML and catalog coverage, missing
items, experimental mappings, review items, and Web Vocabulary issues. The
Excel workbook contains Summary, Errors, Warnings, YAML Coverage, Catalog
Coverage, Missing From Catalog, Missing From YAML, Experimental Mappings, Needs
Review, and WebVoc Issues tabs.

Reports are diagnostic inputs for human review. A warning does not by itself
mean the current converter output is invalid.

From v0.6.0, each warning also includes:

- `category`
- `affected_field_property`
- `reason`
- `recommended_action`
- `blocks_release`

Categories distinguish vocabulary gaps, available linktypes, experimental
mappings, BMS review, YAML/catalog mismatches, document/DPP modelling,
nutrient modelling, image modelling, schema.org fallback, and governance
review.
