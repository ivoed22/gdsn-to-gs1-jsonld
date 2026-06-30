# GDSN to GS1 JSON-LD

Convert GDSN-like product XML into GS1 Web Vocabulary JSON-LD through a
configurable YAML mapping and a typed canonical product model.

Version 0.11.0 adds a Mapping Candidate Generator — a deterministic,
offline tool that proposes possible GDSN/BMS/XPath source fields for GS1
Web Vocabulary properties with confidence scoring and review reasons.
Candidates are review support only; no mappings are automatically accepted
or written.

Version 0.10.0 added a Manual JSON-LD Prototype Builder for authoring
range-aware GS1 Web Vocabulary product markup by hand.

## Mapping profiles

- `mapping/mapping_mvp.yaml`: v0.1.0 product identity and presentation fields
- `mapping/mapping_v0_2.yaml`: v0.1.0 fields plus ingredients, allergens, and
  nutrients
- `mapping/mapping_v0_3.yaml`: v0.2.0 fields plus certifications and
  DPP/certification document links

## MVP outputs

Each CLI conversion creates:

- `product_{GTIN}.jsonld`
- `mapping_report_{GTIN}.xlsx`
- `validation_report_{GTIN}.json`
- `unmapped_fields_{GTIN}.json`

When GTIN is unavailable, filenames use `unknown`.

## Installation

Python 3.11 or newer is required.

```bash
python -m venv .venv
python -m pip install -e ".[dev,app]"
```

For Streamlit Community Cloud, `requirements.txt` contains all runtime
dependencies and the app adds `src/` to its import path.

## CLI

```bash
gdsn-to-gs1-jsonld convert examples/input/example_product.xml \
  --mapping mapping/mapping_v0_3.yaml \
  --output output_v0_3/
```

You can also run the module directly:

```bash
python -m gdsn_to_gs1_jsonld.cli convert examples/input/example_product.xml \
  --mapping mapping/mapping_v0_3.yaml \
  --output output_v0_3/
```

Convert all XML files in the synthetic sample corpus:

```bash
gdsn-to-gs1-jsonld convert-samples \
  --input-dir examples/input/samples \
  --mapping mapping/mapping_v0_3.yaml \
  --output-dir examples/output/samples
```

The command creates per-product conversion reports plus
`sample_conversion_summary.json` and `sample_conversion_summary.xlsx`.
Failures identify the sample, processing stage, and exception message.

Convert XML files from a ZIP batch:

```bash
gdsn-to-gs1-jsonld convert-batch \
  --input-zip path/to/input.zip \
  --mapping mapping/mapping_v0_3.yaml \
  --output-dir batch_output/ \
  --max-files 100 \
  --max-file-size-mb 10 \
  --max-total-size-mb 100
```

The command ignores non-XML files, rejects unsafe ZIP paths, converts XML files
independently, and writes `batch_summary.json`, `batch_summary.xlsx`, and
`batch_export.zip`. See
[bulk XML batch conversion](docs/bulk-xml-batch-conversion.md).

Validate the mapping catalog:

```bash
gdsn-to-gs1-jsonld check-catalog \
  --catalog mapping_catalog/gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_3_webvoc_validated.csv
```

Compare an executable YAML profile with the catalog and create reports:

```bash
gdsn-to-gs1-jsonld check-mapping \
  --mapping mapping/mapping_v0_3.yaml \
  --catalog mapping_catalog/gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_3_webvoc_validated.csv \
  --output mapping_quality_report/
```

Warnings are non-failing by default. Add `--strict` to either quality command
to make warnings produce exit code 1.

Check the committed Web Vocabulary snapshot without network access:

```bash
gdsn-to-gs1-jsonld check-webvoc-updates \
  --snapshot-dir webvoc/current \
  --output webvoc_update_report/ \
  --no-network
```

Revalidate the mapping catalog against that snapshot:

```bash
gdsn-to-gs1-jsonld revalidate-mapping-catalog \
  --catalog mapping_catalog/gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_3_webvoc_validated.csv \
  --webvoc-dir webvoc/current \
  --output mapping_catalog_revalidation/
```

Normal conversion never fetches external vocabulary resources. See the
[Web Vocabulary update monitor](docs/webvoc-update-monitor.md) for controlled
online comparison and snapshot refresh.

Export the maintained standards-review backlog without network access:

```bash
gdsn-to-gs1-jsonld export-standards-backlog \
  --warning-review docs/warning-cleanup-v0.6.1.md \
  --output docs/standards-decisions/ \
  --format all
```

The command refreshes JSON and CSV backlog files. Detailed
[standards decision records](docs/standards-decisions/index.md) remain
human-maintained review documents.

Export the read-only Web Vocabulary Explorer dataset:

