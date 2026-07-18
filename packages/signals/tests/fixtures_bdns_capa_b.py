"""Càrrega de les fixtures de la CAPA B del banc C4 (tests offline, deterministes).

La capa B (C4 §2 v2, tasca R1.5) és la **classe positiva composada**: cerca
dirigida a la BDNS per LLISTA DE PROGRAMES (R-FUNC §2) sobre la finestra
18/07/2025–18/07/2026, arxivant **tot** el que cada consulta retorna — mai una
tria per «sembla elegible». Les consultes exactes, els recomptes, els retalls
mecànics (regex documentada) i els programes sense resultat viuen a `_meta` del
JSON: la composició és auditable línia a línia.

**Guarda anti-pre-etiquetatge (C4 §2 v2):** cap entrada porta `golden`,
`semafor` ni `motiu`, i l'ordre és mecànic (codigoBDNS ascendent). El camp
`programa` és la procedència de la CONSULTA que la va retornar (traçabilitat),
no cap judici d'elegibilitat. Qui etiqueta és NOMÉS la direcció humana, sobre
les capes A+B juntes.

`render_fila_taula` és l'única font de veritat del format de la taula
d'etiquetatge (`docs/ajuntaments/banc-c4-etiquetatge.md`, segona taula): el
generador i el test de transcripció mecànica la comparteixen, així la taula no
pot divergir de les fixtures sense que el test caigui (patró `test_parafrasis`).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FIXTURE_PATH_CAPA_B = Path(__file__).resolve().parent / "fixtures" / "bdns_capa_b.json"

_DOC = json.loads(FIXTURE_PATH_CAPA_B.read_text(encoding="utf-8"))

META_B: dict[str, Any] = _DOC["_meta"]
# [{"programa": str, "busqueda": {...}, "detall": {...}}, …] — codigoBDNS ascendent.
CONVOCATORIES_B: list[dict[str, Any]] = _DOC["convocatories"]

DETALLS_B: list[dict[str, Any]] = [c["detall"] for c in CONVOCATORIES_B]
BUSQUEDES_B: list[dict[str, Any]] = [c["busqueda"] for c in CONVOCATORIES_B]
PROGRAMES_B: list[str] = [c["programa"] for c in CONVOCATORIES_B]

PORTAL = "https://www.infosubvenciones.es/bdnstrans/GE/es/convocatorias/{codi}"

# Talls de columna calibrats sobre la taula de la capa A (#251): el «mateix
# format» del mandat és literal, no aproximat.
_TALL_CONVOCANT = 45
_TALL_OBJECTE = 95
_TALL_BENEFICIARIS = 60
_TALL_TERMINI = 30


def _colapsa(text: Any) -> str:
    """Espais/salts col·lapsats i `|` escapat: una cel·la de taula no pot trencar files."""
    return " ".join(str(text or "").split()).replace("|", "\\|")


def render_fila_taula(num: int, entrada: dict[str, Any]) -> str:
    """Una entrada de la fixture → la SEVA fila de la taula d'etiquetatge.

    Transcripció MECÀNICA (cap camp editat, cap judici): convocant =
    `organo.nivel2 / nivel3` @45 · objecte = `descripcion` @95 · beneficiaris =
    `"; ".join(tiposBeneficiarios)` @60 · àmbit = `regiones[0]` — i, si la fitxa
    en llista més d'una, «(+N)» perquè la primera sola no enganyi (cas real:
    896067 llista 19 CCAA i la primera és Galícia) · termini =
    `fechaFinSolicitud` (ISO) o, si no n'hi ha, `textFin` @30, o «—». Les tres
    columnes finals (golden/semafor/motiu) queden BUIDES: són de la direcció.
    """
    det = entrada["detall"]
    codi = str(det["codigoBDNS"])
    organo = det.get("organo") or {}
    convocant = _colapsa(
        " / ".join(
            str(organo.get(f"nivel{i}")).strip()
            for i in (2, 3)
            if organo.get(f"nivel{i}") and str(organo.get(f"nivel{i}")).strip()
        )
    )[:_TALL_CONVOCANT]
    objecte = _colapsa(det.get("descripcion"))[:_TALL_OBJECTE]
    beneficiaris = _colapsa(
        "; ".join(
            (t.get("descripcion") or "").strip()
            for t in (det.get("tiposBeneficiarios") or [])
        )
    )[:_TALL_BENEFICIARIS]
    regions = det.get("regiones") or []
    if not regions:
        ambit = "—"
    else:
        ambit = _colapsa(regions[0].get("descripcion") or "")
        if len(regions) > 1:
            ambit += f" (+{len(regions) - 1})"
    if det.get("fechaFinSolicitud"):
        termini = str(det["fechaFinSolicitud"])[:10]
    else:
        termini = _colapsa(det.get("textFin"))[:_TALL_TERMINI] or "—"
    return (
        f"| {num} | [{codi}]({PORTAL.format(codi=codi)}) | {convocant} | {objecte} "
        f"| {beneficiaris} | {ambit} | {termini} | | | |"
    )


def taula_capa_b(primer_num: int = 27) -> list[str]:
    """Totes les files de la segona taula, numerades a continuació de la capa A (26)."""
    return [
        render_fila_taula(primer_num + i, entrada)
        for i, entrada in enumerate(CONVOCATORIES_B)
    ]


def per_codi_b(codi: str) -> dict[str, Any]:
    """L'entrada {programa, busqueda, detall} d'un `codigoBDNS` concret."""
    for c in CONVOCATORIES_B:
        if str(c["detall"].get("codigoBDNS")) == str(codi):
            return c
    raise KeyError(f"cap fixture de capa B amb codigoBDNS={codi}")
