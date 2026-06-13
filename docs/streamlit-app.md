# Streamlit app

Start the app with:

```bash
streamlit run app/streamlit_app.py
```

The `v0.2.0-dev` app accepts one XML upload and offers:

- Food v0.2.0 mapping, selected by default
- MVP v0.1.0 mapping for compatibility

It displays validation and JSON-LD, previews mapping rows, persists results
across download reruns, and provides four downloads. Uploaded XML bytes are
passed directly to the package and are not intentionally written to disk.
