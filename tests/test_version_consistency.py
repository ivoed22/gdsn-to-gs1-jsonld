"""Version-consistency guard (v0.12.1).

Fails if version metadata drifts between pyproject.toml, app/ui.py, the
CHANGELOG, the matching release notes, and the README. This catches the class
of release-prep mistake where one source (e.g. pyproject) is left on the
previous version.

Deterministic and offline.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _pyproject_version() -> str:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return data["project"]["version"]


def test_app_version_matches_pyproject() -> None:
    version = _pyproject_version()
    ui_text = (ROOT / "app" / "ui.py").read_text(encoding="utf-8")
    match = re.search(
        r'APP_VERSION\s*=\s*"v?([0-9]+\.[0-9]+\.[0-9]+)"', ui_text
    )
    assert match, "APP_VERSION not found in app/ui.py"
    assert match.group(1) == version, (
        f"app/ui.py APP_VERSION {match.group(1)} != pyproject version {version}"
    )


def test_changelog_latest_heading_matches_pyproject() -> None:
    version = _pyproject_version()
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    match = re.search(
        r"^##\s+v([0-9]+\.[0-9]+\.[0-9]+)", changelog, re.MULTILINE
    )
    assert match, "No version heading found in CHANGELOG.md"
    assert match.group(1) == version, (
        f"Latest CHANGELOG heading v{match.group(1)} != pyproject version {version}"
    )


def test_release_notes_exist_for_current_version() -> None:
    version = _pyproject_version()
    notes = ROOT / "docs" / "releases" / f"v{version}.md"
    assert notes.is_file(), f"Missing release notes: {notes}"
    assert version in notes.read_text(encoding="utf-8")


def test_readme_mentions_current_version() -> None:
    version = _pyproject_version()
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert version in readme, f"README.md does not mention current version {version}"
