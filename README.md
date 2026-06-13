# GDSN to GS1 JSON-LD

Convert GDSN-like product XML into GS1 Web Vocabulary JSON-LD through a
configurable YAML mapping and a typed canonical product model.

Version 0.3.0 keeps the v0.1.0 and v0.2.0 outputs stable and adds experimental
BMS/XPath-aligned certification and document mapping. It is deliberately a
structured product converter, not a generic XML-to-JSON utility.

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

## Streamlit

```bash
streamlit run app/streamlit_app.py
```

The app defaults to Certifications & Documents v0.3.0 and can switch to the
Food v0.2.0 or MVP v0.1.0 profiles.

## Mapping

Mapping YAML is the executable converter configuration. The catalog under
`mapping_catalog/` is the BMS/XPath and vocabulary traceability layer. Version
0.3.0 uses GDSN 3.1.36 catalog rows and locally validated Web Vocabulary terms
as design inputs.

## Development

```bash
pytest
```

See [`docs/`](docs/index.md) for architecture, mapping, output, app, and roadmap
notes.

## Roadmap

Later releases may resolve experimental document semantics, add broader food
coverage, certification verification, validation profiles, and batch
conversion.

## Disclaimer

This is an experimental converter. Generic DPP/document links require
standards review. No certificate verification, URL dereferencing, full GDSN
coverage, or full GDSN XSD validation is provided.
