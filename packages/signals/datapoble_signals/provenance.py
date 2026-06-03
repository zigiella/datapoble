"""Metadades de procedència (mateix patró que Sondeig).

Regla del projecte (CONTRIBUTING / metrics.yml): *cap número sense procedència*.
A la capa de senyals la traçabilitat per fila ja viu a ``font_url``; aquest
sidecar documenta la **càrrega sencera** (font, query, recompte, fitxer).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import __version__
from .config import SOURCES


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_provenance(
    source: str,
    out_dir: Path,
    *,
    row_count: int,
    files: list[str],
    query: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> Path:
    """Escriu ``_provenance.json`` amb la traçabilitat de la càrrega."""
    src = SOURCES[source]
    record: dict[str, Any] = {
        "source": source,
        "organisme": src["organisme"],
        "producte": src["producte"],
        "dataset_id": src.get("dataset_id"),
        "url": src["url"],
        "llicencia": src["llicencia"],
        "fetched_at": now_utc_iso(),
        "row_count": row_count,
        "files": files,
        "scope": "Berguedà (pilot: Castellar, Berga, Consell Comarcal)",
        "signals_version": __version__,
    }
    if query is not None:
        record["query"] = query
    if extra:
        record.update(extra)

    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "_provenance.json"
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
