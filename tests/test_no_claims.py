"""No-claim tests (v0.15.0 onward).

The app must never claim official GS1 validation, EU DPP compliance, or
production readiness. Claim-shaped phrases may appear only in negated form
("not official GS1 validation", "No production compliance", ...). These tests
scan the rendered app text on the compliance-sensitive routes.
"""

from __future__ import annotations

import re

from streamlit.testing.v1 import AppTest

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
REQUIRED_NEGATIONS = (
    "no official gs1 validation",
    "no production compliance",
)


def _rendered_text(app: AppTest) -> str:
    parts: list[str] = []
    parts.extend(markdown.value for markdown in app.markdown)
    parts.extend(warning.value for warning in app.warning)
    parts.extend(info.value for info in app.info)
    parts.extend(caption.value for caption in app.caption)
    return "\n".join(str(part) for part in parts)


def _assert_no_positive_claims(text: str) -> None:
    lowered = text.lower()
    for phrase in CLAIM_PHRASES:
        for match in re.finditer(re.escape(phrase.lower()), lowered):
            context = lowered[max(0, match.start() - 80) : match.start()]
            assert any(negator in context for negator in NEGATORS), (
                f"Claim phrase {phrase!r} appears without a negation. "
                f"Context: ...{context[-60:]}{phrase}"
            )


def _open_workflow(app: AppTest, workflow_key: str) -> None:
    """Direct navigation (v0.30.0): open one of the five workflows."""
    for button in app.button:
        if getattr(button, "key", None) == f"workflow_mode_{workflow_key}":
            button.click().run(timeout=20)
            return
    raise AssertionError(f"workflow button workflow_mode_{workflow_key} not found")


def test_landing_page_makes_no_positive_claims() -> None:
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    text = _rendered_text(app)
    _assert_no_positive_claims(text)
    lowered = text.lower()
    for required in REQUIRED_NEGATIONS:
        assert required in lowered, f"Required negation missing: {required!r}"


def test_product_passport_workflow_makes_no_positive_claims() -> None:
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    _open_workflow(app, "product_passport")
    _assert_no_positive_claims(_rendered_text(app))


def test_mapping_governance_workflow_makes_no_positive_claims() -> None:
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    _open_workflow(app, "governance")
    _assert_no_positive_claims(_rendered_text(app))
