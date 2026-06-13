# GDSN to GS1 JSON-LD

Convert GDSN-like product XML into GS1 Web Vocabulary JSON-LD through a
configurable YAML mapping and a typed canonical product model.

Version 0.2.0 keeps the v0.1.0 product identity output stable and adds an
experimental food profile for multilingual ingredients, allergen details, and
basic nutrient quantities. It is deliberately a structured product converter,
not a generic XML-to-JSON utility.

## Mapping profiles

- `mapping/mapping_mvp.yaml`: v0.1.0 product identity and presentation fields
- `mapping/mapping_v0_2.yaml`: v0.1.0 fields plus ingredients, allergens, and
  nutrients

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
  --mapping mapping/mapping_v0_2.yaml \
  --output output_v0_2/
```

You can also run the module directly:

```bash
python -m gdsn_to_gs1_jsonld.cli convert examples/input/example_product.xml \
  --mapping mapping/mapping_v0_2.yaml \
  --output output_v0_2/
```

## Streamlit

```bash
streamlit run app/streamlit_app.py
```

The app defaults to the Food v0.2.0 profile and can switch back to the MVP
v0.1.0 profile. It processes uploaded XML in memory, displays the JSON-LD and
validation status, previews the mapping report, and provides four downloads.

## Mapping

Mapping YAML is the source of truth for XML XPath expressions, canonical field
targets, transforms, requirements, and JSON-LD property names. Version 0.2.0
adds `object_mappings` for configurable allergen and nutrient objects. XPath
expressions select elements so language attributes remain available.

## Development

```bash
pytest
```

See [`docs/`](docs/index.md) for architecture, mapping, output, app, and roadmap
notes.

## Roadmap

Later releases may add broader food coverage, certifications, serving
information, validation profiles, batch conversion, and service interfaces.

## Disclaimer

This is an experimental converter. The v0.2.0 food mapping does not provide
full GDSN coverage, full nutrition or allergen semantics, full GDSN XSD
validation, or a guarantee that generated data satisfies every consuming
system's GS1 implementation profile.
