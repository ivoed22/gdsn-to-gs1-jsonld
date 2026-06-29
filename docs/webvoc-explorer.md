# Web Vocabulary Explorer

## Purpose

The Web Vocabulary Explorer turns the v0.9.0 placeholder into a read-only
review surface for the local GS1 Web Vocabulary snapshot. It helps users browse
classes and properties, inspect mapping coverage, and see where catalog rows or
standards decision records already provide evidence.

The Explorer is a standards and mapping review tool. It is not a manual mapping
editor and does not generate JSON-LD or YAML mappings.

## Local Input Files

- `webvoc/current/gs1Voc.jsonld`
- `webvoc/current/linktypes.json`
- `webvoc/current/metadata.json`
- `mapping_catalog/gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_3_webvoc_validated.csv`
- `docs/standards-decisions/standards_review_backlog.json`

All inputs are local. The Explorer does not fetch online vocabulary resources
or call external APIs.

## Extraction

Classes are extracted from JSON-LD graph nodes with `owl:Class` or
`rdfs:Class` types.

Properties are extracted from graph nodes with `rdf:Property`,
`owl:ObjectProperty`, or `owl:DatatypeProperty` types.

For each term, the Explorer preserves available local metadata:

- compact term id, such as `gs1:gtin`
- full IRI, usually `https://gs1.org/voc/<term>`
- label and comment
- domain and range
- `subPropertyOf`
- type/classification
- Web Vocabulary term status
- link-type indicator where the property is a `gs1:linkType` child or appears
  in `linktypes.json`

## Coverage Statuses

Mapping coverage is derived from the local mapping catalog. The Explorer uses
catalog property references from `jsonld_property`,
`recommended_jsonld_property`, and `webvoc_property_validation`.

Statuses are deterministic:

- `high_confidence`: mapped catalog row with high confidence
- `mapped`: mapped catalog row without high-confidence classification
- `candidate`: candidate catalog row
- `experimental`: explicitly experimental catalog row
- `standards_review_required`: row needing BMS, Web Vocabulary, semantic, or
  governance review
- `schema_org_fallback`: catalog row currently using Schema.org where a GS1
  relationship is under review
- `unmapped`: Web Vocabulary property has no linked catalog row
- `unknown`: catalog row has an unrecognized mapping status

Warnings are not suppressed. Existing review warnings remain visible through
coverage and SDR indicators.

## Grouping Logic

Property grouping is pragmatic rather than normative. It is intended to make a
large vocabulary easier to browse in a GS1/GDSN mapping review workflow.

The grouping heuristics consider:

- property name
- label and comment
- domain and range
- `subPropertyOf`
- link-type status
- mapping catalog scope group, canonical field, source attribute, and property
  references

Groups used in v0.9.0:

- Core Product Information
- Classification & Links
- Physical Dimensions
- Digital Links & Services
- Provenance and Claims
- Packaging Details
- Food, Beverage & Tobacco
- Nutritional Information
- Allergens
- Certifications
- Documents and DPP
- Organization and Place
- Offer and Sales Information
- Traceability and Lifecycle
- Other Web Vocabulary Properties

The grouping is deliberately conservative and can be refined later without
changing converter output.

## Mapping Evidence

Where a Web Vocabulary property is referenced by the mapping catalog, the
Explorer links catalog evidence:

- canonical field
- JSON-LD property
- mapping status
- confidence
- mapping version
- technical mapping profile
- scope group
- BMS ID
- GDSN XPath
- source attribute name
- source workbook or review source

This evidence is read-only. It helps explain why a property is considered
mapped, candidate, or review-bound.

## SDR And Governance Links

The Explorer loads the standards review backlog and links open SDR records to
properties listed in each SDR's `affected_properties`.

Displayed governance context includes:

- SDR ID
- title
- category
- status
- warning count
- affected fields
- GitHub issue URL where available
- decision file

## CLI Usage

Export the Explorer dataset:

```bash
gdsn-to-gs1-jsonld export-webvoc-explorer \
  --webvoc webvoc/current/gs1Voc.jsonld \
  --catalog mapping_catalog/gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_3_webvoc_validated.csv \
  --backlog docs/standards-decisions/standards_review_backlog.json \
  --output-dir webvoc_explorer_output/
```

Outputs:

- `webvoc_explorer_properties.json`
- `webvoc_explorer_properties.csv`
- `webvoc_explorer_summary.json`
- `webvoc_explorer_summary.xlsx`

## Streamlit Usage

Run the app:

```bash
streamlit run app/streamlit_app.py
```

Choose `Explore GS1 Web Vocabulary`.

The mode shows:

- WebVoc version
- class and property counts
- mapped property count
- standards-review property count
- group filter
- domain selector
- coverage status filter
- search box
- mapped-only and standards-review-only filters
- read-only property table
- property detail expander with evidence and SDR notes
- a clearly labelled manual JSON-LD prototype panel marked as planned

## Limitations

- The Explorer uses the committed local snapshot only.
- It does not refresh Web Vocabulary data.
- It does not edit catalog rows.
- It does not edit or generate mapping YAML.
- It does not change converter output.
- It does not prove full GS1 Web Vocabulary conformance.
- Grouping is heuristic and intended for review navigation.

## Why Read-Only In v0.9.0

Manual JSON-LD authoring and mapping edits would need stronger governance.
Manual JSON-LD would not be GDSN/BMS/XPath traceable unless linked to mapping
evidence. v0.9.0 therefore focuses on browsing, coverage review, and evidence
surfacing while preserving converter behavior.
