"""Tests for the GS1 Digital Link URI form + local QR (v0.34.0).

The important properties: the URI form matches what the converter
already emits as ``@id``; the QR is rendered locally, deterministically,
with no external resource references; and nothing claims resolvability.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from gdsn_to_gs1_jsonld.digital_link import (
    DIGITAL_LINK_CAVEAT,
    DigitalLinkError,
    build_digital_link_uri,
    digital_link_qr_svg,
)


def test_uri_form_matches_converter_id_form():
    # Same form the converter's jsonld_builder emits as @id for the
    # example fixture (asserted elsewhere against the rendered app).
    assert (
        build_digital_link_uri("08712345678906")
        == "https://id.gs1.org/01/08712345678906"
    )
    assert build_digital_link_uri(" 08712345678906 ") == (
        "https://id.gs1.org/01/08712345678906"
    )


def test_unusable_gtin_raises():
    for bad in ("", "   ", None, "not-a-gtin", "12345 678"):
        with pytest.raises(DigitalLinkError):
            build_digital_link_uri(bad)  # type: ignore[arg-type]


def test_qr_svg_is_wellformed_deterministic_and_selfcontained():
    uri = build_digital_link_uri("08712345678906")

    first = digital_link_qr_svg(uri)
    second = digital_link_qr_svg(uri)

    assert first == second  # deterministic
    root = ET.fromstring(first)  # well-formed XML
    assert root.tag.endswith("svg")
    # No external resource references anywhere in the SVG (the xmlns
    # namespace identifier is not a fetched resource).
    for element in root.iter():
        for name, value in element.attrib.items():
            assert not (
                name in {"href", "src"} and value.startswith(("http://", "https://"))
            ), f"external reference in QR SVG: {name}={value}"


def test_caveat_never_claims_resolvability():
    lowered = DIGITAL_LINK_CAVEAT.lower()
    assert "does not check or claim" in lowered
    for word in ("registered", "resolvable", "live"):
        assert word in lowered  # explicitly negated, not merely omitted
