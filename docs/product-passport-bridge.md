# Product Passport Bridge

**Status: Prototype/reference only. Source inventory and structural schema validation only. No official GS1 validation or production compliance is claimed.**

> **v0.12.1 hardening.** `jsonschema>=4` is now an explicit project dependency.
> Structural validation uses jsonschema Draft7; a required-field-only fallback
> is retained but clearly flagged (`validator_mode`, plus a visible warning in
> the CLI and UI) so a "Passed" result under the fallback is never mistaken for
> full structural validation. The source manifest is also enforced against
> `source_manifest.schema.json`. Placeholder schemas with no downloaded file
> are listed as unavailable and are not offered as validation targets.

## Purpose

The Product Passport Bridge is a prototype workflow that:

1. Inventories public Digital Product Passport (DPP) reference sources (JSON-LD contexts, JSON Schemas, SHACL shapes, examples).
2. Validates prototype Product Passport JSON files against local JSON Schemas using structural validation.

It does **not** claim official GS1 validation, EU DPP regulatory compliance, or production readiness.

## Naming Policy

The feature family name is **Product Passport Bridge**. External source names (e.g., specific regulation names, project names) are allowed **only** in source manifests (`source_manifest.json`) as provenance metadata (title, URL, checksum, license). They must **not** appear in product-facing labels, UI text, release titles, or roadmap headings.

## Source / Reference Scope

All source files used by the Product Passport Bridge are:
- Downloaded separately by the user from public URLs listed in the source manifest.
- Not committed to the repository (with the exception of locally-created prototype examples).
- Tracked in `product_passport/reference_sources/source_manifest.json` with checksums, retrieval dates, and usage notes.

## Source Manifest Structure

File: `product_passport/reference_sources/source_manifest.json`

Each source entry contains:

| Field | Required | Description |
|---|---|---|
| `source_id` | Yes | Unique snake_case identifier |
| `title` | Yes | Human-readable title |
| `source_url` | Yes | Public URL or PLACEHOLDER |
| `source_type` | Yes | One of: `context`, `json_schema`, `shacl_shape`, `example`, `epcis_example` |
| `version` | No | Version string or PLACEHOLDER |
| `sector` | Yes | One of: `core`, `general_product`, `battery`, `textile`, `epcis` |
| `local_path` | Yes | Path relative to repo root |
| `sha256` | No | SHA-256 checksum or PLACEHOLDER |
| `retrieved_at` | No | ISO 8601 date/datetime |
| `public_accessible` | No | Boolean or null |
| `license_or_rights_note` | No | License/rights note |
| `proof_of_concept_note` | No | POC/placeholder status note |
| `usage_note` | No | How this source is used |
| `used_by` | No | List of feature/release identifiers |
| `normalized_output` | No | Path to normalized output or null |

The manifest schema is at `product_passport/reference_sources/source_manifest.schema.json`.

## Contexts Inventory

Source type: `context`  
Currently: 1 placeholder entry for a core DPP JSON-LD context.  
Sector: `core`  
Local path pattern: `product_passport/reference_sources/raw_public/contexts/`

## JSON Schema Inventory

Source type: `json_schema`  
Currently: placeholder entries for general product, battery, and textile DPP schemas.  
Sectors: `general_product`, `battery`, `textile`  
Local path pattern: `product_passport/reference_sources/raw_public/schemas/`

A built-in minimal schema is committed to the repository:  
`product_passport/reference_sources/raw_public/schemas/dpp_minimal.schema.json`

This schema validates the presence of `@context` and `@type` only. It does not claim to be an official DPP schema.

## SHACL Shapes (Inventory Only)

Source type: `shacl_shape`  
Currently: 1 placeholder entry for core DPP SHACL shapes.  
Sector: `core`  
Local path pattern: `product_passport/reference_sources/raw_public/shacl/`

**SHACL execution is NOT performed in v0.12.0.** Shapes are inventoried only.

## Examples Inventory

Source type: `example`  
A minimal prototype example is committed to the repository:  
`product_passport/examples/minimal_product_passport.json`

This example is for structural testing only. It is not official GS1 or DPP production data.

## EPCIS Example Inventory

Source type: `epcis_example`  
Currently: 1 placeholder entry.  
Sector: `epcis`

## Structural Validation Approach

The Schema Validator uses JSON Schema Draft 7 (via `jsonschema` library) to perform structural validation. It:
- Loads a local JSON Schema file.
- Validates a Product Passport JSON instance against it.
- Returns a validation report with status (`valid`/`invalid`/`schema_error`), error list, and prototype warning.

If `jsonschema` is not installed, a minimal fallback checks required-field presence only.

This is **not** official GS1 validation. This is **not** production compliance checking.

## CLI Commands

### inventory-product-passport-sources

```bash
gdsn-to-gs1-jsonld inventory-product-passport-sources \
  --manifest product_passport/reference_sources/source_manifest.json \
  --output-dir product_passport/reference_sources/normalized/ \
  --format json,csv
```

Outputs:
- `product_passport_source_inventory.json`
- `product_passport_source_inventory.csv`
- `product_passport_source_summary.json`

### validate-product-passport

```bash
gdsn-to-gs1-jsonld validate-product-passport \
  --input product_passport/examples/minimal_product_passport.json \
  --schema product_passport/reference_sources/raw_public/schemas/dpp_minimal.schema.json \
  --manifest product_passport/reference_sources/source_manifest.json \
  --output-dir product_passport/validation_reports/
```

Outputs:
- `product_passport_validation_report.json`

Exit 0 on success. Non-zero exit only on tool error (file not found, invalid JSON). Validation failure (invalid instance) still exits 0.

## Streamlit Workflow

The "Validate Product Passport Sources" workflow is the sixth workflow card (marker: PP) in the Streamlit app.

It has three tabs:

1. **Source Inventory** — Load manifest, view source counts by type/sector, browse source table, download inventory JSON/CSV.
2. **Schema Validator** — Upload or paste Product Passport JSON, select local schema, validate, view errors, download report.
3. **Examples** — List example sources, preview committed example JSON.

Top warning (always visible): "⚠️ Product Passport Bridge is a prototype/reference workflow. v0.12.0 performs source inventory and structural schema validation only. It does not claim official GS1 validation or production compliance."

## Limitations

- All source files (except the committed minimal example and schema) must be downloaded separately by the user.
- SHACL shapes are inventoried but not executed.
- JSON Schema validation is structural only; it does not check GS1 semantic correctness.
- No GS1 Digital Link resolution is performed.
- No VC / signed credentials are created.
- No online fetching is performed.
- No production compliance is claimed.

## What This Does NOT Do

- Does NOT build a Product Passport Builder (authoring tool).
- Does NOT implement GS1 ↔ Product Passport Crosswalk.
- Does NOT execute SHACL validation.
- Does NOT fetch from the internet at runtime.
- Does NOT claim official GS1 validation.
- Does NOT claim production compliance.
- Does NOT create VC/signed credentials.
- Does NOT create tag/release v0.12.0 as part of this feature.
