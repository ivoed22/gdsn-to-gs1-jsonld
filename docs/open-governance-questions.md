# Open Governance Questions

This project makes governance questions visible by turning mapping decisions
into executable configuration, catalog rows, quality warnings, and observable
JSON-LD output.

## Mapping authority

- When is a technical mapping considered an official GS1 mapping?
- Who approves mappings between GDSN BMS IDs and GS1 Web Vocabulary
  properties?
- Who maintains mappings when GDSN, BMS IDs, or Web Vocabulary terms change?
- What evidence and review are required to promote a candidate or experimental
  mapping?
- Should executable YAML be derived from an authoritative catalog, or should
  both artifacts remain independently reviewed?

## Versioning

- How should GDSN versions, Web Vocabulary versions, mapping catalog versions,
  and converter versions be aligned?
- How should breaking mapping changes be communicated?
- How should historical mappings be preserved?
- Which version identifiers should be included in generated output and
  reports?
- How long should older mapping profiles remain supported?

## Web Vocabulary conformance

- When may output be called Web Vocabulary conformant?
- When should it only be called Web Vocabulary aligned?
- How should missing or experimental Web Vocabulary terms be handled?
- Is use of schema.org alongside GS1 Web Vocabulary acceptable under a defined
  conformance profile?
- Should conformance be assessed per document, mapping profile, property, or
  release?

## Document and DPP modelling

- Should DPP-like documents be represented using GS1 Web Vocabulary terms,
  GS1 Digital Link link types, schema.org, DCAT/DPROD, or another pattern?
- What is the preferred model for certification document links?
- Should document metadata live inside product JSON-LD or behind link
  relations?
- Which relation should connect a product to a generic referenced document?
- How should `ReferencedFileTypeCode` be represented when code values exist
  but a corresponding Web Vocabulary property is not validated?

## Certification and trust

- Is GS1 only representing certification claims, or also supporting
  verification?
- How should certification issuers, schemes, and documents be identified?
- Should Verifiable Credentials be supported later?
- What is the role of registries or issuer identifiers?
- How should a certification organization GLN be distinguished from agency
  text or an agency URL?
- When is a certification identification a value, a URI, or both?

## Sector governance

- Which mappings are global and which are sector-specific?
- How should FMCG, Healthcare, DIY, Textile/DPP, and other sector differences
  be managed?
- Can one generic mapping profile be sufficient, or are sector profiles
  needed?
- Who owns cross-sector canonical fields and code-list interpretation?
- How should sector extensions avoid fragmenting shared product semantics?

## Conformance claims

The main governance question is not whether conversion is technically
possible, but when a mapping can be considered authoritative, maintained and
conformant with GS1 standards.

Until that threshold is defined, project documentation should distinguish:

- technically functioning mappings
- BMS/XPath-traceable mappings
- Web Vocabulary-validated mappings
- candidate mappings requiring review
- explicitly experimental mappings

This distinction enables useful implementation work without turning project
choices into implied standards decisions.
