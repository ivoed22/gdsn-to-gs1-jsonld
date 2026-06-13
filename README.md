# GDSN to GS1 JSON-LD

Convert GDSN-like product XML into GS1 Web Vocabulary JSON-LD through a
configurable YAML mapping and a typed canonical product model.

This first MVP supports GTIN, multilingual product names and descriptions,
brand name, GPC category code, net content, product image URLs, and a product
page URL. It is deliberately a structured product converter, not a generic
XML-to-JSON utility.

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
  --mapping mapping/mapping_mvp.yaml \
  --output output/
```

You can also run the module directly:

```bash
python -m gdsn_to_gs1_jsonld.cli convert examples/input/example_product.xml \
  --mapping mapping/mapping_mvp.yaml \
  --output output/
```

## Streamlit

```bash
streamlit run app/streamlit_app.py
```

The app processes uploaded XML in memory, displays the JSON-LD and validation
status, previews the mapping report, and provides downloads for all four
outputs.

## Mapping

`mapping/mapping_mvp.yaml` is the source of truth for XML XPath expressions,
canonical field targets, transforms, requirements, and JSON-LD property names.
XPath expressions select elements so language attributes remain available.
Copy `mapping/mapping_template.yaml` to start a profile.

## Development

```bash
pytest
```

See [`docs/`](docs/index.md) for architecture, mapping, output, app, and roadmap
notes.

## Roadmap

Later releases may add broader GDSN coverage, ingredients, allergens,
nutrition, certifications, validation profiles, batch conversion, and service
interfaces.

## Disclaimer

This is an experimental MVP. It does not provide full GDSN coverage, full GDSN
XSD validation, or a guarantee that generated data satisfies every consuming
system's GS1 implementation profile.
