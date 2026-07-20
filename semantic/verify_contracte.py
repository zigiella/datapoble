#!/usr/bin/env python3
"""Verificador del CONTRACTE semàntic (`semantic/metrics.yml`). Owner: Talaia.

Corre OFFLINE sobre artefactes versionats (el contracte + els parquets dels marts). No
substitueix els tests de `packages/ai` (que comproven com el catàleg SERVEIX el contracte):
aquí es comprova que el contracte no s'afirma a si mateix coses que les dades desmenteixen.

Per què existeix (2026-07-20). Mirador, escrivint el copy de D11, va anar a llegir el `caveat`
de `pct_nacionalitat_estrangera` i s'hi va trobar una invariant: «Sempre ≤ % nascuts a
l'estranger». És FALSA a 37 dels 938 municipis amb dada. Cap test la protegia perquè cap test
mirava el contracte contra les dades: el text d'un caveat era prosa lliure. Si Mirador hi
hagués recolzat el copy, la mentida hauria sortit publicada a 37 fitxes.

Tres comprovacions, totes barates:
  1. Claus mortes: `font`/`label_ca`/`label_es` van ser retirades (redundants de
     `origin_source` i de `label{ca,es}`); si reapareixen, algú ha tornat a duplicar un camp.
     NOTA: `visibilitat` NO és una clau morta — C1 §3 la declara vinculant i distinta de
     `visibility` («dos camps, no dos noms del mateix»). Talaia la va esborrar per error el
     mateix dia i la va haver de restaurar; per això aquí queda escrit.
  2. Invariants numèriques citades als caveats: el que el text afirma amb una xifra, es
     recompta al parquet. Avui: els 37/938 de la bretxa de naturalització negativa.
  3. Vocabulari de la regla d'evidència citable (E7a): els valors de `status` i `categoria`
     són els del contracte i no n'apareixen de nous per accident.
"""
from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import yaml

ARREL = Path(__file__).resolve().parent.parent
CONTRACTE = ARREL / "semantic" / "metrics.yml"
MARTS = ARREL / "data" / "marts"

CLAUS_RETIRADES = ("font", "label_ca", "label_es")
STATUS_VALIDS = {None, "planned", "deprecated"}
CATEGORIA_VALIDES = {None, "derived"}

errors: list[str] = []


def ok(cond: bool, msg: str) -> None:
    if not cond:
        errors.append(msg)


def main() -> int:
    contracte = yaml.safe_load(CONTRACTE.read_text(encoding="utf-8"))
    metrics: dict = contracte["metrics"]

    # 1 · claus retirades
    for nom, m in metrics.items():
        for clau in CLAUS_RETIRADES:
            ok(
                clau not in m,
                f"'{nom}' porta la clau retirada '{clau}': redundant d'origin_source/label. "
                f"Un camp amb dos noms és com es va perdre el caveat el 2026-07-17.",
            )

    # 2 · la invariant que el caveat afirma amb xifres, comptada a la dada
    dem = MARTS / "mart_demografia.parquet"
    if dem.exists():
        con = duckdb.connect()
        neg, amb_dada = con.execute(
            f"""SELECT count(*) FILTER (WHERE bretxa_naturalitzacio < 0),
                       count(*) FILTER (WHERE bretxa_naturalitzacio IS NOT NULL)
                FROM '{dem.as_posix()}'"""
        ).fetchone()
        for nom in ("pct_nacionalitat_estrangera", "bretxa_naturalitzacio"):
            text = " ".join(str(v) for v in (metrics.get(nom, {}).get("caveat") or {}).values())
            ok(
                str(neg) in text and str(amb_dada) in text,
                f"'{nom}': el caveat ha de dir el recompte real de la bretxa negativa "
                f"({neg} de {amb_dada}); si la dada s'ha refrescat, actualitza el text. "
                f"Aquesta comprovació existeix perquè el caveat afirmava «Sempre ≤» i era fals.",
            )
            ok(
                "empre ≤" not in text and "iempre ≤" not in text,
                f"'{nom}': el caveat torna a afirmar una invariant absoluta («Sempre ≤») que "
                f"les dades desmenteixen a {neg} municipis.",
            )

    # 3 · vocabulari de la regla d'evidència citable (E7a)
    for nom, m in metrics.items():
        ok(
            m.get("status") in STATUS_VALIDS,
            f"'{nom}': status '{m.get('status')}' desconegut (vàlids: planned, deprecated o cap).",
        )
        ok(
            m.get("categoria") in CATEGORIA_VALIDES,
            f"'{nom}': categoria '{m.get('categoria')}' desconeguda (vàlida: derived o cap). "
            f"La regla d'evidència citable s'hi recolza.",
        )

    if errors:
        print(f"CONTRACTE: {len(errors)} problema(es)\n")
        for e in errors:
            print(f"  ✗ {e}")
        return 1
    print(f"OK: contracte coherent ({len(metrics)} mètriques).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
