# Architecture

The conversion flow is:

1. `xml_parser.py` parses XML with entity resolution and network access disabled.
2. `mapping_loader.py` validates the YAML profile.
3. `converter.py` evaluates element-selecting XPath expressions and transforms values.
4. `canonical_model.py` validates the typed intermediate product.
5. `validator.py` records required-field errors and optional-field warnings.
6. `jsonld_builder.py` emits mapped GS1 Web Vocabulary properties.
7. `reporter.py` creates JSON and Excel reports.

Both `cli.py` and `app/streamlit_app.py` call `convert_xml_to_jsonld`; interface
code does not duplicate converter logic.
