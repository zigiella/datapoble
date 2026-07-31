#!/usr/bin/env python3
"""QUINES MÈTRIQUES PINTA EL TAULER — derivat, mai mantingut a mà (D10 · serrell c).

El forat que tapa
-----------------
`mart_tendencia` i `export_tauler_web` portaven cadascun **la seva llista escrita a
mà** de les mètriques que el tauler ensenya. Dues llistes a mà i una tercera al front
(`GOVERN_KPIS`) no poden fer altra cosa que divergir, i quan divergeixen ho fan **en
silenci**: `serveis_estab` i `restauracio_estab` es pintaven al tauler i no tenien cap
fila al mart, ni tan sols com a `sense_serie` amb motiu. Una fila que falta és
INVISIBLE — el lector no distingeix «no ha canviat» de «no ho sabem». Un motiu, en
canvi, es pot llegir.

Aquest mòdul deriva el conjunt d'UNA sola autoritat: `packages/web/src/lib/govern/kpis.js`,
que el propi front ja declara com a «font ÚNICA de l'ordre i la composició del tauler»
(la comparteixen el component i `verify-govern.mjs`). Els verificadors i l'exportador de
dades hi recauen, així que el dia que Mirador afegeixi una targeta i el mart no tingui la
seva fila, **el CI cau** en comptes d'emetre un tauler amb una targeta muda.

Frontera de jurisdicció
-----------------------
`packages/web/` és de Mirador i aquí NOMÉS ES LLEGEIX (mai s'escriu). Llegir l'autoritat
és el contrari de duplicar-la.

Per què un parser i no un JSON compartit
----------------------------------------
Perquè `kpis.js` ÉS l'autoritat viva del front i qualsevol còpia intermèdia tornaria a
ser una segona llista a mà — el problema que això arregla. El parser és deliberadament
estricte: si no troba el bloc, si no en surt cap entrada o si apareix un `kind` que no
sap mapejar, **peta**. Un parser que falla en silenci seria pitjor que la llista a mà.

Ús:
    from tauler_kpis import metriques_del_tauler
    metriques_del_tauler(REPO)   # -> {'atur_registrat', 'poblacio', …}

Jurisdicció: Sondeig (dada + exportadors).
"""
from __future__ import annotations

import re
from pathlib import Path

KPIS_JS = Path("packages") / "web" / "src" / "lib" / "govern" / "kpis.js"

# Mètriques que pinta cada `kind` NO estàndard de `GOVERN_KPIS`. Les targetes `kind:
# 'metric'` porten la seva clau a la pròpia entrada i no calen aquí; aquestes altres
# pinten xifres SENSE dir-ho a l'entrada, així que el mapa s'ha d'escriure —i amb el
# motiu escrit, que és el que el fa auditable.
#
#   · 'atur'    → la clau ve de `trendKey` a la mateixa entrada ('atur_registrat'), i
#                 per això el mapa la deixa buida: no s'endevina, es llegeix.
#   · 'serveis' → la targeta pinta DUES xifres (comerç/serveis + restauració) sota un
#                 sol KPI. Les dues són dada publicada, així que les dues han de poder
#                 dir si tenen sèrie o per què no.
#   · 'etca'    → presència oficial d'Idescat (ETCA). NO és una mètrica de
#                 `mart_municipi` ni té contracte de tendència: viu al seu propi
#                 verificador (`tools/validacio_etca.py`). Buit DECLARAT, no oblit.
#                 ➡️ Handoff obert: l'ETCA té sèrie anual a la font; si algun dia es
#                 pinta amb fletxa, aquesta línia ha de deixar de ser buida.
KIND_METRICS: dict[str, tuple[str, ...]] = {
    "metric": (),        # la clau és a l'entrada (`key`)
    "atur": (),          # la clau és a l'entrada (`trendKey`)
    "serveis": ("serveis_estab", "restauracio_estab"),
    "etca": (),          # buit declarat (vegeu el comentari)
    # V3 (2026-07-29): les 4 franges d'edat i les 4 d'origen es fonen en DUES targetes amb barra
    # apilada. La targeta és una, però les 8 mètriques SEGUEIXEN PINTADES (recompte i % dins la
    # barra i la seva llegenda) — per tant segueixen necessitant fila al mart, que és el que
    # aquesta guarda protegeix. Registrar-les aquí no és burocràcia: sense això, fondre targetes
    # hauria tret 8 mètriques de tota guarda sense que ningú ho veiés.
    "edats": ("pob_0_14", "pob_15_64", "pob_65_84", "pob_85_mes"),
    "naixement": (
        "poblacio_nascuda_catalunya",
        "poblacio_nascuda_resta_espanya",
        "poblacio_nascuda_estranger",
        "pct_nascuda_estranger",
    ),
}

