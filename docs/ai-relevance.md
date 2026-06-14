# Why This Matters for AI

## AI needs structured, trustworthy, explicit data

AI can extract facts from documents and web pages, but extraction alone does
not establish what a value means, which product it describes, or whether two
publishers use the same concept. Structured product data reduces that
ambiguity. Trustworthy use also requires identifiers, provenance, validation,
and an accountable source.

## JSON-LD makes meaning easier for machines to interpret

JSON-LD combines a familiar machine-readable format with linked-data semantics.
Properties can refer to shared vocabularies, and entities can have stable web
identifiers. Compared with unstructured prose, this gives search systems,
knowledge graphs, retrieval pipelines, and agents a clearer representation of
product facts and relationships.

JSON-LD does not make an inaccurate claim true. It makes the claim more
explicit and therefore easier to process, compare, validate, and challenge.

## GS1 identifiers and vocabularies provide grounding

GTIN gives an AI system a product identity that is more precise than a product
name. GS1 Web Vocabulary properties provide shared semantic labels for product
facts. GDSN, GPC, BMS definitions, and XPath references add domain structure
and a route back to the exchange standard.

Together, these assets can help an AI system answer:

- Which product does this fact concern?
- What does the property mean?
- Which unit, language, or classification applies?
- Which source field and mapping decision produced the value?

## Mapping catalogs provide traceability

The project's mapping catalog records the relationship between source
concepts, canonical fields, and target JSON-LD properties. It can also capture
confidence, mapping status, BMS IDs, XPath evidence, experimental status, and
Web Vocabulary review findings.

For AI applications, that record is valuable because it makes transformation
logic inspectable. A reviewer can distinguish a well-supported mapping from an
experimental or unresolved one, and a system can use those distinctions when
ranking or filtering data.

## AI should not blindly trust every claim

A standards-based identifier or JSON-LD property is not proof that the
underlying statement is current, authorized, or correct. The converter does
not verify certificates, dereference every document, validate every GDSN rule,
or establish who is accountable for a source claim.

AI systems should retain uncertainty and avoid presenting experimental
mappings as established facts. High-impact decisions may require source
verification or human review.

## Governance and provenance remain essential

Useful AI-ready product data needs more than a serialization format. A
production approach should define:

- who owns and approves mappings;
- which source supplied each claim and when;
- how mapping versions and corrections are managed;
- what conformance level is asserted;
- how certifications and documents are verified;
- which claims require human or rules-based review.

The converter demonstrates a technical bridge. Its strategic opportunity is to
pair that bridge with GS1 governance, trusted identifiers, and transparent
provenance so machine-readable product data can be used responsibly.
