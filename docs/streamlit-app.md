# Streamlit app

Start the app with:

```bash
streamlit run app/streamlit_app.py
```

The `v0.8.0` app opens with workflow modes:

- `Convert GDSN XML`
- `Explore GS1 Web Vocabulary`
- `Standards Review`

`Convert GDSN XML` contains:

- `Single XML`, the existing one-product upload and export workflow
- `Bulk ZIP`, a batch upload workflow for ZIP files containing XML products

The mapping selector offers:

- Certifications & Documents v0.3.0, selected by default
- Food v0.2.0 mapping
- MVP v0.1.0 mapping for compatibility

The sidebar shows the app version, active mapping path, and supported groups.
Changing profiles clears previous results. Uploaded XML bytes are passed
directly to the package and are not intentionally written to disk.

The Bulk ZIP tab ignores non-XML files and uses the shared batch converter to
produce `batch_summary.json`, `batch_summary.xlsx`, and a batch export ZIP.
The Web Vocabulary mode is a placeholder for a later Explorer release. The
Standards Review mode shows compact read-only SDR/backlog status.
