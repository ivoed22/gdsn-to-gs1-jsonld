# Product Passport Builder

**Status: Prototype/reference only. Minimal-schema prototype mode. Structural validation only. Not official GS1 validation, not EU DPP regulatory compliance, and not production-ready.**

## Purpose

The Product Passport Builder (v0.13.0) wraps GS1 Web Vocabulary JSON-LD into a
prototype Product Passport JSON-LD envelope and validates the built envelope
against a local structural schema. It is part of the **Product Passport Bridge**
feature family and reuses the validator introduced in v0.12.x.

It answers: "Given GS1 Web Vocabulary JSON-LD for a product, what would a
prototype Product Passport envelope look like, and does it match a local
structural schema?"

## Minimal-schema prototype mode

v0.13.0 validates only against the committed built-in minimal schema
(`product_passport/reference_sources/raw_public/schemas/dpp_minimal.schema.json`).
The external DPP schemas listed in the source manifest are placeholders (source
URLs and checksums not yet filled) and are **not** selectable build targets. No
real DPP schema is invented or claimed.

## Input

GS1 Web Vocabulary JSON-LD from any of:

- the converter output;
- the Manual JSON-LD Prototype Builder;
- pasted or uploaded GS1 JSON-LD.

Input is tolerant of both converter (`@type: gs1:Product`) and manual-builder
(`@type: Product`) shapes, and of language-tagged values.

## Envelope structure

```
@context, @type, @id
productPassportId, passportType, passportVersion, status
prototypeNotice, defaultLanguage, createdByVersion
source:      { sourceType, sourceFormat, sourceGtin, sourceProductName }
validation:  { validationMode, schema, note }
product:     { ...embedded source GS1 JSON-LD... }   (toggleable)
generatedAt: (only if explicitly supplied)
```

Default output is deterministic (byte-stable) so tests and diffs are stable.

## Builder settings

- passport id (optional; derived from GTIN if blank)
- default language
- include source GS1 JSON-LD (on by default)
- validation schema (built-in minimal; placeholders shown as unavailable)

## CLI

```bash
gdsn-to-gs1-jsonld build-product-passport \
  --input path/to/gs1-product.jsonld \
  --schema product_passport/reference_sources/raw_public/schemas/dpp_minimal.schema.json \
  --output-dir product_passport/builder_outputs/
```

Outputs `product_passport.jsonld`, `product_passport_validation_report.json`,
and `product_passport_summary.json`. Prints the prototype/reference warning,
schema, validator mode, and structural validation status. If `jsonschema` is
unavailable it falls back to a required-field check and says so.

## Streamlit workflow

"Build Product Passport Prototype" (marker: PB), four tabs: Input GS1 JSON-LD,
Builder Settings, Product Passport Output, Validation Report. The validation tab
states explicitly that passing means only that the JSON matches the selected
local structural schema — not an official GS1 validation or EU DPP compliance
result.

## Validation report

Reuses the v0.12.x validator. Fields: `validation_status`
(`valid`/`invalid`/`schema_error`), `validator_mode`
(`jsonschema`/`minimal_fallback`), `errors`, `warnings`, `validator_version`,
`schema_file`, `prototype_warning`.

## What it does NOT do

- Does NOT claim official GS1 validation.
- Does NOT claim EU DPP regulatory or production compliance.
- Does NOT validate against real DPP schemas (minimal-schema mode).
- Does NOT build the GS1 ↔ Product Passport Crosswalk (planned v0.14.0).
- Does NOT execute SHACL.
- Does NOT create Verifiable Credentials or signed credentials.
- Does NOT fetch anything online.

## Relation to other features

- **v0.12.x Product Passport Source Validator** — source inventory and schema
  validation; this builder reuses its validator.
- **v0.14.0 GS1 ↔ Product Passport Crosswalk** (future) — property-level
  crosswalk evidence.
- **Future VC / trust layer** — envelope and proofs; not started.
