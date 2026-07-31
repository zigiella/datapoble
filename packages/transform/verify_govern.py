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
 10. R-REFERENCIA · LA PONDERADA (total ÷ habitants), recalculada a mà amb el pes PROPI de
     cada mètrica i comparada. ⚠️ Aquí NO es pot exigir igualtat EXACTA i el motiu és
     aritmètic, no laxitud: la mediana és una SELECCIÓ (DuckDB i pandas trien el mateix
     element, bit a bit), però la ponderada és una SUMA, i la suma en coma flotant no és
     associativa — la finestra de DuckDB i el groupby de pandas sumen en ordres diferents.
     Divergència MESURADA sobre les 7.576 files comparables: màxim 1,5e-15 relatiu (~7 ulp).
     La tolerància és 1e-12 relatiu, ~700× la divergència observada i encara 1e-9 kWh sobre
     una xifra de 1.252 kWh/hab: prou fina per caçar qualsevol error de dada i prou ampla
     per no caçar l'ordre de la suma. El DENOMINADOR (hab_ponderada_*) sí que es compara
     amb igualtat exacta: són sumes de sencers.
 11. R-REFERENCIA · L'ESTRATIFICADA PER FRANJA: franja recalculada dels talls declarats,
     mediana i n de la franja recalculats amb pandas i comparats amb igualtat exacta.
 12. La guarda del model APARCAT, AMPLIADA: abans només mirava `mediana_catalunya`; ara
     mira TOTES les referències (mediana comarcal/catalana/de franja i ponderada
     comarcal/catalana) i també la quarta constant aparcada, `base_comarcal` (452), que
     abans no hi era. Motiu concret: la ponderada comarcal de residus del Berguedà mesura
     452,90 — a mig punt de la constant. No hi coincideix (i és una MESURA nova, no la
     constant), però l'endemà d'una recàrrega podria coincidir-hi per atzar i llavors
     l'hem de mirar, no publicar.

    python packages/transform/verify_govern.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
MART = REPO / "data" / "marts" / "mart_govern.parquet"
MART_MUNI = REPO / "data" / "marts" / "mart_municipi.parquet"
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
#
# ⚠️ LES DUES DE `kwh_hab` VAN CANVIAR el 2026-07-31 (R-REFERENCIA) i NO és una deriva:
# fins llavors la mètrica dividia el consum de 2024 pel padró de 2025 i els seus dos valors
# eren 1.529,3 (CAT) i 1.648,8 (Berguedà). Amb el denominador de l'any correcte són 1.538,2
# i 1.694,6. Les vuit mètriques restants NO es mouen ni un dígit (comprovat parquet contra
# parquet), i per això aquestes dues àncores es reescriuen amb el motiu escrit al costat en
# comptes d'afluixar-se: una àncora que es canvia sense dir per què deixa de ser una àncora.
MEDIANES_CAT: dict[str, float] = {
    "kg_hab_any": 472.06,
    "kwh_hab": 1538.2,
    "vidre_hab": 29.0,
}
MEDIANES_BERGUEDA: dict[str, float] = {
    "kg_hab_any": 759.88,
    "kwh_hab": 1694.6,
    "vidre_hab": 49.8,
}

# R-REFERENCIA · àncores A MÀ de la PONDERADA de Catalunya (total ÷ habitants), les tres
# xifres que Bea va portar de les fonts oficials i que aquest PR ha de reproduir:
#   · residus 476,85 kg/hab/any — i el titular d'Idescat (~500) NO hi ha de coincidir:
#     la diferència és la fila «No territorialitzable» del propi dataset de l'ARC
#     (175.115,55 t el 2024), residus reals que no s'atribueixen a cap municipi.
#   · elèctric 1.252,1 kWh/hab — EL NÚMERO DE BEA. Abans del fix del vintage sortia
#     1.234,86 (un 1,40% per sota): aquesta àncora és la prova que el bug està tancat.
#   · vidre 22,89 kg/hab/any.
# Tolerància relativa: la mateixa 1e-12 del recàlcul (vegeu el docstring, punt 10).
PONDERADES_CAT: dict[str, float] = {
    "kg_hab_any": 476.8462845666835,
    "kwh_hab": 1252.1089886200245,
    "vidre_hab": 22.88903666157405,
}

