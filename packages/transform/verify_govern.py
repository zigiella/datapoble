"""Verificació OFFLINE de mart_govern (D4) — apte per a CI.

Corre sobre l'artefacte VERSIONAT ``data/marts/mart_govern.parquet`` + l'autoritat
territorial ``data/web/municipis-territori.json`` (cap xarxa). Guarda el contracte D4:

  1. Estructura: 7 KPIs OFICIALS × 947 municipis, format llarg (1 fila per ine5×metric),
     sense duplicats, ine5 de 5 caràcters.
  2. La comarca de CADA fila és la de municipis-territori.json (l'autoritat que parteix
     els rangs) — mai una llista fixa ni la comarca dels residus.
  3. Rang «k de n» PER COMARCA, recalculat independentment amb pandas (rank min,
     descendent) i comparat fila a fila amb el rang emmagatzemat: prova que el rang es
     va calcular al transform, no al front.
  4. n_amb_dada = municipis de la comarca amb la dada (denominador honest); rang dins
     [1, n_amb_dada]; NULL honest (valor NULL ⇒ rang NULL, i n_amb_dada l'exclou).
  5. RANG PER COMARCA DEL MUNICIPI, no per una llista fixa: Gombrèn (17080) rankeja
     contra els 19 del Ripollès, no contra els 31 del Berguedà (el forat que la spec
     evita explícitament).
  6. Byte-match d'àncores calculades A MÀ contra la gorra §2 (la Pobla, 08166):
     envelliment 6/31, padró 8/31, %no-principal 10/31, renda 19/31, residus 24/31.

    python packages/transform/verify_govern.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
MART = REPO / "data" / "marts" / "mart_govern.parquet"
TERRITORI = REPO / "data" / "web" / "municipis-territori.json"

N_MUNICIPIS = 947
METRICS = {
    "index_envelliment", "poblacio", "pct_noprincipal", "rtc_per_1000hab",
    "kwh_hab", "renda_neta_persona", "kg_hab_any",
}

# Àncores calculades A MÀ des de la gorra §2 (docs/ajuntaments/gorra-alcalde-pobla.md):
# la Pobla de Lillet (08166), Berguedà. (metric) -> (rang, n_amb_dada).
POBLA_ANCHORS: dict[str, tuple[int, int]] = {
    "index_envelliment": (6, 31),
    "poblacio": (8, 31),
    "pct_noprincipal": (10, 31),
    "renda_neta_persona": (19, 31),
    "kg_hab_any": (24, 31),
}


def main() -> int:
    fails: list[str] = []

    if not MART.exists():
        print(f"FALLA: no existeix {MART} (executa la ingesta + dbt build)", file=sys.stderr)
        return 2
    df = pd.read_parquet(MART)
    territori = json.loads(TERRITORI.read_text(encoding="utf-8"))
    ine5_to_comarca = {k: v["comarca"] for k, v in territori.items()}

    def check(cond: bool, msg: str) -> None:
        if not cond:
            fails.append(msg)

    # --- 1. Estructura ---
    check(not df.empty, "mart buit")
    check(set(df["metric"]) == METRICS,
          f"conjunt de mètriques inesperat: {sorted(set(df['metric']))}")
    check(df["ine5"].nunique() == N_MUNICIPIS,
          f"municipis = {df['ine5'].nunique()} ≠ {N_MUNICIPIS}")
    check(len(df) == N_MUNICIPIS * len(METRICS),
          f"files = {len(df)} ≠ {N_MUNICIPIS * len(METRICS)} (947×7)")
    check(df.duplicated(subset=["ine5", "metric"]).sum() == 0,
          "(ine5, metric) amb duplicats")
    check(df["ine5"].str.len().eq(5).all(), "hi ha ine5 que no fan 5 caràcters")
    check(df["data"].notna().all() and df["data"].str.len().ge(4).all(),
          "hi ha `data` (vintage) buida o massa curta")

    # --- 2. Comarca = municipis-territori.json (l'autoritat que parteix el rang) ---
    mismatch = df[df["comarca"] != df["ine5"].map(ine5_to_comarca)]
    check(mismatch.empty,
          f"comarca del mart ≠ municipis-territori.json a {len(mismatch)} files "
          f"(p. ex. {mismatch['ine5'].head(3).tolist()})")

    # --- 3. Rang recalculat independentment (rank min descendent) == rang del mart ---
    esperat = df.groupby(["comarca", "metric"])["valor"].rank(
        method="min", ascending=False, na_option="keep"
    )
    diff_rang = df[~(
        (df["rang"].isna() & esperat.isna())
        | (df["rang"] == esperat)
    )]
    check(diff_rang.empty,
          f"rang emmagatzemat ≠ rang recalculat a {len(diff_rang)} files "
          f"(p. ex. {diff_rang[['ine5', 'metric']].head(3).values.tolist()})")

    # --- 4. n_amb_dada honest + rang dins rang + NULL honest ---
    n_real = df.groupby(["comarca", "metric"])["valor"].transform("count")
    check((df["n_amb_dada"] == n_real).all(),
          "n_amb_dada ≠ recompte real de valors no nuls per (comarca, metric)")
    amb_valor = df[df["valor"].notna()]
    check(amb_valor["rang"].notna().all(), "hi ha valor sense rang (NULL indegut)")
    check((amb_valor["rang"] >= 1).all() and (amb_valor["rang"] <= amb_valor["n_amb_dada"]).all(),
          "hi ha rang fora de [1, n_amb_dada]")
    sense_valor = df[df["valor"].isna()]
    check(sense_valor["rang"].isna().all(),
          "valor NULL amb rang NO nul (rang fabricat sobre una absència)")

    # --- 5. Rang PER COMARCA DEL MUNICIPI (Gombrèn contra el Ripollès, no els 31) ---
    n_ripolles = sum(1 for c in ine5_to_comarca.values() if c == "Ripollès")
    n_bergueda = sum(1 for c in ine5_to_comarca.values() if c == "Berguedà")
    gombren = df[df["ine5"] == "17080"]
    check(not gombren.empty, "Gombrèn (17080) absent del mart")
    check((gombren["comarca"] == "Ripollès").all(),
          "Gombrèn no surt al Ripollès")
    # els seus KPIs plens tenen n_amb_dada = els del Ripollès (19), MAI els 31 del Berguedà
    check((gombren["n_amb_dada"] <= n_ripolles).all() and (gombren["n_amb_dada"] > 0).all(),
          f"Gombrèn amb n_amb_dada > {n_ripolles} (rankeja fora del Ripollès!)")
    check(not (gombren["n_amb_dada"] == n_bergueda).any() or n_ripolles == n_bergueda,
          "Gombrèn amb n_amb_dada = 31 (rankeja contra el Berguedà, no el Ripollès)")
    # concretament: cap KPI ple de Gombrèn té rang > 19
    check((gombren[gombren["valor"].notna()]["rang"] <= n_ripolles).all(),
          f"Gombrèn amb rang > {n_ripolles} (impossible dins el Ripollès)")

    # --- 6. Byte-match d'àncores A MÀ (la Pobla vs gorra §2) ---
    pobla = df[df["ine5"] == "08166"].set_index("metric")
    check(not pobla.empty, "la Pobla (08166) absent del mart")
    check((pobla["comarca"] == "Berguedà").all(), "la Pobla no surt al Berguedà")
    for metric, (rang, n) in POBLA_ANCHORS.items():
        try:
            row = pobla.loc[metric]
        except KeyError:
            fails.append(f"àncora Pobla {metric}: fila absent")
            continue
        if not (int(row["rang"]) == rang and int(row["n_amb_dada"]) == n):
            fails.append(f"àncora Pobla {metric}: esperava {rang}/{n}, "
                         f"tinc {int(row['rang'])}/{int(row['n_amb_dada'])}")

    if fails:
        print("VERIFICACIÓ mart_govern: FALLA", file=sys.stderr)
        for f in fails:
            print(f"  [x] {f}", file=sys.stderr)
        return 1
    n_null = int(df["valor"].isna().sum())
    print(f"VERIFICACIÓ mart_govern: OK — {len(df)} files "
          f"({df['ine5'].nunique()} municipis × {len(METRICS)} KPIs), "
          f"{df['comarca'].nunique()} comarques, {n_null} sense dada (rang NULL honest), "
          f"{len(POBLA_ANCHORS)} àncores a mà byte-match (Pobla/gorra §2), "
          f"Gombrèn rankeja contra {n_ripolles} del Ripollès.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