_BLOC = re.compile(r"export\s+const\s+GOVERN_KPIS\s*=\s*\[(.*?)\n\];", re.S)
_ENTRADA = re.compile(r"\{[^{}]*\}", re.S)
_CAMP = re.compile(r"(\w+)\s*:\s*'([^']*)'")
_BLOC_RANK = re.compile(r"export\s+const\s+GOVERN_RANK_KEYS\s*=\s*\[(.*?)\];", re.S)
_CLAU = re.compile(r"'([^']+)'")


def entrades_del_tauler(repo: Path) -> list[dict[str, str]]:
    """Les entrades de `GOVERN_KPIS` tal com el front les declara, en ordre.

    Peta si el fitxer no hi és o si el bloc no es deixa llegir: val més un CI vermell
    que una guarda que passa perquè no ha trobat res a comprovar.
    """
    js = repo / KPIS_JS
    if not js.exists():
        raise SystemExit(
            f"FALLA: no existeix {KPIS_JS.as_posix()} — és l'autoritat de la composició "
            f"del tauler i sense ella no es pot comprovar cap cobertura."
        )
    text = js.read_text(encoding="utf-8")
    bloc = _BLOC.search(text)
    if not bloc:
        raise SystemExit(
            f"FALLA: no s'ha trobat `export const GOVERN_KPIS = [ … ];` a "
            f"{KPIS_JS.as_posix()} — ha canviat de forma? El parser ha de canviar amb ella, "
            f"mai passar per alt."
        )
    entrades = [dict(_CAMP.findall(e)) for e in _ENTRADA.findall(bloc.group(1))]
    entrades = [e for e in entrades if e.get("kind")]
    if not entrades:
        raise SystemExit(
            f"FALLA: `GOVERN_KPIS` s'ha llegit BUIT a {KPIS_JS.as_posix()}. Un conjunt buit "
            f"faria passar totes les guardes de cobertura sense comprovar res."
        )
    return entrades


def metriques_del_tauler(repo: Path) -> set[str]:
    """Claus de mètrica que el tauler PINTA. És el conjunt que `mart_tendencia` ha de
    cobrir sencer: amb sèrie o amb `sense_serie` + motiu, però mai amb una absència."""
    out: set[str] = set()
    for e in entrades_del_tauler(repo):
        kind = e["kind"]
        if kind not in KIND_METRICS:
            raise SystemExit(
                f"FALLA: `GOVERN_KPIS` porta un kind nou, '{kind}', que aquest mapa no coneix. "
                f"Digues quines mètriques pinta a KIND_METRICS (tools/tauler_kpis.py) abans "
                f"de continuar — si no, la seva targeta quedaria fora de tota guarda."
            )
        clau = e.get("trendKey") or e.get("key")
        if clau:
            out.add(clau)
        out.update(KIND_METRICS[kind])
    return out


def claus_rankejades_del_front(repo: Path) -> set[str]:
    """Claus que el front declara com a RANKEJABLES (`GOVERN_RANK_KEYS` de `kpis.js`).

    Per què cal llegir-la (W3, 2026-07-31): el conjunt de mètriques amb rang viu escrit
    DUES vegades —`RANK_METRICS` a l'exportador i `GOVERN_RANK_KEYS` al front— i les dues
    llistes poden divergir en silenci. La direcció perillosa és una sola: si el FRONT
    reclama rang d'una clau que el mart no rankeja, la targeta es queda muda o pinta un
    forat; a l'inrevés (el mart rankeja i el front encara no ho pinta) és un estat de
    trànsit legítim mentre les dues jurisdiccions no han fusionat el mateix dia. Per això
    la guarda comprova la inclusió, no la igualtat.

    Mateixa frontera que la resta del mòdul: `packages/web/` NOMÉS es llegeix.
    """
    js = repo / KPIS_JS
    if not js.exists():
        raise SystemExit(
            f"FALLA: no existeix {KPIS_JS.as_posix()} — és l'autoritat de què el front "
            f"declara rankejable i sense ella la guarda no comprova res."
        )
    bloc = _BLOC_RANK.search(js.read_text(encoding="utf-8"))
    if not bloc:
        raise SystemExit(
            f"FALLA: no s'ha trobat `export const GOVERN_RANK_KEYS = [ … ];` a "
            f"{KPIS_JS.as_posix()} — ha canviat de forma? El parser ha de canviar amb "
            f"ella, mai passar per alt."
        )
    claus = set(_CLAU.findall(bloc.group(1)))
    if not claus:
        raise SystemExit(
            f"FALLA: `GOVERN_RANK_KEYS` s'ha llegit BUIT a {KPIS_JS.as_posix()}. Un "
            f"conjunt buit faria passar la guarda sense comprovar res."
        )
    return claus


if __name__ == "__main__":  # inspecció manual
    repo = Path(__file__).resolve().parents[1]
    claus = sorted(metriques_del_tauler(repo))
    print(f"{len(claus)} mètriques pintades pel tauler ({KPIS_JS.as_posix()}):")
    for c in claus:
        print(f"  · {c}")
    rank = sorted(claus_rankejades_del_front(repo))
    print(f"{len(rank)} claus que el front declara rankejables:")
    for c in rank:
        print(f"  · {c}")
