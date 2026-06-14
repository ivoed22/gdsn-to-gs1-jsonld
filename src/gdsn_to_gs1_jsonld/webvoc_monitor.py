"""Monitor and locally snapshot official GS1 Web Vocabulary resources."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import tempfile
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

import pandas as pd

DEFAULT_JSONLD_URL = "https://ref.gs1.org/voc/data/gs1Voc.jsonld"
DEFAULT_TTL_URL = "https://ref.gs1.org/voc/data/gs1Voc.ttl"
DEFAULT_LINKTYPES_URL = "https://ref.gs1.org/voc/data/linktypes"

SNAPSHOT_FILES = {
    "jsonld": "gs1Voc.jsonld",
    "ttl": "gs1Voc.ttl",
    "linktypes": "linktypes.json",
}


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: str | Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def load_webvoc_jsonld(path: str | Path) -> dict[str, dict[str, Any]]:
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    return {
        item["@id"]: item
        for item in data.get("@graph", [])
        if isinstance(item, dict)
        and isinstance(item.get("@id"), str)
        and item["@id"].startswith("gs1:")
        and item["@id"] != "gs1:"
    }


def load_linktypes(path: str | Path) -> dict[str, dict[str, Any]]:
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("Link types snapshot must contain a JSON object.")
    return {
        key: value
        for key, value in data.items()
        if isinstance(key, str) and isinstance(value, dict)
    }


def _jsonld_metadata(content: bytes) -> tuple[str | None, str | None]:
    data = json.loads(content.decode("utf-8-sig"))
    ontology = next(
        (
            item
            for item in data.get("@graph", [])
            if isinstance(item, dict) and item.get("@id") == "gs1:"
        ),
        {},
    )
    version = ontology.get("owl:versionInfo")
    modified = ontology.get("dc:lastModified")
    if isinstance(modified, dict):
        modified = modified.get("@value")
    return (
        str(version) if version is not None else None,
        str(modified) if modified is not None else None,
    )


def _jsonld_terms(content: bytes) -> dict[str, dict[str, Any]]:
    data = json.loads(content.decode("utf-8-sig"))
    return {
        item["@id"]: item
        for item in data.get("@graph", [])
        if isinstance(item, dict)
        and isinstance(item.get("@id"), str)
        and item["@id"].startswith("gs1:")
        and item["@id"] != "gs1:"
    }


def _ttl_terms(content: bytes) -> set[str]:
    text = content.decode("utf-8-sig", errors="replace")
    return set(re.findall(r"(?m)^gs1:([A-Za-z][A-Za-z0-9_-]*)\s+", text))


def _linktypes(content: bytes) -> dict[str, dict[str, Any]]:
    data = json.loads(content.decode("utf-8-sig"))
    return data if isinstance(data, dict) else {}


def _changed_records(
    local: dict[str, Any],
    remote: dict[str, Any],
) -> tuple[list[str], list[str], list[str]]:
    local_keys = set(local)
    remote_keys = set(remote)
    changed = sorted(
        key
        for key in local_keys & remote_keys
        if json.dumps(local[key], sort_keys=True, ensure_ascii=False)
        != json.dumps(remote[key], sort_keys=True, ensure_ascii=False)
    )
    return sorted(remote_keys - local_keys), sorted(local_keys - remote_keys), changed


def _fetch(url: str) -> tuple[bytes, str | None]:
    request = Request(url, headers={"User-Agent": "gdsn-to-gs1-jsonld/0.6"})
    with urlopen(request, timeout=30) as response:
        return response.read(), response.headers.get("Last-Modified")


def _load_metadata(snapshot_dir: Path) -> dict[str, Any]:
    path = snapshot_dir / "metadata.json"
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _snapshot_metadata(
    contents: dict[str, bytes],
    *,
    urls: dict[str, str],
    last_modified_header: str | None = None,
) -> dict[str, Any]:
    version, detected_modified = _jsonld_metadata(contents["jsonld"])
    return {
        "source_url_jsonld": urls["jsonld"],
        "source_url_ttl": urls["ttl"],
        "source_url_linktypes": urls["linktypes"],
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "jsonld_sha256": sha256_bytes(contents["jsonld"]),
        "ttl_sha256": sha256_bytes(contents["ttl"]),
        "linktypes_sha256": sha256_bytes(contents["linktypes"]),
        "detected_version": version,
        "detected_last_modified": detected_modified or last_modified_header,
    }


def _write_snapshot(
    snapshot_dir: Path,
    contents: dict[str, bytes],
    metadata: dict[str, Any],
) -> None:
    snapshot_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=snapshot_dir.parent) as temporary:
        staging = Path(temporary)
        for source, filename in SNAPSHOT_FILES.items():
            (staging / filename).write_bytes(contents[source])
        (staging / "metadata.json").write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        for path in staging.iterdir():
            shutil.copy2(path, snapshot_dir / path.name)


def check_webvoc_updates(
    snapshot_dir: str | Path,
    *,
    jsonld_url: str = DEFAULT_JSONLD_URL,
    ttl_url: str = DEFAULT_TTL_URL,
    linktypes_url: str = DEFAULT_LINKTYPES_URL,
    no_network: bool = False,
    update_snapshot: bool = False,
) -> dict[str, Any]:
    directory = Path(snapshot_dir)
    urls = {
        "jsonld": jsonld_url,
        "ttl": ttl_url,
        "linktypes": linktypes_url,
    }
    local_contents: dict[str, bytes] = {}
    warnings: list[str] = []
    for source, filename in SNAPSHOT_FILES.items():
        path = directory / filename
        if not path.is_file():
            raise FileNotFoundError(f"Web Vocabulary snapshot missing: {path}")
        local_contents[source] = path.read_bytes()

    remote_contents: dict[str, bytes] = {}
    remote_last_modified: dict[str, str | None] = {}
    if not no_network:
        for source, url in urls.items():
            remote_contents[source], remote_last_modified[source] = _fetch(url)
    else:
        warnings.append("Network disabled; validated local snapshot only.")

    local_metadata = _load_metadata(directory)
    local_version, local_modified = _jsonld_metadata(local_contents["jsonld"])
    remote_version = local_version
    remote_modified = local_modified
    if remote_contents:
        remote_version, remote_modified = _jsonld_metadata(
            remote_contents["jsonld"]
        )

    local_jsonld_terms = _jsonld_terms(local_contents["jsonld"])
    local_ttl_terms = _ttl_terms(local_contents["ttl"])
    local_linktypes = _linktypes(local_contents["linktypes"])
    remote_jsonld_terms = (
        _jsonld_terms(remote_contents["jsonld"])
        if remote_contents
        else local_jsonld_terms
    )
    remote_ttl_terms = (
        _ttl_terms(remote_contents["ttl"])
        if remote_contents
        else local_ttl_terms
    )
    remote_linktypes = (
        _linktypes(remote_contents["linktypes"])
        if remote_contents
        else local_linktypes
    )

    new_terms, removed_terms, changed_terms = _changed_records(
        local_jsonld_terms,
        remote_jsonld_terms,
    )
    links_new, links_removed, links_changed = _changed_records(
        local_linktypes,
        remote_linktypes,
    )

    term_counts = {
        "jsonld": (len(local_jsonld_terms), len(remote_jsonld_terms)),
        "ttl": (len(local_ttl_terms), len(remote_ttl_terms)),
        "linktypes": (len(local_linktypes), len(remote_linktypes)),
    }
    sources = []
    for source, filename in SNAPSHOT_FILES.items():
        local_hash = sha256_bytes(local_contents[source])
        remote_hash = (
            sha256_bytes(remote_contents[source]) if remote_contents else None
        )
        sources.append(
            {
                "source": source,
                "source_url": urls[source],
                "local_hash": local_hash,
                "remote_hash": remote_hash,
                "changed": bool(remote_hash and remote_hash != local_hash),
                "detected_version": (
                    remote_version if source == "jsonld" else None
                ),
                "detected_last_modified": (
                    remote_modified
                    if source == "jsonld"
                    else remote_last_modified.get(source)
                ),
                "term_count_local": term_counts[source][0],
                "term_count_remote": term_counts[source][1],
            }
        )

    changed_sources = [item["source"] for item in sources if item["changed"]]
    actions = (
        [
            "Review new, removed, and changed terms before updating mappings.",
            "Run revalidate-mapping-catalog against the refreshed snapshot.",
        ]
        if changed_sources
        else ["No snapshot refresh action is required."]
    )

    if update_snapshot:
        if no_network:
            raise ValueError("--update-snapshot cannot be used with --no-network")
        metadata = _snapshot_metadata(
            remote_contents,
            urls=urls,
            last_modified_header=remote_last_modified.get("jsonld"),
        )
        _write_snapshot(directory, remote_contents, metadata)

    return {
        "summary": {
            "valid": True,
            "network_used": not no_network,
            "snapshot_updated": update_snapshot,
            "changed_sources": changed_sources,
            "local_version": local_metadata.get(
                "detected_version",
                local_version,
            ),
            "remote_version": remote_version if remote_contents else None,
        },
        "sources": sources,
        "new_terms": new_terms,
        "removed_terms": removed_terms,
        "changed_terms": changed_terms,
        "linktypes_new": links_new,
        "linktypes_removed": links_removed,
        "linktypes_changed": links_changed,
        "warnings": warnings,
        "recommended_actions": actions,
    }


def _update_report_xlsx_bytes(report: dict[str, Any]) -> bytes:
    sheets = {
        "Summary": [report["summary"]],
        "Sources": report["sources"],
        "New Terms": [{"term": item} for item in report["new_terms"]],
        "Removed Terms": [{"term": item} for item in report["removed_terms"]],
        "Changed Terms": [{"term": item} for item in report["changed_terms"]],
        "Linktypes New": [{"linktype": item} for item in report["linktypes_new"]],
        "Linktypes Removed": [
            {"linktype": item} for item in report["linktypes_removed"]
        ],
        "Linktypes Changed": [
            {"linktype": item} for item in report["linktypes_changed"]
        ],
        "Warnings": [{"warning": item} for item in report["warnings"]],
        "Recommended Actions": [
            {"recommended_action": item}
            for item in report["recommended_actions"]
        ],
    }
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for sheet, rows in sheets.items():
            pd.DataFrame(rows).to_excel(writer, index=False, sheet_name=sheet)
    return buffer.getvalue()


def write_webvoc_update_reports(
    report: dict[str, Any],
    output_dir: str | Path,
) -> dict[str, Path]:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": directory / "webvoc_update_report.json",
        "xlsx": directory / "webvoc_update_report.xlsx",
    }
    paths["json"].write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    paths["xlsx"].write_bytes(_update_report_xlsx_bytes(report))
    return paths
