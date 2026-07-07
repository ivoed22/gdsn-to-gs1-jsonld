"""Tests for the self-contained HTML product report (v0.32.0 Report Center).

The report is an outward-facing artifact, so the important properties are:
fully offline (no external resource references), deterministic, honest
(readiness rendered verbatim incl. the not-yet-assessed DPP dimension),
and no-claims-safe (every restricted phrase appears only negated).
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path

from gdsn_to_gs1_jsonld.codelist_registry import load_codelist_registry
from gdsn_to_gs1_jsonld.converter import convert_xml_to_jsonld
from gdsn_to_gs1_jsonld.report import build_product_report_html, product_report_bytes

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_XML = ROOT / "examples" / "input" / "example_product.xml"
MAPPING_REGISTRY = ROOT / "mapping" / "mapping_registry.yaml"
CODELIST_REGISTRY_JSON = (
    ROOT / "reference_data" / "normalized" / "gdsn_codelists_r3_1_36.json"
)

# Same restricted phrases + negators as tests/test_no_claims.py, applied to
# the report text.
CLAIM_PHRASES = (
    "official GS1 validation",
    "officially validated",
    "EU DPP compliance",
    "EU DPP compliant",
    "EU DPP regulatory compliance",
    "production-ready",
    "production ready",
    "production compliance",
)
NEGATORS = ("not ", "no ", "never ", "without ", "nor ")


class _StructureParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: list[str] = []
        self.errors: list[str] = []

    def handle_starttag(self, tag, attrs):  # noqa: ANN001
        self.tags.append(tag)
        for name, value in attrs:
            if name in {"src", "href"} and value and value.startswith(
                ("http://", "https://", "//")
            ):
                self.errors.append(f"external resource reference: {name}={value}")

    def handle_startendtag(self, tag, attrs):  # noqa: ANN001
        self.handle_starttag(tag, attrs)


def _real_report() -> str:
    registry = load_codelist_registry(CODELIST_REGISTRY_JSON)
    result = convert_xml_to_jsonld(
        EXAMPLE_XML.read_bytes(),
        MAPPING_REGISTRY,
        write_files=False,
        codelist_registry=registry,
    )
    return build_product_report_html(
        jsonld_data=result.jsonld_data,
        validation_report=result.validation_report,
        mapping_report_rows=result.mapping_report_rows,
        unmapped_fields=result.unmapped_fields,
        codelist_validation=result.codelist_validation,
    )


def test_report_contains_identity_readiness_and_evidence():
    html = _real_report()

    assert "08712345678906" in html  # example fixture GTIN
    assert "attention points" in html  # readiness level (2 unknown codelist values)
    assert "not_yet_assessed_pending_crosswalk" in html
    assert "DPP readiness" in html
    assert "Mapping evidence summary" in html
    assert "Codelist validation counts" in html
    assert "Generated GS1 Web Vocabulary JSON-LD" in html


def test_report_is_selfcontained_and_parseable():
    """No scripts and no external stylesheet/image/font references — the
    file must render identically fully offline. URLs inside the product's
    own data values (escaped inside <pre>) are fine and expected."""
    html = _real_report()

    parser = _StructureParser()
    parser.feed(html)
    assert parser.errors == []
    assert "script" not in parser.tags
    assert "link" not in parser.tags
    assert "img" not in parser.tags
    assert "style" in parser.tags and "footer" in parser.tags


def test_report_negates_every_restricted_claim_phrase():
    lowered = _real_report().lower()
    for phrase in CLAIM_PHRASES:
        for match in re.finditer(re.escape(phrase.lower()), lowered):
            context = lowered[max(0, match.start() - 80) : match.start()]
            assert any(negator in context for negator in NEGATORS), (
                f"claim phrase {phrase!r} appears without negation"
            )
    # The governance negations are actually present, not just vacuously.
    assert "not official gs1 validation" in lowered
    assert "no production compliance" in lowered


def test_report_is_deterministic_and_bytes_roundtrip():
    first = _real_report()
    second = _real_report()
    assert first == second
    assert product_report_bytes(first) == first.encode("utf-8")


def test_report_embeds_digital_link_uri_and_qr_with_caveat():
    """v0.34.0: the report carries the Digital Link URI form and an
    inline QR SVG (self-contained), plus the no-resolution caveat."""
    html = _real_report()

    assert "GS1 Digital Link" in html
    assert "https://id.gs1.org/01/08712345678906" in html
    assert "<svg" in html and "</svg>" in html
    assert "does not check or claim" in html


def test_report_without_codelist_registry_says_not_evaluated():
    result = convert_xml_to_jsonld(
        EXAMPLE_XML.read_bytes(), MAPPING_REGISTRY, write_files=False
    )
    html = build_product_report_html(
        jsonld_data=result.jsonld_data,
        validation_report=result.validation_report,
        mapping_report_rows=result.mapping_report_rows,
        unmapped_fields=result.unmapped_fields,
        codelist_validation=result.codelist_validation,
    )
    assert "not_evaluated" in html
    assert "Not evaluated in this conversion." in html
