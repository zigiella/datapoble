"""Export web del mart_govern (D4) → JSON servit per la vista de govern (D5).

Pont de dades: D4 va crear ``data/marts/mart_govern.parquet`` (rang «k de n» per
comarca, calculat AL TRANSFORM), però NO en va emetre cap JSON servible. La vista de
govern (D5, Mirador) no pot calcular el rang al front (C6 §4, criteri verificable per
grep); per tant NOMÉS pot LLEGIR-lo. Aquest exportador tradueix el parquet a un JSON
servit com la resta de ``data/web/*.json`` (copiat a ``static/data/`` pel prebuild de
Mirador i llegit pel ``load`` de la fitxa).

Frontera honesta: aquí NO es calcula cap rang ni percentil — només es re-serialitza la
sortida del mart (valor, rang, n_amb_dada, data + un indicador d'empat derivat del propi
rang). El mart és la font; això només el fa servible al web estàtic.

Abast: els municipis del **Berguedà** (la vista de govern s'ofereix al Berguedà, C6 §1.2).
Per ampliar a més comarques: canvia ``SCOPE_COMARCA`` a ``None`` (exporta els 947) i
amplia la porta de la vista al front.

Ús:
    python tools/export_govern_web.py            # (re)genera data/web/govern.bergueda.json
    python tools/export_govern_web.py --check    # falla si el fitxer versionat és estale

Jurisdicció: els exportadors ``tools/export_*.py`` i els artefactes ``data/web/*.json``
són de Sondeig; això és un pont que D4 no va emetre. Handoff a Sondeig/Talaia per a
la propietat i el cablejat a la data-job (com ``--check`` dels altres exports).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
MART = REPO / "data" / "marts" / "mart_govern.parquet"
OUT = REPO / "data" / "web" / "govern.bergueda.json"

# Comarca de l'abast de la vista (C6 §1.2). None = totes (947).
SCOPE_COMARCA: str | None = "Berguedà"

# Els 7 KPIs mesurats i oficials que el mart rankeja (gorra §3 / D4). L'ordre no importa
# aquí (el front el fixa); és el conjunt que esperem trobar al mart.
RANK_METRICS = {
    "index_envelliment", "poblacio", "pct_noprincipal", "rtc_per_1000hab",
    "kwh_hab", "renda_neta_persona", "kg_hab_any",
}


def build(df: pd.DataFrame) -> dict:
    """De les files del mart (format llarg) a ``{ine5: {comarca, metrics: {...}}}``."""
    if SCOPE_COMARCA is not None:
        df = df[df["comarca"] == SCOPE_COMARCA]

    # Empat = més d'un municipi de la (comarca, metric) comparteix aquest rang (rank min:
    # els empatats comparteixen posició). Ho derivem del propi rang del mart, mai el
    # recalculem: comptem quantes files tenen el mateix (comarca, metric, rang).
    grp = df.groupby(["comarca", "metric", "rang"], dropna=True)["ine5"].transform("count")
    df = df.assign(empat_flag=grp.gt(1))

    out: dict[str, dict] = {}
    for r in df.itertuples(index=False):
        rang = getattr(r, "rang")
        valor = getattr(r, "valor")
        entry = out.setdefault(r.ine5, {"comarca": r.comarca, "metrics": {}})
        entry["metrics"][r.metric] = {
            "valor": None if pd.isna(valor) else float(valor),
            "rang": None if pd.isna(rang) else int(rang),
            "n_amb_dada": int(getattr(r, "n_amb_dada")),
            "data": str(getattr(r, "data")),
            # Empat honest (C6 §3.2): rang compartit explícit. Només té sentit amb rang.
            "empat": bool(getattr(r, "empat_flag")) if not pd.isna(rang) else False,
        }
    # Ordre estable (per ine5) perquè la sortida sigui determinista i el diff net.
    return {k: out[k] for k in sorted(out)}


def main() -> int:
    check = "--check" in sys.argv[1:]
    if not MART.exists():
        print(f"FALLA: no existeix {MART} (executa la ingesta + dbt build de mart_govern)",
              file=sys.stderr)
        return 2
    df = pd.read_parquet(MART)
    got = set(df["metric"].unique())
    missing = RANK_METRICS - got
    if missing:
        print(f"FALLA: el mart no porta els KPIs esperats: falten {sorted(missing)}",
              file=sys.stderr)
        return 1

    payload = build(df)
    # Serialització compacta i estable (com la resta d'actius servits), UTF-8 real.
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n"

    if check:
        if not OUT.exists():
            print(f"FALLA --check: no existeix {OUT} (executa'l sense --check)", file=sys.stderr)
            return 1
        current = OUT.read_text(encoding="utf-8")
        if current != text:
            print(f"FALLA --check: {OUT.name} està estale — regenera'l "
                  f"(python tools/export_govern_web.py)", file=sys.stderr)
            return 1
        print(f"OK --check: {OUT.name} al dia ({len(payload)} municipis).")
        return 0

    OUT.write_text(text, encoding="utf-8")
    n_rank = sum(
        1 for muni in payload.values() for mk, mv in muni["metrics"].items()
        if mv["rang"] is not None
    )
    print(f"OK: {OUT.name} → {len(payload)} municipis "
          f"({SCOPE_COMARCA or 'tota Catalunya'}), "
          f"{n_rank} cel·les amb rang, {OUT.stat().st_size / 1024:.1f} kB.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
