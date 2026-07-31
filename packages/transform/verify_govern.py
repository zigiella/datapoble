"""Verificació OFFLINE de mart_govern (D4) — apte per a CI.

Corre sobre l'artefacte VERSIONAT ``data/marts/mart_govern.parquet`` + l'autoritat
territorial ``data/web/municipis-territori.json`` (cap xarxa). Guarda el contracte D4:

  1. Estructura: 9 KPIs OFICIALS × 947 municipis, format llarg (1 fila per ine5×metric),
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
  7. W4 · LA MEDIANA DE REFERÈNCIA, recalculada independentment amb pandas i comparada
     amb IGUALTAT EXACTA (no s'arrodoneix ni al mart ni aquí: mesurat, les medianes de
     DuckDB i de pandas coincideixen bit a bit als 387 grups comarcals i als 9 catalans).
     Denominadors honestos: la comarcal es calcula sobre n_amb_dada i la catalana sobre
     n_mediana_catalunya, tots dos recomptats a mà.
  8. LA TRAMPA DEL MODEL APARCAT, amb guarda pròpia: la referència ha de sortir de les
     NOSTRES dades, mai de les bases del model de pernocta aparcat (base_residencial
     410 · base_electric 1224 · base_vidre 26,5, a dbt_project.yml). Si algun dia una
     mediana catalana d'aquestes tres mètriques hi coincideix exactament, el CI s'atura
     i que algú ho miri: seria el model tornant per la porta del darrere.
  9. Àncores A MÀ de les sis medianes (Catalunya i Berguedà) dels tres rastres físics.

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
    # W3 (2026-07-31): vidre (esmena de Bea) i nacionalitat estrangera (esmena E9, el
    # vot narratiu que la retenia ja havia arribat el 2026-07-19).
    "vidre_hab", "pct_nacionalitat_estrangera",
}

# Àncores calculades A MÀ des de la gorra §2 (docs/ajuntaments/gorra-alcalde-pobla.md):
# la Pobla de Lillet (08166), Berguedà. (metric) -> (rang, n_amb_dada).
POBLA_ANCHORS: dict[str, tuple[int, int]] = {
    "index_envelliment": (6, 31),
    "poblacio": (8, 31),
    "pct_noprincipal": (10, 31),
    "renda_neta_persona": (19, 31),
    "kg_hab_any": (24, 31),
    # W3 · les dues noves, comptades a mà sobre el mart. La segona ensenya per què cal
    # el denominador honest: el Berguedà té 31 municipis però NOMÉS 27 tenen aquest
    # percentatge (els altres 4 cauen pel llindar mínim N de mart_demografia), i el
    # rang ho ha de dir — «6 de 27», mai «6 de 31».
    "vidre_hab": (17, 31),
    "pct_nacionalitat_estrangera": (6, 27),
}

# W4 · àncores A MÀ de la MEDIANA (mesurades sobre les nostres 947 dades, verificades
# contra les xifres que Talaia va portar a next.md el 2026-07-31: 472,1 · 1.529,3 · 29,0
# de Catalunya i 759,9 · 1.648,8 · 49,8 del Berguedà — les dues primeres estaven
# arrodonides a 1 decimal, el valor exacte és 472,06 i 759,88).
MEDIANES_CAT: dict[str, float] = {
    "kg_hab_any": 472.06,
    "kwh_hab": 1529.3,
    "vidre_hab": 29.0,
}
MEDIANES_BERGUEDA: dict[str, float] = {
    "kg_hab_any": 759.88,
    "kwh_hab": 1648.8,
    "vidre_hab": 49.8,
}

# Les BASES del model de pernocta APARCAT (dbt_project.yml). No són una referència
# publicable: si una mediana hi coincideix exactament, algú ha cablat la constant.
BASES_APARCADES: dict[str, float] = {
    "kg_hab_any": 410.0,
    "kwh_hab": 1224.0,
    "vidre_hab": 26.5,
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
          f"files = {len(df)} ≠ {N_MUNICIPIS * len(METRICS)} (947×{len(METRICS)})")
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

    # --- 7. W4 · la MEDIANA de referència, recalculada independentment ---
    # Esquema primer: sense les columnes, les guardes de sota petarien amb un KeyError.
    manquen = [c for c in ("mediana_comarca", "mediana_catalunya", "n_mediana_catalunya")
               if c not in df.columns]
    check(not manquen, f"columnes de la mediana (W4) absents del mart: {manquen}")
    if not manquen:
        # Comparació EXACTA, no aproximada: el mart no arrodoneix i pandas i DuckDB
        # calculen la mateixa mediana bit a bit. Si algun dia divergissin, val més veure
        # el vermell que amagar-lo darrere d'una tolerància.
        esperat_com = df.groupby(["comarca", "metric"])["valor"].transform("median")
        diff_com = df[~(
            (df["mediana_comarca"].isna() & esperat_com.isna())
            | (df["mediana_comarca"] == esperat_com)
        )]
        check(diff_com.empty,
              f"mediana_comarca ≠ mediana recalculada a {len(diff_com)} files "
              f"(p. ex. {diff_com[['ine5', 'metric']].head(3).values.tolist()})")

        esperat_cat = df.groupby("metric")["valor"].transform("median")
        diff_cat = df[~(
            (df["mediana_catalunya"].isna() & esperat_cat.isna())
            | (df["mediana_catalunya"] == esperat_cat)
        )]
        check(diff_cat.empty,
              f"mediana_catalunya ≠ mediana recalculada a {len(diff_cat)} files "
              f"(p. ex. {diff_cat[['ine5', 'metric']].head(3).values.tolist()})")

        # Denominadors honestos: el de la comarcal ÉS n_amb_dada (mateix partition by);
        # el de la catalana es recompta a part.
        n_cat = df.groupby("metric")["valor"].transform("count")
        check((df["n_mediana_catalunya"] == n_cat).all(),
              "n_mediana_catalunya ≠ recompte real de valors no nuls per mètrica")
        check((df["n_mediana_catalunya"] >= df["n_amb_dada"]).all(),
              "hi ha n_mediana_catalunya < n_amb_dada (el tot no pot ser menor que la part)")
        # NULL honest: si no hi ha cap dada al grup, no hi ha mediana (mai un 0 fabricat).
        check(df.loc[df["n_amb_dada"] == 0, "mediana_comarca"].isna().all(),
              "hi ha mediana_comarca amb n_amb_dada = 0 (mediana fabricada sobre una absència)")
        check(df.loc[df["n_amb_dada"] > 0, "mediana_comarca"].notna().all(),
              "hi ha mediana_comarca NULL havent-hi dada a la comarca")

        # --- 8. La trampa del model APARCAT ---
        for metric, base in BASES_APARCADES.items():
            fila = df[df["metric"] == metric]
            if fila.empty:
                continue
            med = float(fila["mediana_catalunya"].iloc[0])
            if med == base:
                fails.append(
                    f"mediana_catalunya de {metric} = {base} = la BASE del model de "
                    f"pernocta APARCAT (dbt_project.yml). La referència s'ha de MESURAR "
                    f"de les nostres dades, no cablar-hi la constant del model aparcat."
                )

        # --- 9. Àncores A MÀ de les medianes (Catalunya i Berguedà) ---
        for metric, esperat in MEDIANES_CAT.items():
            fila = df[df["metric"] == metric]
            if fila.empty:
                fails.append(f"àncora mediana CAT {metric}: mètrica absent")
                continue
            got = float(fila["mediana_catalunya"].iloc[0])
            if got != esperat:
                fails.append(f"àncora mediana CAT {metric}: esperava {esperat}, tinc {got}")
        berg = df[df["comarca"] == "Berguedà"]
        for metric, esperat in MEDIANES_BERGUEDA.items():
            fila = berg[berg["metric"] == metric]
            if fila.empty:
                fails.append(f"àncora mediana Berguedà {metric}: mètrica absent")
                continue
            got = float(fila["mediana_comarca"].iloc[0])
            if got != esperat:
                fails.append(f"àncora mediana Berguedà {metric}: esperava {esperat}, tinc {got}")

    if fails:
        print("VERIFICACIÓ mart_govern: FALLA", file=sys.stderr)
        for f in fails:
            print(f"  [x] {f}", file=sys.stderr)
        return 1
    n_null = int(df["valor"].isna().sum())
    n_med = len(MEDIANES_CAT) + len(MEDIANES_BERGUEDA)
    print(f"VERIFICACIÓ mart_govern: OK — {len(df)} files "
          f"({df['ine5'].nunique()} municipis × {len(METRICS)} KPIs), "
          f"{df['comarca'].nunique()} comarques, {n_null} sense dada (rang NULL honest), "
          f"{len(POBLA_ANCHORS)} àncores de rang a mà byte-match (Pobla/gorra §2), "
          f"Gombrèn rankeja contra {n_ripolles} del Ripollès, "
          f"medianes W4 recalculades amb igualtat exacta "
          f"({df.groupby(['comarca', 'metric']).ngroups} grups comarcals + {len(METRICS)} "
          f"catalans, {n_med} àncores a mà) i cap coincidint amb les bases aparcades.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
