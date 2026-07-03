"""Guardes del joc congelat de paràfrasis (TORCH-FREE, offline).

La guarda important: el JSON és una transcripció MECÀNICA del doc congelat
(09-parafrasis-adversarials.md). Aquest test re-parseja el doc amb la mateixa regla i
exigeix igualtat exacta — cap deriva silenciosa entre el que Bea va congelar i el que
es corre. Cap test afirma el resultat del run oficial (el número es mesura, no s'afirma).
"""

import json
import re
from pathlib import Path

from datapoble_geo_rag.eval3 import load_bank
from datapoble_geo_rag.eval_parafrasis import (
    FAMILIA_ESPERADA,
    familia_silenci,
    load_parafrasis,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
DOC = _REPO_ROOT / "docs" / "experiment-rag-geo" / "09-parafrasis-adversarials.md"

_PAT = re.compile(r"P(\d+)([ab])(?:\s+\*\*\[es\]\*\*)?\s+«([^»]+)»")
_ESPAT = re.compile(r"P(\d+)([ab])\s+\*\*\[es\]\*\*")


def _parse_doc() -> list[dict]:
    doc = DOC.read_text(encoding="utf-8")
    es_ids = {(int(m.group(1)), m.group(2)) for m in _ESPAT.finditer(doc)}
    out = []
    for m in _PAT.finditer(doc):
        q, sub, text = int(m.group(1)), m.group(2), m.group(3).strip()
        out.append(
            {"id": f"P{q}{sub}", "q": q,
             "lang": "es" if (q, sub) in es_ids else "ca", "query": text}
        )
    out.sort(key=lambda e: (e["q"], e["id"]))
    return out


def test_json_es_transcripcio_fidel_del_doc_congelat():
    assert json.loads(json.dumps(load_parafrasis())) == _parse_doc()


def test_composicio_68_cada_q_dues_vegades_5_es():
    paras = load_parafrasis()
    assert len(paras) == 68
    counts = {}
    for p in paras:
        counts[p["q"]] = counts.get(p["q"], 0) + 1
    assert counts == {q: 2 for q in range(1, 35)}
    assert sum(1 for p in paras if p["lang"] == "es") == 5


def test_daurades_heretables_del_banc():
    bank_ids = {e["id"] for e in load_bank()}
    assert all(p["q"] in bank_ids for p in load_parafrasis())


def test_families_de_silenci():
    assert familia_silenci("valor_municipi") == "dada"
    assert familia_silenci("comparacio") == "ordre"
    assert familia_silenci("municipi_desconegut") == "catàleg"
    assert familia_silenci("indicador_desconegut") == "catàleg"
    assert familia_silenci("consulta_no_reconeguda") == "catàleg"
    assert familia_silenci("veins") == "altra"
    assert FAMILIA_ESPERADA == {"D": "dada", "E": "dada", "F": "ordre", "G": "catàleg"}
