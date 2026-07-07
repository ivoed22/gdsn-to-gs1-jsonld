"""GS1 Digital Link URI form + locally rendered QR (v0.34.0).

Constructs the GS1 Digital Link URI *form* for a GTIN
(``https://id.gs1.org/01/{gtin}`` — the same form the converter already
emits as ``@id``) and renders it as a QR code SVG, entirely offline.

Honesty constraint: constructing this URI is pure string formatting.
Whether it actually *resolves* anywhere is a completely separate matter —
nothing here checks, claims, or implies that the link is registered,
resolvable, or live, and no code in this module performs any network
call. UI text built on this module must present the value as "the GS1
Digital Link URI form for this GTIN", nothing stronger.
"""

from __future__ import annotations

DIGITAL_LINK_BASE = "https://id.gs1.org"

# Wording reused by the Streamlit panel and the HTML report so the
# no-resolution caveat cannot drift between surfaces.
DIGITAL_LINK_CAVEAT = (
    "GS1 Digital Link URI form constructed offline from the GTIN. This "
    "does not check or claim that the link is registered, resolvable, or "
    "live."
)


class DigitalLinkError(ValueError):
    """Raised for an unusable GTIN or a missing QR rendering dependency."""


def build_digital_link_uri(gtin: str) -> str:
    """Return the GS1 Digital Link URI form for *gtin*.

    Same ``https://id.gs1.org/01/{gtin}`` form the converter's
    ``jsonld_builder`` emits as ``@id``. Digits-only validation keeps
    obviously broken input out of QR codes; full GTIN check-digit
    validation remains the converter/validator's job, not this helper's.
    """
    cleaned = str(gtin or "").strip()
    if not cleaned or not cleaned.isdigit():
        raise DigitalLinkError(
            f"GTIN must be a non-empty digit string, got {gtin!r}."
        )
    return f"{DIGITAL_LINK_BASE}/01/{cleaned}"


def digital_link_qr_svg(uri: str) -> str:
    """Render *uri* as a QR code SVG string, locally.

    Uses ``qrcode``'s SVG path factory, which needs no raster imaging
    dependency. Deterministic: the same URI always produces the same SVG.
    """
    try:
        import qrcode
        import qrcode.image.svg
    except ImportError as exc:  # pragma: no cover - declared dependency
        raise DigitalLinkError(
            "The 'qrcode' package is required for QR rendering. Install "
            "project dependencies (pip install -e .)."
        ) from exc

    qr = qrcode.QRCode(
        image_factory=qrcode.image.svg.SvgPathImage,
        box_size=10,
        border=2,
    )
    qr.add_data(uri)
    qr.make(fit=True)
    return qr.make_image().to_string(encoding="unicode")
