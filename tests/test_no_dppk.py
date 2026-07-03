"""No-dppk policy tests (v0.15.0 onward).

DPP Keystone (dppk) may be referenced in documentation as external tooling
inspiration only. Generated and recommended output — mapping artifacts, app
code, converter source, example outputs, builder manifest, and Product
Passport examples — must never contain dppk terms or namespaces.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Directories whose content is generated/recommended output or the code that
# produces it. docs/ is deliberately excluded: documentation may mention DPP
# Keystone as external tooling inspiration (clearly marked, never emitted).
SCANNED_DIRECTORIES = (
    "mapping",
    "mapping_catalog",
    "app",
    "src",
    "examples",
    "builder_manifest",
    "product_passport",
    "scripts",
    "tests",
)
SCANNED_SUFFIXES = {".py", ".yaml", ".yml", ".json", ".jsonld", ".csv", ".md", ".xml"}
FORBIDDEN_MARKERS = ("dppk:", "dppk/", '"dppk"', "'dppk'", "dpp-keystone", "dpp_keystone")
# This policy test file itself necessarily names the markers.
ALLOWED_FILES = {Path("tests") / "test_no_dppk.py"}


def _scannable_files() -> list[Path]:
    files: list[Path] = []
    for directory in SCANNED_DIRECTORIES:
        base = ROOT / directory
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in SCANNED_SUFFIXES:
                continue
            if path.relative_to(ROOT) in ALLOWED_FILES:
                continue
            files.append(path)
    return files


def test_no_dppk_in_generated_or_recommended_output() -> None:
    violations: list[str] = []
    for path in _scannable_files():
        try:
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            continue
        for marker in FORBIDDEN_MARKERS:
            if marker in text:
                violations.append(f"{path.relative_to(ROOT)}: {marker}")
    assert not violations, (
        "dppk must never appear in generated/recommended output: "
        + "; ".join(violations)
    )


def test_scanned_directories_exist() -> None:
    """Guard against the scan silently going stale if directories move."""
    for directory in ("mapping", "app", "src", "examples"):
        assert (ROOT / directory).is_dir(), directory