# Recàlcul de la ponderada: el PES de cada mètrica és el SEU PROPI DENOMINADOR (columna de
# mart_municipi). Escrit aquí a mà, no llegit del mart: si el model canviés de pes sense
# dir-ho, el verificador ho ha de veure. `poblacio` no en té (vegeu el capçal del model).
PES_DE_LA_METRICA: dict[str, str | None] = {
    "index_envelliment": "pob_0_14",
    "poblacio": None,
    "pct_noprincipal": "hab_total",
    "rtc_per_1000hab": "poblacio",
    "kwh_hab": "poblacio_kwh",
    "renda_neta_persona": "poblacio",
    "kg_hab_any": "poblacio_residus",
    "vidre_hab": "poblacio_residus",
    "pct_nacionalitat_estrangera": "poblacio",
}

# Talls de franja de població (esmena de Bea, R-REFERENCIA 2026-07-31). Escrits aquí a mà
# per la mateixa raó: el verificador ha de tenir la seva pròpia còpia de la regla.
FRANGES: list[tuple[float, str]] = [
    (250, "<250"), (500, "250-499"), (1000, "500-999"),
    (5000, "1.000-4.999"), (20000, "5.000-19.999"), (float("inf"), ">=20.000"),
]

# Tolerància relativa del recàlcul de la ponderada (vegeu el punt 10 del docstring).
RTOL_PONDERADA = 1e-12

