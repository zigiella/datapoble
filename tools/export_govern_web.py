"""Export web del mart_govern (D4) → JSON servit per la vista de govern (D5).

Pont de dades: D4 va crear ``data/marts/mart_govern.parquet`` (rang «k de n» per
comarca, calculat AL TRANSFORM), però NO en va emetre cap JSON servible. La vista de
govern (D5, Mirador) no pot calcular el rang al front (C6 §4, criteri verificable per
grep); per tant NOMÉS pot LLEGIR-lo. Aquest exportador tradueix el parquet a un JSON
servit com la resta de ``data/web/*.json`` (copiat a ``static/data/`` pel prebuild de
Mirador i llegit pel ``load`` de la fitxa).

Frontera honesta: aquí NO es calcula cap rang, percentil ni mediana — només es
re-serialitza la sortida del mart (valor, rang, n_amb_dada, data, les dues medianes de
referència + un indicador d'empat derivat del propi rang). El mart és la font; això
només el fa servible al web estàtic.

W4 (2026-07-31) · VALOR DE REFERÈNCIA. Cada cel·la porta les DUES medianes que el mart
mesura de les nostres pròpies dades: ``mediana_comarca`` (calculada sobre els
``n_amb_dada`` municipis de la comarca amb dada — el MATEIX denominador del rang) i
``mediana_catalunya`` (sobre ``n_mediana_catalunya``). Van DINS la cel·la, i no en un
bloc global, perquè el prebuild de Mirador parteix aquest fitxer per municipi
(``static/data/govern/<ine5>.json``) i el front només llegeix el seu tros: una
referència fora de l'entrada del municipi no li arribaria. La redundància (la catalana
és constant per mètrica) és el preu del shard, ja pagat amb ``comarca`` i ``data``.
⚠️ Aquestes medianes NO són les bases del model de pernocta aparcat (410/1224/26,5):
són mesura de les 947 dades nostres, i verify_govern.py té una guarda que peta si
alguna hi coincideix.

ABAST (P-947, 2026-07-27): s'emeten DOS artefactes, cadascun amb el seu ``--check``:
  · ``govern.bergueda.json`` — els 31 del Berguedà (RETROCOMPATIBILITAT: el
    prebuild ``copy-data.mjs`` i el verificador ``verify-govern.mjs`` de Mirador encara
    en depenen; no es toca fins que Mirador migri a l'abast 947).
  · ``govern.catalunya.json`` — els 947 municipis de Catalunya, cada rang «k de n»
    LLEGIT del mart contra LA COMARCA DEL PROPI MUNICIPI (43 comarques; el mart ja el
    calcula així, C6 §4). Un sol fitxer va bé: a 947 fa ~0,7 MB (les 7 mètriques de
    govern, sense sèries) i la fitxa el llegeix sencer per resoldre un municipi.
El rang mai es recalcula aquí: es re-serialitza el que el mart afirma.

GUARDA ANTI-FUITA (P-947): cap mètrica ``dimension: politica`` / ``source: electoral``
(res de ``mart_electoral``) pot entrar en aquest export. mart_govern només porta les 9
mètriques segures de govern; la guarda ho ASSERTA a cada execució (write i ``--check``)
llegint el contracte, perquè obrir l'export a 947 no destapi mai vot.

GUARDA DEL PONT FRONT↔DADES (W3): el conjunt de mètriques amb rang viu escrit dues
vegades —``RANK_METRICS`` aquí i ``GOVERN_RANK_KEYS`` a ``kpis.js``— i divergir en
silenci ja ha mossegat abans (el 2026-07-30, uns ``kind`` nous del tauler sense
registrar). Aquí es comprova la direcció perillosa: **cap clau que el front declari
rankejable pot faltar al mart** (si en falta, la targeta prometria un rang que ningú
serveix). La inversa —el mart rankeja i el front encara no ho pinta— és un estat de
trànsit legítim entre dues jurisdiccions que no fusionen el mateix dia.

Ús:
    python tools/export_govern_web.py            # (re)genera els DOS JSON (31 + 947)
    python tools/export_govern_web.py --check    # falla si algun fitxer versionat és estale

Jurisdicció: els exportadors ``tools/export_*.py`` i els artefactes ``data/web/*.json``
són de Sondeig.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tauler_kpis import claus_rankejades_del_front  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
MART = REPO / "data" / "marts" / "mart_govern.parquet"
METRICS_YML = REPO / "semantic" / "metrics.yml"
OUT_BERGUEDA = REPO / "data" / "web" / "govern.bergueda.json"
OUT_CATALUNYA = REPO / "data" / "web" / "govern.catalunya.json"

# (comarca de l'abast, fitxer de sortida). None = tots els 947 municipis. El Berguedà es
# manté per retrocompatibilitat (Mirador encara en depèn); Catalunya és el nou abast (P-947).
SCOPES: list[tuple[str | None, Path]] = [
    ("Berguedà", OUT_BERGUEDA),
    (None, OUT_CATALUNYA),
]

# Els 9 KPIs mesurats i oficials que el mart rankeja (gorra §3 / D4 + W3). L'ordre no
# importa aquí (el front el fixa); és el conjunt que esperem trobar al mart. TOTES són
# segures (cap de vot): la guarda anti-fuita (assert_no_electoral) ho verifica contra el
# contracte. W3 (2026-07-31) hi afegeix `vidre_hab` (esmena de Bea) i
# `pct_nacionalitat_estrangera` (esmena E9, vot narratiu ja emès el 2026-07-19).
RANK_METRICS = {
    "index_envelliment", "poblacio", "pct_noprincipal", "rtc_per_1000hab",
    "kwh_hab", "renda_neta_persona", "kg_hab_any",
    "vidre_hab", "pct_nacionalitat_estrangera",
}

# W4 · columnes de referència que el mart mesura i aquí NOMÉS es re-serialitzen.
MEDIANA_COLS = ("mediana_comarca", "mediana_catalunya", "n_mediana_catalunya")


def forbidden_metric_keys(contract: dict) -> set[str]:
    """Claus de mètrica que NO poden sortir mai al web públic de govern: qualsevol de
    ``dimension: politica`` o ``source: electoral`` o ``table: mart_electoral`` (les tres
    marquen la capa de vot). Es deriva del contracte, no d'una llista a mà, perquè si un dia
    se n'afegeix una de nova la guarda la cull sola."""
    forbidden: set[str] = set()
    for key, spec in contract.get("metrics", {}).items():
        if (
            spec.get("dimension") == "politica"
            or spec.get("source") == "electoral"
            or spec.get("table") == "mart_electoral"
        ):
            forbidden.add(key)
    return forbidden