```bash
gdsn-to-gs1-jsonld export-webvoc-explorer \
  --webvoc webvoc/current/gs1Voc.jsonld \
  --catalog mapping_catalog/gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_3_webvoc_validated.csv \
  --backlog docs/standards-decisions/standards_review_backlog.json \
  --output-dir webvoc_explorer_output/
```

The command writes property JSON/CSV and summary JSON/XLSX files without
network access. See the [Web Vocabulary Explorer](docs/webvoc-explorer.md).

Import public reference source data into normalized offline JSON and CSV:

```bash
gdsn-to-gs1-jsonld import-reference-data \
  --gdsn-xlsx reference_data/raw_public/GDSN_Attributes_with_BMSId_xPath_3.1.36_June_5_2026.xlsx \
  --webvoc webvoc/current/gs1Voc.jsonld \
  --source-manifest reference_data/source_manifest.json \
  --output-dir reference_data/normalized/
```

The command checks manifest hashes and writes normalized GDSN/WebVoc reference
data plus `source_data_summary.json`. See the
[source data inventory](docs/source-data-inventory.md) and
[reference data import](docs/reference-data-import.md) notes.

Generate mapping candidates for GS1 Web Vocabulary properties:

```bash
gdsn-to-gs1-jsonld generate-mapping-candidates \
  --webvoc-properties reference_data/normalized/webvoc_properties_1_17.csv \
  --gdsn-reference reference_data/normalized/gdsn_attributes_bms_xpath_3_1_36.csv \
  --catalog mapping_catalog/gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_3_webvoc_validated.csv \
  --mapping mapping/mapping_v0_3.yaml \
  --standards-backlog docs/standards-decisions/standards_review_backlog.json \
  --output-dir mapping_candidate_reports/
```

Candidates are review support only; no mappings are accepted or written.
See [Mapping Candidate Generator](docs/mapping-candidate-generator.md).

## Streamlit

```bash
streamlit run app/streamlit_app.py
```

The app defaults to Certifications & Documents v0.3.0 and can switch to the
Food v0.2.0 or MVP v0.1.0 profiles. It now starts with workflow modes:

- `Convert GDSN XML`, with `Single XML` and `Bulk ZIP` tabs
- `Explore GS1 Web Vocabulary`, a read-only local vocabulary and coverage
  explorer
- `Create JSON-LD Prototype`, a manual Web Vocabulary markup form with live
  JSON-LD preview
- `Standards Review`, a compact read-only view of open SDR/backlog status

## Mapping

Mapping YAML is the executable converter configuration. The catalog under
`mapping_catalog/` is the BMS/XPath and vocabulary traceability layer. Version
0.3.0 uses GDSN 3.1.36 catalog rows and locally validated Web Vocabulary terms
as design inputs. Version 0.4.0 checks catalog governance and YAML/catalog
alignment without generating YAML or changing converter output.

## Sample testing

The files under `examples/input/samples/` are synthetic and contain no real
company data. Place private real-world GDSN XML files in a separate local
directory and point `convert-samples` at that directory. Review the validation
and unmapped reports before sharing outputs because source XML may contain
confidential data.

The converter does not perform full GDSN XSD validation. Unmapped fields show
which populated XML elements were outside the selected profile; they do not
prove that the source XML is invalid.

## Strategic relevance

This project demonstrates a practical bridge from GS1 product data exchange to
machine-readable structured data using GDSN, BMS/XPath, and GS1 Web
Vocabulary.

- [Internal positioning](docs/internal-positioning.md)
- [Open governance questions](docs/open-governance-questions.md)
- [Web Vocabulary conformance review](docs/web-vocabulary-conformance-review.md)
- [Web Vocabulary Explorer](docs/webvoc-explorer.md)
- [Manual JSON-LD Prototype Builder](docs/manual-jsonld-builder.md)
- [Public source data inventory](docs/source-data-inventory.md)
- [Reference data import](docs/reference-data-import.md)
- [Standards decision register](docs/standards-decisions/index.md)
- [Strategic next steps](docs/strategic-next-steps.md)

## For GS1 stakeholders

These concise documents explain the demonstration, its practical output, and
its relevance to standards, AI, and machine-readable product data:

- [Stakeholder one-pager](docs/stakeholder-one-pager.md)
- [Five-minute demo story and speaker notes](docs/demo-story.md)
- [Before and after example](docs/before-after-example.md)
- [Why this matters for AI](docs/ai-relevance.md)

## Development

```bash
python -m pytest
```

See [`docs/`](docs/index.md) for architecture, mapping, output, app, and roadmap
notes.

## Roadmap

Later releases may accept or defer registered standards decisions, add manual
JSON-LD authoring linked to mapping evidence, broaden food coverage, add
certification verification, validation profiles, and production batch
operations beyond the current ZIP upload workflow.

## Disclaimer

This is an experimental converter. Generic DPP/document links require
standards review. No certificate verification, URL dereferencing, full GDSN
coverage, or full GDSN XSD validation is provided.
