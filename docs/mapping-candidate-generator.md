# Mapping Candidate Generator

## Purpose and Review-Only Scope

The Mapping Candidate Generator proposes possible GDSN/BMS/XPath source fields
for GS1 Web Vocabulary properties.  It is a review and decision-support tool.

**What it does NOT do:**
- Does not automatically accept any mapping.
- Does not write or modify mapping YAML files.
- Does not update converter behavior.
- Does not update the mapping catalog CSV.
- Does not claim official GS1 validation.
- Does not claim production compliance.
- Does not fetch anything online.
- Does not use external APIs.

All generation is fully deterministic and offline.  The same inputs always
produce the same outputs.

## Source Inputs

| Input | Description |
|---|---|
| `reference_data/normalized/webvoc_properties_1_17.csv` | GS1 Web Vocabulary properties (v1.17 snapshot) |
| `reference_data/normalized/gdsn_attributes_bms_xpath_3_1_36.csv` | GDSN BMS/XPath attribute reference (v3.1.36) |
| `mapping_catalog/gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_3_webvoc_validated.csv` | Existing mapping catalog |
| `mapping/mapping_v0_3.yaml` | Active YAML mapping profile |
| `docs/standards-decisions/standards_review_backlog.json` | Standards review backlog (optional) |

## Scoring Signals

Scoring combines 11 positive signals and 3 negative signals into a score in
[0.0, 1.0].

### Positive Signals

| Signal | Weight | Description |
|---|---|---|
| `existing_mapping_catalog_match` | 0.90 | WebVoc property already in catalog as mapped |
| `mapping_yaml_canonical_field_match` | 0.65 | GDSN field referenced in YAML for this property |
| `semantic_resource_urn_match` | 0.80 | GDSN SemanticResourceURN matches WebVoc term URI |
| `exact_property_name_match` | 0.70 | WebVoc label/compact name exactly matches GDSN name |
| `label_attribute_token_overlap` | 0.35 | Token overlap between WebVoc label/comment and GDSN name/definition |
| `xpath_terminal_match` | 0.25 | XPath terminal segment resembles WebVoc compact name tokens |
| `definition_comment_overlap` | 0.20 | Shared tokens between WebVoc comment and GDSN definition |
| `range_datatype_compatible` | 0.15 | WebVoc range and GDSN DataType appear compatible |
| `quantity_uom_compatible` | 0.20 | Quantity-like property paired with UOM-enabled GDSN attribute |
| `code_list_signal` | 0.15 | Both property and attribute involve controlled value lists |
| `standards_review_linked` | 0.10 | Property referenced in open standards-review backlog |

### Negative Signals (Penalties)

| Signal | Penalty | Description |
|---|---|---|
| `deleted_attribute_warning` | -0.30 | GDSN attribute is marked deleted |
| `datatype_mismatch_warning` | -0.15 | Range/DataType appear incompatible |
| `class_row_not_attribute` | -0.20 | Row is Class/Module, not leaf Attribute |

## Confidence Levels

| Level | Score Threshold | Description |
|---|---|---|
| `high` | >= 0.70 | Strong convergence of multiple signals |
| `medium` | >= 0.40 | Moderate signal overlap |
| `low` | >= 0.15 | Weak signal; requires careful review |
| `review_required` | < 0.15 or SDR-linked | Low confidence or explicitly in standards backlog |

## Review Statuses

| Status | When Assigned |
|---|---|
| `already_mapped` | Property is in catalog with mapped/candidate status |
| `review_required` | Standards-review-linked or low confidence |
| `not_recommended` | Deleted attribute or incompatible type |
| `proposed` | Passes confidence threshold with no disqualifying signal |

## Reason Codes Reference

| Code | Meaning |
|---|---|
| `existing_mapping_catalog_match` | Catalog already maps this property |
| `mapping_yaml_canonical_field_match` | YAML includes a field for this property |
| `semantic_resource_urn_match` | SemanticResourceURN matches WebVoc term |
| `exact_property_name_match` | Name exactly matches label/compact name |
| `label_attribute_token_overlap` | Token overlap between label/comment and GDSN name |
| `xpath_terminal_match` | XPath terminal resembles compact name |
| `definition_comment_overlap` | Shared tokens in definitions/comments |
| `range_datatype_compatible` | Compatible range/datatype pair |
| `quantity_uom_compatible` | Quantity property + UOM-enabled attribute |
| `code_list_signal` | Both sides have controlled value lists |
| `standards_review_linked` | SDR open for this property |
| `deleted_attribute_warning` | Attribute is deleted |
| `datatype_mismatch_warning` | Incompatible range/datatype |
| `class_row_not_attribute` | Row is not a leaf attribute |

