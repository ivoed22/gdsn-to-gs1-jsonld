# From GDSN XML to GS1 Web Vocabulary JSON-LD

## What does this tool prove?

The tool demonstrates that existing GS1 product data can be transformed from
GDSN XML into machine-readable, semantically structured JSON-LD using GS1 Web
Vocabulary.

Its value is not generic XML-to-JSON conversion. A generic conversion can
preserve syntax while losing the standards meaning, provenance, and governance
needed for dependable reuse. This project demonstrates a standards-traceable
pipeline:

```text
GDSN XML
-> BMS ID / XPath
-> mapping catalog
-> canonical product model
-> GS1 Web Vocabulary JSON-LD
-> machine-readable structured data
```

Each layer has a distinct role. GDSN supplies exchanged product data, BMS IDs
and XPath expressions identify source semantics, the mapping catalog records
mapping decisions, the canonical model separates extraction from publication,
and JSON-LD expresses reusable web-native meaning.

That pipeline is relevant to:

- AI systems that need structured product context rather than document text
- agents that need stable identifiers and typed properties
- search and discovery across heterogeneous product-data sources
- Digital Product Passport exploration
- data spaces that require interoperable semantic exchange
- automated product-data interpretation and validation

## Why is this relevant for GS1?

GS1 already provides global building blocks for product identification,
product data exchange, classification, and semantic product description. This
tool shows how those assets can be connected into an AI-ready and web-native
structured data layer.

The demonstrator brings together:

- GTIN for globally recognizable product identity
- GDSN for product-data exchange
- BMS IDs and XPath expressions for source traceability
- GS1 Web Vocabulary for semantic product description
- GS1 Digital Link URI patterns for web-addressable product identifiers
- certification information for structured claims
- a mapping catalog for review, versioning, and governance

GS1 does not need to start from scratch for AI-ready product data. Many of the
required building blocks already exist. The challenge is to connect them in a
machine-readable, semantically consistent and governable way.

The project makes that challenge concrete. It shows both where existing
standards connect cleanly and where authoritative mapping or modelling
decisions are still required.

## Standards and models

| Standard / model | Role in this tool | Current maturity in the project |
|---|---|---|
| GDSN | Source product-data structures and business attributes | Focused realistic subset; not full module or XSD coverage |
| GDSN BMS ID / XPath | Traceability from mapped fields to GDSN definitions and locations | Strong for catalogued fields; some source mechanisms still need review |
| GTIN | Product identity and basis for the product URI | High confidence and regression tested |
| GPC | Product classification code | High-confidence direct mapping |
| GS1 Web Vocabulary | Semantic target for product properties and objects | Strong for core fields; mixed for nutrients, images, and documents |
| JSON-LD / Linked Data | Machine-readable serialization with typed properties and contexts | Implemented and stable for the current profiles |
| GS1 Digital Link URI pattern | Web-addressable `@id` pattern based on GTIN | Implemented as `https://id.gs1.org/01/{GTIN}`; no resolver calls |
| Certification information model | Structured certification details, dates, identifiers, and values | Useful demonstrator with strong core terms and some semantic review items |
| Referenced file information | Source for product, certification, and DPP-like document links | BMS/XPath traceable; target relationship remains experimental |
| schema.org | Fallback vocabulary for URLs and document metadata | Deliberate external vocabulary use; not GS1 Web Vocabulary conformance |
| Mapping catalog | Governance layer connecting source, canonical, and target semantics | Implemented with automated quality checks; authority remains project-level |

## What does the tool not prove yet?

The tool is a focused demonstrator and implementation testbed. It does not:

- prove full GDSN XSD validity
- verify certificates or certification claims
- dereference URLs or test whether linked resources exist
- prove full GS1 Web Vocabulary conformance for every mapping
- implement Verifiable Credentials
- implement a full Digital Product Passport model
- solve mapping ownership, approval, maintenance, or version governance by
  itself

The strongest current claim is that the pipeline is technically demonstrated,
standards traceable for catalogued mappings, and Web Vocabulary aligned where
the target terms have been validated. Authoritative conformance requires the
governance decisions described in
[Open Governance Questions](open-governance-questions.md).
