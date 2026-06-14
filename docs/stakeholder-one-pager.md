# GDSN to GS1 JSON-LD Converter

## What this project is

The GDSN to GS1 JSON-LD Converter is an experimental, open implementation of a
practical bridge from GS1 product data exchange to machine-readable,
semantically structured product data.

It reads GDSN-like XML, applies traceable mappings, and produces JSON-LD using
GS1 Web Vocabulary terms. The conversion path connects GDSN, BMS identifiers
and official XPath references, a mapping catalog, a canonical product model,
and web-native output.

## What it proves

The project shows that selected product information can move from an
exchange-oriented XML structure into reusable linked data without losing sight
of where each field came from. It demonstrates:

- repeatable conversion rather than a one-off data transformation;
- traceability from output properties back to mapping decisions;
- diagnostics for validation, unmapped source elements, and mapping quality;
- compatibility profiles that preserve earlier output behavior.

## Why it matters for GS1

GS1 already provides trusted identifiers, data models, exchange standards, and
web vocabularies. This project makes the relationship between those building
blocks visible in running software. It can support discussion about how product
data shared through established GS1 processes can also serve web, search, data
space, Digital Product Passport, and AI use cases.

## Which standards come together

- **GDSN-like XML** supplies structured product data for exchange.
- **BMS IDs and official XPath references** identify and locate source fields.
- **GTIN and GPC** provide product identity and classification.
- **GS1 Web Vocabulary** provides semantic properties for web-native output.
- **JSON-LD** expresses that output as linked, machine-readable data.
- **GS1 Digital Link-style URIs** give products a resolvable identity pattern.
- **The mapping catalog** records evidence, confidence, scope, and review needs.

## Why it matters for AI and machine-readable product data

AI systems are more useful when product facts are explicit, structured, and
grounded in shared identifiers and vocabularies. JSON-LD makes relationships
and meanings clearer than free text alone. The mapping catalog also makes it
possible to inspect how an output claim was derived rather than treating the
conversion as an opaque step.

This improves the basis for retrieval, comparison, product discovery, agent
workflows, and validation. It does not remove the need to verify provenance,
authority, currency, or the truth of individual claims.

## Current status up to v0.5.0

The released profiles cover core product data, food information,
certification-related fields, and experimental document links. v0.4.0 added
catalog and YAML quality checks with JSON and Excel reporting. v0.5.0 added
robustness testing against multiple synthetic GDSN-like sample shapes.

The CLI and Streamlit interface use the same converter package. Validation,
mapping, and unmapped-field reports expose limitations instead of hiding them.
The repository includes automated tests, examples, release notes, and
strategic and conformance reviews.

## What it does not claim yet

The project does not claim complete GDSN coverage, full GDSN XSD validation,
or complete GS1 Web Vocabulary conformance. It does not verify certificates,
dereference links, establish the truth of source claims, or define an approved
GS1 governance model. Document-link and DPP modelling remain experimental.

The most accurate description is **GS1 Web Vocabulary aligned and BMS/XPath
traceable**, within the scope of the selected mapping profile.

## Recommended next discussion points

1. Which mappings should GS1 review and recognize as authoritative?
2. What evidence and governance are required for conformance claims?
3. How should document, certification, and DPP links be modelled?
4. Which provenance metadata should accompany generated JSON-LD?
5. Which real-world sample sets can be used for controlled validation?
6. Where could this bridge add value in GS1 services, data spaces, or AI
   initiatives?
