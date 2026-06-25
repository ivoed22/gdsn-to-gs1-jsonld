# Bulk XML batch conversion

Version 0.8.0 adds a batch wrapper around the existing single-file converter.
It processes multiple XML files from one ZIP and produces a downloadable ZIP
with JSON-LD outputs, per-file reports, and batch summaries.

Batch conversion does not change mapping semantics. Each XML file is converted
with the same `convert_xml_to_jsonld` path used by the single XML CLI and
Streamlit workflow.

## ZIP input

The input must be a `.zip` file. XML files may be at the ZIP root or in nested
folders. Non-XML files are ignored.

ZIP entry paths are never used as output paths. Unsafe XML entries, including
absolute paths, drive-qualified paths, and `..` traversal segments, are reported
as per-file errors and are not read.

## Safety limits

The batch backend enforces configurable limits before conversion:

- maximum XML file count
- maximum uncompressed size per XML file
- maximum total uncompressed XML payload size

The default CLI limits are:

- `--max-files 100`
- `--max-file-size-mb 10`
- `--max-total-size-mb 100`

## Output ZIP

The generated batch export ZIP contains:

```text
batch_summary.json
batch_summary.xlsx
products/<output_name>.jsonld
reports/<output_name>_mapping_report.xlsx
reports/<output_name>_validation_report.json
reports/<output_name>_unmapped_fields.json
errors/<safe_filename>_error.json
```

Successful XML files create one product JSON-LD file and three supporting
reports. Failed XML files create an error JSON file with the original filename,
sanitized filename, error type, and message.

## Per-file results

Each batch summary row includes:

- original filename
- sanitized filename
- status
- GTIN, when detected
- output base name
- mapped count
- unmapped count
- validation status
- validation error and warning counts
- error type and message for failures

One invalid XML file does not stop the rest of the batch. The CLI exits
successfully when at least one XML file converts successfully. It exits
non-zero when no XML file can be processed or when a fatal batch-level issue,
such as an unreadable ZIP or exceeded total-size limit, occurs.

## CLI usage

```bash
gdsn-to-gs1-jsonld convert-batch \
  --input-zip path/to/input.zip \
  --mapping mapping/mapping_v0_3.yaml \
  --output-dir batch_output/ \
  --max-files 100 \
  --max-file-size-mb 10 \
  --max-total-size-mb 100
```

The output directory receives:

- `batch_summary.json`
- `batch_summary.xlsx`
- `batch_export.zip`

## Streamlit usage

In the Streamlit app, choose `Convert GDSN XML`, then open the `Bulk ZIP` tab.
Upload a ZIP file, run the batch conversion, review the dashboard and preview
table, then download the batch export ZIP.

The existing `Single XML` tab keeps the original one-product workflow and
download filenames.

## Mapping behavior

Bulk conversion does not introduce new mappings, suppress warnings, or change
converter output for existing single-file workflows. Mapping YAML files, catalog
data, and Web Vocabulary snapshots remain unchanged.
