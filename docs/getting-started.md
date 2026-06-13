# Getting started

## Requirements

- Python 3.11 or newer
- A GDSN-like XML product document

## Install

```bash
python -m venv .venv
python -m pip install -e ".[dev,app]"
```

## Convert the example

```bash
gdsn-to-gs1-jsonld convert examples/input/example_product.xml \
  --mapping mapping/mapping_mvp.yaml \
  --output output/
```

Run `pytest` to verify the converter and reports.