# Les BASES del model de pernocta APARCAT (dbt_project.yml). No són una referència
# publicable: si una referència hi coincideix exactament, algú ha cablat la constant.
# `base_comarcal` (452) hi entra el 2026-07-31: és la quarta constant aparcada i la
# ponderada comarcal de residus del Berguedà mesura 452,90, a mig punt d'ella.
BASES_APARCADES: dict[str, float] = {
    "kg_hab_any": 410.0,
    "kwh_hab": 1224.0,
    "vidre_hab": 26.5,
}
BASE_COMARCAL_APARCADA = 452.0


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

        # --- 8. La trampa del model APARCAT (AMPLIADA a TOTES les referències) ---
        cols_referencia = [c for c in ("mediana_comarca", "mediana_catalunya", "mediana_franja",
                                       "ponderada_comarca", "ponderada_catalunya")
                           if c in df.columns]
        for metric, base in BASES_APARCADES.items():
            fila = df[df["metric"] == metric]
            if fila.empty:
                continue
            for col in cols_referencia:
                n_hit = int((fila[col] == base).sum())
                if n_hit:
                    fails.append(
                        f"{col} de {metric} = {base} a {n_hit} files = la BASE del model de "
                        f"pernocta APARCAT (dbt_project.yml). La referència s'ha de MESURAR "
                        f"de les nostres dades, no cablar-hi la constant del model aparcat."
                    )
            # La quarta constant aparcada: base_comarcal (452), la «mitjana comarcal
            # pop-ponderada» del model. La ponderada comarcal de residus del Berguedà hi frega.
            if metric == "kg_hab_any":
                for col in cols_referencia:
                    n_hit = int((fila[col] == BASE_COMARCAL_APARCADA).sum())
                    if n_hit:
                        fails.append(
                            f"{col} de {metric} = {BASE_COMARCAL_APARCADA} a {n_hit} files = "
                            f"base_comarcal, la constant APARCADA del tall relatiu "
                            f"(dbt_project.yml). Que hi coincideixi exactament vol dir que "
                            f"algú l'ha cablada o que cal mirar-s'ho abans de publicar-ho."
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

    # --- 10-11. R-REFERENCIA · ponderada i estratificada ---
    COLS_REF = ("pes_ponderada", "ponderada_comarca", "hab_ponderada_comarca",
                "ponderada_catalunya", "hab_ponderada_catalunya",
                "franja_poblacio", "mediana_franja", "n_franja")
    manquen_ref = [c for c in COLS_REF if c not in df.columns]
    check(not manquen_ref, f"columnes de referència (R-REFERENCIA) absents del mart: {manquen_ref}")
    n_franges = 0
    if not manquen_ref and MART_MUNI.exists():
        muni = pd.read_parquet(MART_MUNI)
        pesos = muni.set_index("ine5")[
            ["poblacio", "hab_total", "pob_0_14", "poblacio_residus", "poblacio_kwh"]
        ]

        # El nom del pes declarat al mart ha de ser el que aquest fitxer diu, mètrica a mètrica.
        for metric, nom in PES_DE_LA_METRICA.items():
            fila = df[df["metric"] == metric]
            if fila.empty:
                continue
            vals = set(fila["pes_ponderada"].dropna().unique())
            esperat_set = set() if nom is None else {nom}
            if vals != esperat_set:
                fails.append(f"pes_ponderada de {metric}: esperava {esperat_set or '∅'}, tinc {vals or '∅'}")

        # Recàlcul a mà de la ponderada i del seu denominador.
        pes = pd.Series(
            [np.nan if PES_DE_LA_METRICA.get(m) is None
             else pesos.at[i, PES_DE_LA_METRICA[m]]
             for i, m in zip(df["ine5"], df["metric"])],
            index=df.index, dtype="float64",
        )
        num = (df["valor"] * pes)
        den = pes.where(df["valor"].notna())
        for scope, keys in (("comarca", ["comarca", "metric"]), ("catalunya", ["metric"])):
            g_num = num.groupby([df[k] for k in keys]).transform("sum", min_count=1)
            g_den = den.groupby([df[k] for k in keys]).transform("sum", min_count=1)
            esperat_pond = g_num / g_den.replace(0, np.nan)
            got_pond = df[f"ponderada_{scope}"]
            # El patró de NULL ha de coincidir EXACTAMENT (un forat declarat no es pot omplir).
            check((esperat_pond.isna() == got_pond.isna()).all(),
                  f"ponderada_{scope}: el patró de NULL no coincideix amb el recalculat "
                  f"(p. ex. `poblacio` ha de sortir NULL: no té denominador propi)")
            tots = esperat_pond.notna() & got_pond.notna()
            prop = np.isclose(esperat_pond[tots], got_pond[tots], rtol=RTOL_PONDERADA, atol=0.0)
            check(bool(prop.all()),
                  f"ponderada_{scope} ≠ ponderada recalculada a {int((~prop).sum())} files "
                  f"(tolerància relativa {RTOL_PONDERADA:g}; vegeu el punt 10 del docstring)")
            # El denominador és una suma de sencers: igualtat EXACTA, sense excuses.
            got_hab = df[f"hab_ponderada_{scope}"]
            check(((got_hab == g_den) | (got_hab.isna() & g_den.isna())).all(),
                  f"hab_ponderada_{scope} ≠ suma recalculada dels habitants amb dada")

        for metric, esperat in PONDERADES_CAT.items():
            fila = df[df["metric"] == metric]
            if fila.empty:
                fails.append(f"àncora ponderada CAT {metric}: mètrica absent")
                continue
            got = float(fila["ponderada_catalunya"].iloc[0])
            if not np.isclose(got, esperat, rtol=RTOL_PONDERADA, atol=0.0):
                fails.append(f"àncora ponderada CAT {metric}: esperava {esperat}, tinc {got}")

        # Franja recalculada dels talls declarats aquí.
        def franja_de(p: float) -> str | None:
            if pd.isna(p):
                return None
            for tall, nom in FRANGES:
                if p < tall:
                    return nom
            return None

        pob = df["ine5"].map(pesos["poblacio"])
        esperat_franja = pob.map(franja_de)
        check((df["franja_poblacio"] == esperat_franja).all(),
              "franja_poblacio ≠ franja recalculada dels talls declarats")
        esperat_medf = df.groupby(["metric", "franja_poblacio"])["valor"].transform("median")
        diff_medf = df[~(
            (df["mediana_franja"].isna() & esperat_medf.isna())
            | (df["mediana_franja"] == esperat_medf)
        )]
        check(diff_medf.empty,
              f"mediana_franja ≠ mediana recalculada a {len(diff_medf)} files")
        esperat_nf = df.groupby(["metric", "franja_poblacio"])["valor"].transform("count")
        check((df["n_franja"] == esperat_nf).all(),
              "n_franja ≠ recompte real de valors no nuls per (mètrica, franja)")
        n_franges = int(df["franja_poblacio"].nunique())
        check(n_franges == len(FRANGES),
              f"franges observades = {n_franges} ≠ {len(FRANGES)} declarades")

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
          f"catalans, {n_med} àncores a mà) i cap coincidint amb les bases aparcades; "
          f"ponderades (total ÷ habitants) recalculades amb el pes propi de cada mètrica "
          f"(rtol {RTOL_PONDERADA:g}, {len(PONDERADES_CAT)} àncores a mà) i estratificada "
          f"per {n_franges} franges de població recalculada amb igualtat exacta.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
