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

**v0.21.0**: Single XML conversion's "Review mapping & evidence" step gained
an "Open codelist validation (Track D)" expander showing per-field
valid/unknown/deprecated/missing/source_unavailable status against the
v0.20.0 codelist registry. Diagnostic only — it never blocks conversion and
adds no new download. See `docs/codelist-registry.md`.

**v0.22.0**: The Bulk ZIP workflow gained the same codelist validation
expander, aggregated across the whole batch: five status metrics summed
over every file, plus a table of files that had at least one non-valid
codelist entry. Diagnostic only — never blocks a file or changes the
export ZIP.

**v0.27.0**: The landing page (shown before any workflow is opened) gains
a "Workbench status" panel with six at-a-glance metrics — WebVoc
coverage, registry accepted count, open SDRs, codelists imported, builder
fields authored, and hard-mapping reviews recorded this session. Every
number is read from an existing workflow's own data source; see
`docs/releases/v0.27.0.md`.