def build(df: pd.DataFrame, scope: str | None) -> dict:
    """De les files del mart (format llarg) a ``{ine5: {comarca, metrics: {...}}}``.
    ``scope`` = nom de comarca a filtrar, o None per a tots els municipis (947)."""
    if scope is not None:
        df = df[df["comarca"] == scope]

    # Empat = més d'un municipi de la (comarca, metric) comparteix aquest rang (rank min:
    # els empatats comparteixen posició). Ho derivem del propi rang del mart, mai el
    # recalculem: comptem quantes files tenen el mateix (comarca, metric, rang). Amb l'abast
    # 947 el grup és PER COMARCA (la del municipi), no una llista fixa del Berguedà.
    grp = df.groupby(["comarca", "metric", "rang"], dropna=True)["ine5"].transform("count")
    df = df.assign(empat_flag=grp.gt(1))

    out: dict[str, dict] = {}
    for r in df.itertuples(index=False):
        rang = getattr(r, "rang")
        valor = getattr(r, "valor")
        entry = out.setdefault(r.ine5, {"comarca": r.comarca, "metrics": {}})
        med_com = getattr(r, "mediana_comarca")
        med_cat = getattr(r, "mediana_catalunya")
        entry["metrics"][r.metric] = {
            "valor": None if pd.isna(valor) else float(valor),
            "rang": None if pd.isna(rang) else int(rang),
            "n_amb_dada": int(getattr(r, "n_amb_dada")),
            "data": str(getattr(r, "data")),
            # Empat honest (C6 §3.2): rang compartit explícit. Només té sentit amb rang.
            "empat": bool(getattr(r, "empat_flag")) if not pd.isna(rang) else False,
            # W4 · valor de referència MESURAT (mai una constant del model aparcat). La
            # comarcal es calcula sobre els `n_amb_dada` municipis d'aquesta mateixa
            # cel·la; la catalana sobre `n_mediana_catalunya`. NULL = cap dada al grup.
            "mediana_comarca": None if pd.isna(med_com) else float(med_com),
            "mediana_catalunya": None if pd.isna(med_cat) else float(med_cat),
            "n_mediana_catalunya": int(getattr(r, "n_mediana_catalunya")),
        }
    # Ordre estable (per ine5) perquè la sortida sigui determinista i el diff net.
    return {k: out[k] for k in sorted(out)}


