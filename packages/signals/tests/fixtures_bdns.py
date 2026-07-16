"""Càrrega de les fixtures reals de la BDNS per a tests offline (deterministes).

Les fixtures són una **captura literal** de l'API (2026-07-16), arxivada a
`tests/fixtures/bdns_convocatories.json`: cap camp afegit ni editat. Cada entrada
porta les DUES cares de la font, perquè els dos endpoints tenen esquemes distints:
  - `busqueda`: la fila plana (`numeroConvocatoria`, `nivel1/2/3`) — la que
    descobreix la novetat.
  - `detall`:   la fitxa niuada (`codigoBDNS`, `organo.*`, `regiones[]`,
    `tiposBeneficiarios[]`, `abierto`, terminis) — la que omple el contracte C3.

Cobertura (verificada, vegeu `test_subvencions_bdns.py`): 26 convocatòries reals ·
LOCAL/AUTONOMICA/ESTADO/OTROS · 7 obertes i 19 tancades · 16 amb text en català
(`descripcionLeng`) · 8 amb el conflicte `abierto=false` + termini futur · regions
ES-ESPAÑA, ES51-CATALUÑA i províncies · 3 amb `urlBasesReguladoras` que NO és URL.

C4 §2: aquestes fixtures són **candidates al banc** d'avaluació. L'etiquetatge
daurat (`golden`) és de Bea, a mà, mai d'un model — aquí no n'hi ha cap.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "bdns_convocatories.json"


def _carrega() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


_DOC = _carrega()

META: dict[str, Any] = _DOC["_meta"]
# [{"busqueda": {...}, "detall": {...}}, …] — ordre estable (per codigoBDNS).
CONVOCATORIES: list[dict[str, Any]] = _DOC["convocatories"]

DETALLS: list[dict[str, Any]] = [c["detall"] for c in CONVOCATORIES]
BUSQUEDES: list[dict[str, Any]] = [c["busqueda"] for c in CONVOCATORIES]


def per_codi(codi: str) -> dict[str, Any]:
    """La parella busqueda/detall d'un `codigoBDNS` concret."""
    for c in CONVOCATORIES:
        if str(c["detall"].get("codigoBDNS")) == str(codi):
            return c
    raise KeyError(f"cap fixture amb codigoBDNS={codi}")
