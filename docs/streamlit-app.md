# Streamlit app

Start the app with:

```bash
streamlit run app/streamlit_app.py
```

The app accepts one XML upload, runs the MVP mapping, displays validation and
JSON-LD, previews mapping rows, and provides four downloads. Uploaded XML bytes
are passed directly to the package and are not intentionally written to disk.
