# Streamlit app

Start the app with:

```bash
streamlit run app/streamlit_app.py
```

The `v0.3.0-dev` app accepts one XML upload and offers:

- Certifications & Documents v0.3.0, selected by default
- Food v0.2.0 mapping
- MVP v0.1.0 mapping for compatibility

The sidebar shows the app version, active mapping path, and supported groups.
Changing profiles clears previous results. Uploaded XML bytes are passed
directly to the package and are not intentionally written to disk.