def render(payload: dict) -> str:
    """Serialització compacta i estable (com la resta d'actius servits), UTF-8 real, LF."""
    return json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n"


def assert_no_electoral(payload: dict, forbidden: set[str], out_name: str) -> None:
    """GUARDA ANTI-FUITA: cap mètrica de la capa de vot pot sortir al web de govern.
    Peta l'export sencer (write O --check) si en troba una. Font: el contracte."""
    emitted = {m for muni in payload.values() for m in muni["metrics"]}
    leak = emitted & forbidden
    if leak:
        raise SystemExit(
            f"FUITA ELECTORAL: {out_name} contindria mètriques de la capa de vot "
            f"{sorted(leak)} (dimension: politica / source: electoral). L'export de "
            f"govern només pot servir les mètriques segures; revisa mart_govern i el contracte."
        )


def main() -> int:
    check = "--check" in sys.argv[1:]
    for p in (MART, METRICS_YML):
        if not p.exists():
            print(f"FALLA: no existeix {p} (executa la ingesta + dbt build de mart_govern)",
                  file=sys.stderr)
            return 2

    contract = yaml.safe_load(METRICS_YML.read_text(encoding="utf-8"))
    forbidden = forbidden_metric_keys(contract)

    df = pd.read_parquet(MART)
    got = set(df["metric"].unique())
    missing = RANK_METRICS - got
    if missing:
        print(f"FALLA: el mart no porta els KPIs esperats: falten {sorted(missing)}",
              file=sys.stderr)
        return 1

    # W4 · sense les columnes de la mediana no es pot emetre la referència; val més un
    # vermell explícit que un JSON servit amb la meitat del contracte.
    if falten_cols := [c for c in MEDIANA_COLS if c not in df.columns]:
        print(f"FALLA: el mart no porta les columnes de la mediana (W4): {falten_cols} "
              f"— reconstrueix mart_govern", file=sys.stderr)
        return 1

    # W3 · guarda del pont front↔dades: cap clau que el front declari rankejable pot
    # faltar al mart (vegeu el capçal). Es llegeix de kpis.js, mai s'hi escriu.
    front = claus_rankejades_del_front(REPO)
    if orfes := sorted(front - RANK_METRICS):
        print(f"FALLA: el front declara rankejables {orfes}, que el mart NO rankeja "
              f"(GOVERN_RANK_KEYS de packages/web/src/lib/govern/kpis.js vs RANK_METRICS "
              f"d'aquest fitxer). La targeta prometria un rang que ningú serveix.",
              file=sys.stderr)
        return 1

    # Construeix + guarda anti-fuita per a cada abast ABANS de tocar el disc.
    outputs: list[tuple[Path, dict, str]] = []
    for scope, out in SCOPES:
        payload = build(df, scope)
        assert_no_electoral(payload, forbidden, out.name)
        outputs.append((out, payload, render(payload)))

    if check:
        stale: list[str] = []
        for out, _payload, text in outputs:
            if not out.exists():
                print(f"FALLA --check: no existeix {out} (executa'l sense --check)", file=sys.stderr)
                return 1
            # newline="": comparació byte-estable a Windows/Linux (els fitxers són eol=lf).
            with out.open("r", encoding="utf-8", newline="") as fh:
                current = fh.read()
            if current != text:
                stale.append(out.name)
        if stale:
            print(f"FALLA --check: {stale} estale — regenera "
                  f"(python tools/export_govern_web.py)", file=sys.stderr)
            return 1
        resum = ", ".join(f"{out.name}: {len(p)}" for out, p, _ in outputs)
        print(f"OK --check: govern al dia ({resum}).")
        return 0

    for out, payload, text in outputs:
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        n_rank = sum(
            1 for muni in payload.values() for mv in muni["metrics"].values()
            if mv["rang"] is not None
        )
        abast = "Berguedà" if out is OUT_BERGUEDA else "tota Catalunya"
        print(f"OK: {out.name} · {len(payload)} municipis ({abast}), "
              f"{n_rank} cel·les amb rang, {out.stat().st_size / 1024:.1f} kB.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
