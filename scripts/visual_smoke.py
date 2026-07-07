"""Browser-based visual smoke test (v0.17.0).

Boots the Streamlit app headless, walks the critical routes/workflows with
Playwright, and asserts layout/content invariants that
`streamlit.testing.v1.AppTest` cannot see (rendered CSS, viewport overflow,
button contrast, screenshots). No app behavior changes; this is read-only
browsing plus assertions.

Deliberately not part of the default `pytest` run: it needs Playwright and a
Chromium download, so it is a separate, documented local/CI step (see
docs/visual-smoke.md), non-blocking in CI until stable.

Usage:
    python scripts/visual_smoke.py [--output-dir tests/visual/baselines] [--port 8577]
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "tests" / "visual" / "baselines"
DEFAULT_PORT = 8577
VIEWPORT = {"width": 1280, "height": 900}

# Same claim phrases/negation check as tests/test_no_claims.py, applied to
# rendered page text instead of AppTest markdown.
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

NAV_BUTTON_SELECTOR = (
    "button[data-testid='stBaseButton-primary'], "
    "button[data-testid='stBaseButton-secondary']"
)

# (workflow_index, screen_name) for every one of the five workflows,
# reached through direct navigation (v0.30.0). Indexes follow
# app/workflow_shared.py WORKFLOW_MODES order and must be kept in sync if
# that structure changes.
SCREENS = [
    (0, "convert_gdsn_xml"),
    (1, "explore_webvoc"),
    (2, "create_jsonld_prototype"),
    (3, "mapping_governance"),
    (4, "product_passport"),
]


class SmokeFailure(Exception):
    pass


def _wait_for_server(url: str, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return
        except OSError as exc:
            last_error = exc
        time.sleep(0.5)
    raise SmokeFailure(f"Streamlit server did not become ready at {url}: {last_error}")


def _nav_buttons(page):
    return page.locator(NAV_BUTTON_SELECTOR).filter(has_text=re.compile(r"^(Open|Active)$"))


def _click_nav_button_if_open(page, index: int, screen: str, failures: list[str]) -> None:
    """Click the nth nav button unless it's already the active (disabled) one.

    Streamlit re-renders the whole nav row on every click, so the locator can
    go stale between an is_disabled() check and the click; re-fetch a fresh
    locator on each attempt instead of caching one across the check-and-click.
    """
    for attempt in range(5):
        try:
            button = _nav_buttons(page).nth(index)
            if button.inner_text(timeout=5000).strip() != "Active":
                button.click(timeout=5000)
            page.wait_for_timeout(1200)
            return
        except Exception:  # noqa: BLE001 - retry on transient re-render races
            if attempt == 4:
                failures.append(f"[{screen}] could not click nav button at index {index}")
                return
            page.wait_for_timeout(500)


def _assert_no_positive_claims(text: str, screen: str, failures: list[str]) -> None:
    lowered = text.lower()
    for phrase in CLAIM_PHRASES:
        for match in re.finditer(re.escape(phrase.lower()), lowered):
            context = lowered[max(0, match.start() - 80) : match.start()]
            if not any(negator in context for negator in NEGATORS):
                failures.append(
                    f"[{screen}] claim phrase {phrase!r} appears without negation"
                )


def _assert_no_horizontal_overflow(page, screen: str, failures: list[str]) -> None:
    overflow = page.evaluate(
        "document.documentElement.scrollWidth - document.documentElement.clientWidth"
    )
    if overflow > 1:
        failures.append(f"[{screen}] horizontal overflow of {overflow}px at 1280px viewport")


def _assert_active_button_readable(page, screen: str, failures: list[str]) -> None:
    active_buttons = page.locator(NAV_BUTTON_SELECTOR).filter(has_text="Active")
    if active_buttons.count() == 0:
        failures.append(f"[{screen}] no active route/workflow button found")
        return
    for i in range(active_buttons.count()):
        try:
            styles = active_buttons.nth(i).evaluate(
                "el => { const s = getComputedStyle(el); "
                "return {color: s.color, background: s.backgroundColor, opacity: s.opacity}; }",
                timeout=5000,
            )
            opacity = float(styles["opacity"])
        except Exception:  # noqa: BLE001 - transient re-render race, not a real check failure
            continue
        if styles["color"] == styles["background"]:
            failures.append(f"[{screen}] active button text color matches background")
        if opacity == 0.0:
            failures.append(f"[{screen}] active button is invisible (opacity 0)")


def _assert_version_visible(page, expected_version: str, screen: str, failures: list[str]) -> None:
    body_text = page.locator("body").inner_text()
    if f"App version: {expected_version}" not in body_text:
        failures.append(f"[{screen}] version string 'App version: {expected_version}' not visible")


def _assert_five_workflows_visible(page, screen: str, failures: list[str]) -> None:
    body_text = page.locator("body").inner_text()
    for workflow_title in (
        "Convert GDSN XML",
        "Explore GS1 Web Vocabulary",
        "Create JSON-LD Prototype",
        "Mapping Governance",
        "Product Passport",
    ):
        if workflow_title not in body_text:
            failures.append(f"[{screen}] workflow card {workflow_title!r} not visible")


def run_visual_smoke(output_dir: Path, port: int) -> list[str]:
    sys.path.insert(0, str(REPO_ROOT))
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from app.ui import APP_VERSION  # noqa: PLC0415 (import after sys.path setup)

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise SmokeFailure(
            "playwright is not installed. Install the 'visual' extra: "
            "pip install -e '.[visual]' && playwright install --with-deps chromium"
        ) from exc

    output_dir.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    url = f"http://127.0.0.1:{port}"

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "app/streamlit_app.py",
            "--server.headless",
            "true",
            "--server.port",
            str(port),
            "--server.address",
            "127.0.0.1",
        ],
        cwd=str(REPO_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_for_server(url)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport=VIEWPORT)
            page.goto(url, wait_until="networkidle", timeout=30000)
            page.wait_for_selector(NAV_BUTTON_SELECTOR, timeout=30000)
            page.wait_for_timeout(1500)

            # Screen 0: landing page (default workflow, no clicks yet).
            screen = "landing_page"
            _assert_version_visible(page, APP_VERSION, screen, failures)
            _assert_five_workflows_visible(page, screen, failures)
            _assert_no_horizontal_overflow(page, screen, failures)
            _assert_active_button_readable(page, screen, failures)
            _assert_no_positive_claims(page.locator("body").inner_text(), screen, failures)
            page.screenshot(path=str(output_dir / f"{screen}.png"), full_page=True)

            for workflow_index, screen in SCREENS:
                _click_nav_button_if_open(page, workflow_index, screen, failures)

                if screen == "mapping_governance":
                    # Drive one generation so lane/status badges render, the
                    # state this workflow spends most of its time in.
                    try:
                        # Streamlit's selectbox is a BaseWeb combobox, not a
                        # native <select>: open it, type to filter, and click
                        # the option inside its virtual dropdown container.
                        property_select = page.get_by_role(
                            "combobox", name=re.compile("WebVoc property")
                        )
                        property_select.click()
                        page.wait_for_timeout(300)
                        property_select.type("gs1:gtin", delay=20)
                        page.wait_for_timeout(400)
                        page.get_by_test_id("stSelectboxVirtualDropdown").get_by_text(
                            "gs1:gtin", exact=True
                        ).click()
                        page.wait_for_timeout(300)
                        page.get_by_role("button", name="Generate Candidates").click()
                        page.wait_for_timeout(2000)
                    except Exception as exc:  # noqa: BLE001 - smoke test, report and continue
                        failures.append(f"[{screen}] could not drive candidate generation: {exc}")

                body_text = page.locator("body").inner_text()
                _assert_no_horizontal_overflow(page, screen, failures)
                _assert_active_button_readable(page, screen, failures)
                _assert_no_positive_claims(body_text, screen, failures)

                # Every workflow carries at least one governance/warning
                # note (prototype/review-only, structural-only, etc.).
                # Retry briefly: heavier workflows (e.g. Explore's dataset
                # build on first render) can still be streaming content when
                # the click settles.
                warnings_present = False
                for _ in range(6):
                    if page.locator("[data-testid='stAlert']").count() > 0:
                        warnings_present = True
                        break
                    page.wait_for_timeout(500)
                if not warnings_present:
                    failures.append(f"[{screen}] no warning/info alert visible")

                page.screenshot(path=str(output_dir / f"{screen}.png"), full_page=True)

            browser.close()
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for screenshots (default: tests/visual/baselines).",
    )
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    try:
        failures = run_visual_smoke(args.output_dir, args.port)
    except SmokeFailure as exc:
        print(f"Visual smoke setup failed: {exc}", file=sys.stderr)
        return 2

    if failures:
        print(f"Visual smoke FAILED ({len(failures)} issue(s)):", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1

    print(f"Visual smoke passed. Screenshots written to {args.output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
