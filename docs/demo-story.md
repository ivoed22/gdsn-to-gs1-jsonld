# Demo Story

## Problem

GS1 product data is rich, structured, and widely exchanged, but its XML
exchange form is not always directly usable by AI systems, agents, search
engines, or web-native applications. Those consumers benefit from explicit
semantics, stable identifiers, and a compact representation of product facts.

## Input

The demo starts with GDSN-like XML containing familiar product information such
as GTIN, product name, brand, net content, ingredients, allergens, nutrients,
certification data, or document references. The converter processes the XML in
memory and applies a selected versioned mapping profile.

## Traceability layer

The mapping is not just a list of renamed fields. BMS IDs and official XPath
references identify the source concepts and locations. A mapping catalog
records canonical fields, target properties, confidence, scope, experimental
status, and Web Vocabulary review findings.

This layer makes each transformation open to standards review.

## Conversion

Selected XML values first enter a canonical product model. That model separates
source extraction from target serialization, so XML details do not leak into
the user interface and output rules remain testable and reusable.

## Output

The result is JSON-LD using GS1 Web Vocabulary properties. The GTIN is retained
as a product identifier and is also used to form a GS1 Digital Link-style
product `@id`. Product facts become explicit properties that web-native systems
can process without reverse-engineering the source XML structure.

The output is aligned with the selected GS1 vocabulary terms. It should not be
presented as proof of complete Web Vocabulary or GDSN conformance.

## Diagnostics

The demo also exposes what the converter knows and what it does not:

- the validation report records conversion-level checks;
- the unmapped report identifies populated XML outside the selected profile;
- the mapping report shows which rules produced the output;
- catalog and YAML quality checks surface coverage, experimental mappings,
  missing evidence, and vocabulary review needs.

These reports turn limitations into reviewable information.

## Strategic value

The project demonstrates a standards-traceable path to AI-ready product data.
It connects existing GS1 exchange assets with linked data and creates a basis
for product discovery, retrieval, comparison, agent workflows, and data-space
interoperability. The value is the bridge and its traceability, not simply a
change of file format.

## Open questions

Standards and governance decisions remain necessary:

- What qualifies an output as conformant rather than aligned?
- Who approves mappings and confidence levels?
- How should generic documents, certification evidence, and DPP links be
  represented?
- Which provenance should travel with each generated claim?
- How should mappings evolve without breaking earlier profiles?

## Five-minute demo script

### 0:00-0:40 - Set the problem

**Say:** "GS1 product data already contains valuable, structured facts. The
challenge is that exchange-oriented XML is not the form most web, search, and
AI systems expect. This project tests a practical bridge into semantically
explicit JSON-LD."

**Speaker notes:** Show the repository or Streamlit landing page. Emphasize
reuse of GS1 assets, not replacement of GDSN.

### 0:40-1:20 - Show the input

**Say:** "Here is a small GDSN-like product message. It contains a GTIN,
description, brand, net content, and, in richer profiles, food and certification
information."

**Speaker notes:** Open one sample XML file. Point to two or three readable
values only; do not spend time explaining XML namespaces.

### 1:20-2:00 - Explain traceability

**Say:** "Before conversion, each rule is connected to a canonical field and
documented in a mapping catalog. BMS IDs and XPath references provide the route
back to the source definition. Confidence and experimental status remain
visible."

**Speaker notes:** Briefly show the mapping catalog or a quality report. The
important point is reviewability, not the number of rows.

### 2:00-2:50 - Run the conversion

**Say:** "The converter reads the XML in memory, applies the selected versioned
profile, and builds a canonical product model. The CLI and Streamlit interface
both call the same converter package."

**Speaker notes:** Run the conversion or click **Convert to JSON-LD**. Select
the latest relevant profile. Mention that earlier profiles remain available for
output compatibility.

### 2:50-3:40 - Show the output

**Say:** "The result uses GS1 Web Vocabulary properties in JSON-LD. The product
gets a GS1 Digital Link-style `@id`, while its facts become explicit,
machine-readable properties."

**Speaker notes:** Highlight `@id`, `gs1:gtin`, one descriptive property, and
`gs1:netContent`. Avoid claiming full conformance.

### 3:40-4:25 - Show diagnostics

**Say:** "A credible bridge must also show its limits. Validation, mapping, and
unmapped-field reports reveal what was converted, what needs review, and what
the selected profile does not cover. Catalog checks compare technical YAML
with the standards evidence."

**Speaker notes:** Open one report. Explain that warnings support standards
review and are not silently discarded.

### 4:25-5:00 - Close with the strategic question

**Say:** "The demonstration is not that XML can become JSON. It is that GS1
product data can become web-native and AI-ready while remaining traceable to
GS1 identifiers, source definitions, and mapping decisions. The next question
is which mappings, provenance rules, and governance model GS1 should endorse."

**Speaker notes:** End on the one-pager's discussion points. Invite review of
conformance language, document links, DPP modelling, and mapping governance.
