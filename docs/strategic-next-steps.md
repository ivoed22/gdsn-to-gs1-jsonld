# Strategic Next Steps

After v0.5.0, the project can create the most value through two complementary
tracks: explaining the demonstrated strategic bridge and hardening the
standards claims behind it.

## Track A — Positioning and demo

### Goal

Use the tool to explain how GS1 product data can become machine-readable
structured data for AI and digital ecosystems.

The central demonstration is a traceable before-and-after story:

```text
GDSN XML -> governed mapping -> GS1 Web Vocabulary-aligned JSON-LD
```

### Suggested outputs

- a concise demo story focused on product identity, semantics, and provenance
- an internal presentation showing the pipeline and current evidence
- stakeholder discussion with Web Vocabulary, GDSN, DPP, Digital Link, and
  data-spaces colleagues
- an example before/after walkthrough from GDSN XML to JSON-LD
- a machine-readable product example consumed by search, an AI assistant, or
  an agent
- a clear explanation of which mappings are validated and which remain
  experimental

### Questions to test with stakeholders

- Does the pipeline express the relationship between existing GS1 assets
  clearly?
- Which use cases best demonstrate value without overstating conformance?
- What evidence would decision-makers need before supporting an official
  mapping initiative?

## Track D — Web Vocabulary conformance hardening

### Goal

Reduce uncertainty around Web Vocabulary terms and document/DPP modelling.

### Suggested outputs

- routine Web Vocabulary and linktype snapshot monitoring
- repeatable mapping-catalog revalidation reports
- a resolved warning list with decisions, owners, and evidence
- a proposed Web Vocabulary term review for missing or replacement properties
- a document-link modelling decision
- an experimental mapping policy
- a conformance wording policy
- a controlled status vocabulary for official, candidate, review, and
  experimental mappings
- explicit version alignment between GDSN, Web Vocabulary, mapping catalog,
  and converter profiles

### Priority decisions

1. Confirm nutrient modelling using validated Web Vocabulary patterns.
2. Select the product image property or relation.
3. Decide the generic document and certification-document relationship model.
4. Clarify `ReferencedFileTypeCode` representation.
5. Clarify certification identifiers and issuer modelling.
6. Define who can approve and maintain mappings.

## Recommended sequencing

Do not start with:

- a full DPP model
- Verifiable Credentials
- DCAT/DPROD
- resolver integration

until the Web Vocabulary and document-link modelling questions are clearer.

Those technologies may become valuable later, but starting there would add
architectural layers before the semantic relationship between product,
certification, and document resources is governed. First establish the mapping
and conformance foundation; then extend into verification, discovery, and DPP
ecosystems.

Version 0.6.0 provides the monitoring and revalidation foundation for this
track. Its reports should inform standards review; they must not be used to
silently rewrite semantic mappings.

Version 0.6.1 removes three reporting false positives and leaves 12 explicit,
non-blocking review items. Those items form a practical standards-review
backlog rather than a reason to weaken report severity or change mappings
automatically.

## Combined outcome

Track A creates understanding and stakeholder momentum. Track D turns project
evidence into clearer standards decisions. Together they move the project from
a successful demonstrator toward an authoritative, maintainable mapping
approach without prematurely expanding implementation scope.
