# Reference Data Import

The `import-reference-data` command converts local public source references
into deterministic JSON and CSV files for offline standards review.

It is an import and inventory command only. It does not call the converter, edit
mapping YAML, update catalog rows, refresh Web Vocabulary snapshots, or fetch
network resources.

## Command

```bash
gdsn-to-gs1-jsonld import-reference-data \
  --gdsn-xlsx reference_data/raw_public/GDSN_Attributes_with_BMSId_xPath_3.1.36_June_5_2026.xlsx \
  --webvoc webvoc/current/gs1Voc.jsonld \
  --source-manifest reference_data/source_manifest.json \
  --output-dir reference_data/normalized/
```

## Inputs

- `--gdsn-xlsx`: public GDSN BMS/XPath workbook.
- `--webvoc`: local GS1 Web Vocabulary JSON-LD snapshot.
- `--source-manifest`: JSON source inventory with URLs, checksums, and usage
  notes.
- `--output-dir`: destination for normalized JSON, CSV, and summary files.

## Outputs

The command writes:

- `gdsn_attributes_bms_xpath_3_1_36.csv`
- `gdsn_attributes_bms_xpath_3_1_36.json`
- `webvoc_properties_1_17.csv`
- `webvoc_properties_1_17.json`
- `webvoc_classes_1_17.csv`
- `webvoc_classes_1_17.json`
- `source_data_summary.json`

## GDSN Normalization

The importer selects the `3.1.36` workbook sheet and includes rows from
`Deleted Attributes` when present. Rows are flagged as:

- attribute rows
- class rows
- deleted rows
- candidate source rows

Candidate source rows are active `Attribute` rows that have a BMS ID, XPath,
and source name. This flag is intended for future review tooling; it does not
change any mapping.

Normalized GDSN fields include BMS ID, message, XPath, module, row type, parent
class, source attribute name, multiplicity, length, data type, code-list
metadata, language/UOM/currency flags, semantic resource URN, definition,
source sheet, source version, deletion flag, and candidate-source flag.

## Web Vocabulary Normalization

The importer reads JSON-LD with `utf-8-sig` so files with or without a UTF-8
BOM are handled the same way.

Normalized Web Vocabulary properties include term ID, compact name, label,
comment, domain, range, `subPropertyOf`, type, link-type flag, term status,
version, and last modified date.

Normalized Web Vocabulary classes include term ID, compact name, label,
comment, superclass, type, term status, version, and last modified date.

## Summary Checks

`source_data_summary.json` includes:

- manifest checksum checks
- GDSN sheet count and selected sheet
- GDSN row counts by role
- rows with BMS ID, XPath, definitions, data types, and code-list metadata
- possible duplicate BMS IDs and XPath values
- missing critical GDSN fields
- Web Vocabulary class and property counts
- Web Vocabulary version and last modified date
- Web Vocabulary link-type and stable-property counts
- missing critical Web Vocabulary fields

Warnings and inventory findings are reported as data. They are not suppressed or
converted into mapping changes.