## CLI Usage

```bash
# Generate candidates for all WebVoc properties
gdsn-to-gs1-jsonld generate-mapping-candidates \
  --webvoc-properties reference_data/normalized/webvoc_properties_1_17.csv \
  --gdsn-reference reference_data/normalized/gdsn_attributes_bms_xpath_3_1_36.csv \
  --catalog mapping_catalog/gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_3_webvoc_validated.csv \
  --mapping mapping/mapping_v0_3.yaml \
  --standards-backlog docs/standards-decisions/standards_review_backlog.json \
  --output-dir mapping_candidate_reports/

# Generate candidates for a single property
gdsn-to-gs1-jsonld generate-mapping-candidates \
  --property gs1:gtin \
  --webvoc-properties reference_data/normalized/webvoc_properties_1_17.csv \
  --gdsn-reference reference_data/normalized/gdsn_attributes_bms_xpath_3_1_36.csv \
  --catalog mapping_catalog/gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_3_webvoc_validated.csv \
  --mapping mapping/mapping_v0_3.yaml \
  --output-dir mapping_candidate_reports_gtin/

# High-confidence only
gdsn-to-gs1-jsonld generate-mapping-candidates \
  --min-confidence high \
  --no-include-low-confidence \
  --webvoc-properties reference_data/normalized/webvoc_properties_1_17.csv \
  --gdsn-reference reference_data/normalized/gdsn_attributes_bms_xpath_3_1_36.csv \
  --catalog mapping_catalog/gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_3_webvoc_validated.csv \
  --mapping mapping/mapping_v0_3.yaml \
  --output-dir mapping_candidate_reports_high/
```

## Streamlit Workflow Description

The "Generate Mapping Candidates" workflow card (marker: MAP) in the Streamlit
app provides:

1. A top-level warning noting candidates are review-only.
2. A controls section: property selector, confidence filter, review status
   filter, include-already-mapped checkbox, include-low-confidence checkbox,
   limit per property input.
3. A "Generate Candidates" button.
4. After generation: metrics (total, high/medium/low/review_required/already_mapped).
5. A candidate table with columns: WebVoc property, GDSN attribute name, BMS ID,
   score, confidence, review status, top reason, SDR linked.
6. A detail expander for the selected candidate.
7. Downloads: JSON, CSV, optional XLSX.

The workflow never provides an "accept" or "apply" button.  No mapping YAML
is editable in this workflow.

## Report Output Format

### JSON (`mapping_candidates.json`)
Array of candidate objects, each containing all fields documented in
`mapping_candidate_generator.py`.

### CSV (`mapping_candidates.csv`)
Flat CSV with the same fields.  List fields (reasons, warnings, linked_sdr_ids)
are joined with `; ` delimiter.

### XLSX (`mapping_candidates.xlsx`)
Excel workbook with the same data as CSV.  Requires `openpyxl`.

### Summary (`mapping_candidates_summary.json`)
Aggregated counts:
- `total_candidates`
- `properties_covered`
- `by_confidence` (high/medium/low/review_required)
- `by_review_status` (proposed/already_mapped/review_required/not_recommended)
- `created_by_version`

## Limitations

- Score thresholds are starting points and may need tuning as more data is reviewed.
- Token matching is case-insensitive and ignores common stopwords, but semantic
  similarity is not guaranteed.
- Range/DataType compatibility mapping is heuristic, not formally derived from
  ontology axioms.
- The generator does not understand complex XPath predicates.
- Candidates for object-type properties (complex structures) require additional
  modelling review beyond what the score captures.

## What It Does NOT Do

- Does NOT accept, write, or apply any mapping.
- Does NOT modify mapping YAML files.
- Does NOT modify the mapping catalog CSV.
- Does NOT change converter output or batch behavior.
- Does NOT fetch anything online.
- Does NOT use external APIs.
- Does NOT claim official GS1 validation.
- Does NOT claim production compliance.
