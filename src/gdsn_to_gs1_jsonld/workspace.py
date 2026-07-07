"""Light workspace persistence for reviewer artifacts (v0.35.0).

Reviewer work — hard-mapping review sign-offs, SDR review annotations,
loaded candidate reports — previously evaporated with the Streamlit
session. This module saves/loads those artifacts as plain JSON files
under a git-ignored ``workspace/`` directory at the repository root.
One current file per artifact kind; saving overwrites. No database, no
timestamps written into payloads (file mtime is filesystem metadata).

Governance constraint: the workspace holds ONLY reviewer-authored
working artifacts. Nothing here reads from or writes to governed data
(``mapping/``, ``mapping_catalog/``, ``docs/standards-decisions/`` or
any other committed file) — the fixed kind vocabulary plus a fixed
filename per kind makes writing anywhere else structurally impossible.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_WORKSPACE_DIR = Path(__file__).resolve().parents[2] / "workspace"

# Fixed vocabulary: one artifact kind per reviewer workflow that produces
# session-scoped work worth keeping. Extend deliberately, never derive
# from user input.
ARTIFACT_KINDS = (
    "hard_mapping_signoff",
    "sdr_review_annotations",
    "candidate_report",
)


class WorkspaceError(ValueError):
    """Raised for an unknown artifact kind or an unserializable payload."""


def _artifact_path(kind: str, workspace_dir: str | Path | None) -> Path:
    if kind not in ARTIFACT_KINDS:
        raise WorkspaceError(
            f"Unknown artifact kind {kind!r}; expected one of {ARTIFACT_KINDS}."
        )
    # Resolved at call time (not in the signature default) so tests can
    # monkeypatch DEFAULT_WORKSPACE_DIR and never touch the real workspace.
    resolved = Path(workspace_dir) if workspace_dir is not None else DEFAULT_WORKSPACE_DIR
    return resolved / f"{kind}.json"


def save_artifact(
    kind: str,
    payload: dict[str, Any] | list[Any],
    workspace_dir: str | Path | None = None,
) -> Path:
    """Save *payload* as the current artifact of *kind*; returns the path."""
    path = _artifact_path(kind, workspace_dir)
    try:
        serialized = json.dumps(payload, indent=2, ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise WorkspaceError(f"Payload for {kind!r} is not JSON-serializable.") from exc
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialized, encoding="utf-8")
    return path


def load_artifact(
    kind: str,
    workspace_dir: str | Path | None = None,
) -> dict[str, Any] | list[Any] | None:
    """Load the current artifact of *kind*, or None when absent/corrupt.

    Corrupt files return None rather than raising: workspace files are
    reviewer conveniences, and a broken one should never take a workflow
    down — the reviewer simply re-authors and re-saves.
    """
    path = _artifact_path(kind, workspace_dir)
    if not path.is_file():
        return None
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(loaded, (dict, list)):
        return None
    return loaded


def list_artifacts(
    workspace_dir: str | Path | None = None,
) -> dict[str, dict[str, Any]]:
    """Report, per kind: whether a saved artifact exists and where."""
    inventory: dict[str, dict[str, Any]] = {}
    for kind in ARTIFACT_KINDS:
        path = _artifact_path(kind, workspace_dir)
        inventory[kind] = {
            "exists": path.is_file(),
            "path": str(path),
        }
    return inventory
