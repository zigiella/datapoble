"""Verificació OFFLINE de mart_tendencia (D7 · E6) — apte per a CI.

Corre sobre els artefactes VERSIONATS ``data/marts/mart_tendencia.parquet`` i
``data/marts/mart_pols_mensual.parquet`` (cap xarxa, cap clau). Guarda la REGLA
D'HONESTEDAT del §2 de ``docs/ajuntaments/tauler-v2-esmenes-bea.md``, que és vinculant:

  1. Estructura: 947 municipis, format llarg (ine5, metric, comparacio) sense duplicats,
     comarca = l'autoritat territorial (municipis-territori.json), estat ∈ {amb_serie,
     sense_serie}.
  2. **Cap fletxa sense període.** Tota fila amb `direccio` o amb `delta` porta
     `periode_anterior` i `periode_actual`. És LA regla de Bea; si es trenca, el CI cau.
  3. **Cap Δ inventat, cap NULL mut.** Les mètriques sense sèrie hi són EXPLÍCITES
     (estat='sense_serie') amb el motiu escrit —EN ELS DOS IDIOMES (D10)— i sense cap
     delta. Les que en tenen no poden dur estat='sense_serie'.
  3b. **CAP TARGETA DEL TAULER SENSE FILA** (D10 · el forat que va destapar Mirador).
     El conjunt esperat NO s'escriu aquí: es deriva de l'autoritat del front
     (``packages/web/src/lib/govern/kpis.js``, via ``tools/tauler_kpis.py``). Fins a D9
     aquest fitxer comprovava «cap 'sense_serie' sense motiu» però no «cap mètrica del
     tauler sense fila», i per això ``serveis_estab``/``restauracio_estab`` es pintaven
     al tauler sense cap fila al mart —ni tan sols com a 'sense_serie'— sense que res
     petés. Una fila que falta és INVISIBLE; un motiu es pot llegir. Amb la llista
     escrita a mà la propera també hauria faltat: per això ara es deriva.
  4. **Doctrina del «<5» propagada al delta** (C1 §1.1): si un dels dos punts venia
     emmascarat, `delta` és NULL i el que s'emet és l'INTERVAL [delta_min, delta_max].
     Mai un número exacte sobre un punt secret, mai un zero.
  5. **Δ D'ATUR RECALCULAT A MÀ des de mart_pols_mensual**, fila a fila, per a les DUES
     comparacions (mes anterior i mateix mes de l'any anterior) i per als 947 municipis:
     el delta i l'interval del mart han de sortir exactament de restar els dos mesos del
     pols. Prova que la tendència es calcula al transform i no se l'inventa ningú.
  6. Àncores calculades A MÀ (la Pobla de Lillet, 08166) — inclosa la que ensenya per què
     calen les dues comparacions: el juny de 2026 l'atur PUJA contra el mes anterior i
     BAIXA contra el mateix mes de l'any anterior. Amb una sola comparació, el tauler
     hauria triat la narrativa.
  7. Àncora d'origen byte-match contra les esmenes de Bea (§2): +5,61 punts i +64
     persones a la Pobla, finestra 2021→2025.

    python packages/transform/verify_tendencia.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
MART = REPO / "data" / "marts" / "mart_tendencia.parquet"
POLS = REPO / "data" / "marts" / "mart_pols_mensual.parquet"
TERRITORI = REPO / "data" / "web" / "municipis-territori.json"

# La composició del tauler es DERIVA (D10), no es copia: vegeu tools/tauler_kpis.py.
sys.path.insert(0, str(REPO / "tools"))
from tauler_kpis import metriques_del_tauler  # noqa: E402

N_MUNICIPIS = 947

AMB_SERIE = {"atur_registrat", "pct_nacionalitat_estrangera", "poblacio_nacionalitat_estrangera"}
SENSE_SERIE = {
    "poblacio", "pob_0_14", "pob_15_64", "pob_65_84", "pob_85_mes", "index_envelliment",
    "renda_neta_persona", "pct_noprincipal", "kg_hab_any", "kwh_hab", "vidre_hab",
    "rtc_per_1000hab",
    # D10 · les dues que es pintaven i no hi eren (targeta «comerç i serveis», bloc C).
    "serveis_estab", "restauracio_estab",
    # D10 (2a passada) · el LLOC DE NAIXEMENT, que D11 va portar al tauler el mateix dia i
    # que tampoc no tenia fila. Ho va destapar aquesta mateixa guarda al primer CI: és el
    # cas d'ús per al qual es va escriure, i va caure a les poques hores.
    "poblacio_nascuda_catalunya", "poblacio_nascuda_resta_espanya",
    "poblacio_nascuda_estranger", "pct_nascuda_estranger",
}

# Àncores A MÀ · la Pobla de Lillet (08166), atur. Llegides del pols i restades a mà:
#   2025-06 = 34 · 2026-05 = 27 · 2026-06 = 31
#   → vs mes anterior:            31 − 27 = +4  (PUJA)
#   → vs mateix mes any anterior: 31 − 34 = −3  (BAIXA)
# La mateixa xifra puja o baixa segons contra què la miris: per això s'emeten totes dues.
POBLA_ATUR = {
    "mes_anterior": {"periode_actual": "2026-06", "periode_anterior": "2026-05",
                     "valor_actual": 31.0, "valor_anterior": 27.0,
                     "delta": 4.0, "direccio": "puja"},
    "mateix_mes_any_anterior": {"periode_actual": "2026-06", "periode_anterior": "2025-06",
                                "valor_actual": 31.0, "valor_anterior": 34.0,
                                "delta": -3.0, "direccio": "baixa"},
}

# Àncora d'origen: les xifres que les esmenes de Bea citen literalment (§2 del doc).
POBLA_ORIGEN = {
    "pct_nacionalitat_estrangera": 5.61,
    "poblacio_nacionalitat_estrangera": 64.0,
}


def main() -> int:  # noqa: C901 — un verificador és una llista de guardes, no una funció «neta»
    fails: list[str] = []

    for p in (MART, POLS, TERRITORI):
        if not p.exists():
            print(f"FALLA: no existeix {p} (executa la ingesta + dbt build)", file=sys.stderr)
            return 2

    df = pd.read_parquet(MART)
    pols = pd.read_parquet(POLS)
    territori = json.loads(TERRITORI.read_text(encoding="utf-8"))
    ine5_to_comarca = {k: v["comarca"] for k, v in territori.items()}

    def check(cond: bool, msg: str) -> None:
        if not cond:
            fails.append(msg)

    # --- 1. Estructura ---
    # Esquema primer: si falta una columna, val més dir-ho que petar amb un KeyError
    # tres guardes més avall (un traceback també és un CI vermell, però no s'entén).
    COLUMNES = [
        "ine5", "codi6", "municipi", "comarca", "metric", "comparacio", "estat",
        "motiu_ca", "motiu_es", "periode_actual", "periode_anterior", "valor_actual",
        "valor_anterior", "delta", "delta_min", "delta_max", "delta_emmascarat",
        "unitat_delta", "direccio",
    ]
    if manquen := [c for c in COLUMNES if c not in df.columns]:
        print(f"VERIFICACIÓ mart_tendencia: FALLA — columnes absents: {manquen} "
              f"(el parquet és d'abans del canvi d'esquema? regenera'l amb dbt build)",
              file=sys.stderr)
        return 1

    check(not df.empty, "mart buit")
    check(df["ine5"].nunique() == N_MUNICIPIS,
          f"municipis = {df['ine5'].nunique()} ≠ {N_MUNICIPIS}")
    check(df.duplicated(subset=["ine5", "metric", "comparacio"], keep=False).sum() == 0,
          "(ine5, metric, comparacio) amb duplicats")
    check(set(df["estat"]) <= {"amb_serie", "sense_serie"},
          f"estats inesperats: {sorted(set(df['estat']))}")
    falten = (AMB_SERIE | SENSE_SERIE) - set(df["metric"].unique())
    check(not falten, f"mètriques esperades absents del mart: {sorted(falten)}")
    mismatch = df[df["comarca"] != df["ine5"].map(ine5_to_comarca)]
    check(mismatch.empty,
          f"comarca ≠ municipis-territori.json a {len(mismatch)} files")

    # --- 1b. CAP TARGETA DEL TAULER SENSE FILA (D10) ---
    # El conjunt esperat es DERIVA del front (kpis.js), no d'una llista d'aquí: si les dues
    # llistes s'escriuen a mà, divergeixen — i divergir vol dir una targeta muda que ningú veu.
    pintades = metriques_del_tauler(REPO)
    al_mart = set(df["metric"].unique())
    sense_fila = pintades - al_mart
    check(not sense_fila,
          f"{len(sense_fila)} mètriques que el TAULER PINTA i que no tenen cap fila al mart: "
          f"{sorted(sense_fila)} — una fila que falta és invisible (el lector no distingeix "
          f"«no ha canviat» de «no ho sabem»); afegeix-les amb estat 'sense_serie' i el motiu escrit")
    # Coherència de la nostra pròpia declaració: si el mart cobreix una targeta, ha de constar
    # als conjunts d'aquest fitxer (si no, el punt 3 la deixaria passar sense classificar).
    no_declarades = pintades - (AMB_SERIE | SENSE_SERIE)
    check(not no_declarades,
          f"mètriques del tauler no declarades ni a AMB_SERIE ni a SENSE_SERIE: "
          f"{sorted(no_declarades)}")

    # --- 2. CAP FLETXA SENSE PERÍODE (la regla de Bea) ---
    amb_fletxa = df[df["direccio"].notna()]
    sense_periode = amb_fletxa[amb_fletxa["periode_anterior"].isna()
                               | amb_fletxa["periode_actual"].isna()]
    check(sense_periode.empty,
          f"{len(sense_periode)} files amb direcció i SENSE període de comparació "
          f"(p. ex. {sense_periode[['ine5', 'metric']].head(3).values.tolist()})")
    amb_delta = df[df["delta"].notna()]
    check(amb_delta["periode_anterior"].notna().all(),
          "hi ha delta sense període de comparació declarat")

    # --- 3. Cap Δ inventat · cap NULL mut ---
    sense = df[df["estat"] == "sense_serie"]
    check(sense["delta"].isna().all(), "una fila 'sense_serie' porta delta")
    check(sense["delta_min"].isna().all() and sense["delta_max"].isna().all(),
          "una fila 'sense_serie' porta interval de delta")
    # El motiu, EN ELS DOS IDIOMES (D10): el front el pinta literal i no el pot traduir sense
    # inventar-se'l, així que si en falta un el lector d'aquesta llengua es quedaria sense
    # l'única explicació que té la targeta.
    for col in ("motiu_ca", "motiu_es"):
        check(sense[col].notna().all() and sense[col].astype(str).str.len().gt(20).all(),
              f"hi ha una fila 'sense_serie' sense {col} escrit (o massa curt per informar)")
    check((sense["motiu_ca"] != sense["motiu_es"]).all(),
          "hi ha una fila 'sense_serie' amb motiu_ca idèntic a motiu_es "
          "(o s'ha copiat el català al castellà, o falta traduir-lo)")
    check(sense["direccio"].isna().all(), "una fila 'sense_serie' porta direcció")
    check(set(sense["metric"].unique()) == SENSE_SERIE,
          f"conjunt 'sense_serie' inesperat: {sorted(set(sense['metric'].unique()))}")
    amb = df[df["estat"] == "amb_serie"]
    check(set(amb["metric"].unique()) == AMB_SERIE,
          f"conjunt 'amb_serie' inesperat: {sorted(set(amb['metric'].unique()))}")
    check(amb["comparacio"].notna().all(), "hi ha 'amb_serie' sense dir quina comparació és")
    check(amb["motiu_ca"].isna().all() and amb["motiu_es"].isna().all(),
          "una fila 'amb_serie' porta motiu de sense-sèrie")

    # --- 4. Doctrina del «<5» propagada al delta ---
    emm = df[df["delta_emmascarat"]]
    check(emm["delta"].isna().all(),
          f"{int(emm['delta'].notna().sum())} deltes EXACTES sobre un punt emmascarat "
          f"(la diferència amb un «<5» és un interval, no un número)")
    check(emm["delta_min"].notna().all() and emm["delta_max"].notna().all(),
          "hi ha delta emmascarat sense interval [delta_min, delta_max]")
    check((emm["delta_min"] <= emm["delta_max"]).all(), "interval de delta invertit")
    # direcció només quan l'interval NO travessa el zero (llavors està PROVADA)
    mal_dir = emm[emm["direccio"].isin(["puja", "baixa"])
                  & ~((emm["delta_min"] > 0) | (emm["delta_max"] < 0))]
    check(mal_dir.empty,
          f"{len(mal_dir)} files emmascarades amb direcció que l'interval no prova")

    # --- 5. Δ D'ATUR RECALCULAT A MÀ des del pols, per als 947 × 2 comparacions ---
    darrer = str(pols["date"].max())
    any_, mes = int(darrer[:4]), int(darrer[5:7])
    prev_mes = f"{any_ - 1}-12" if mes == 1 else f"{any_}-{mes - 1:02d}"
    prev_any = f"{any_ - 1}-{mes:02d}"
    idx = pols.set_index(["ine5", "date"])
    esperat_rows = []
    for comparacio, periode in (("mes_anterior", prev_mes),
                                ("mateix_mes_any_anterior", prev_any)):
        a = idx.xs(darrer, level="date")
        b = idx.xs(periode, level="date")
        j = a.join(b, lsuffix="_a", rsuffix="_b", how="inner")
        esperat_rows.append(pd.DataFrame({
            "ine5": j.index,
            "metric": "atur_registrat",
            "comparacio": comparacio,
            "periode_actual": darrer,
            "periode_anterior": periode,
            # delta EXACTE només si cap dels dos punts venia emmascarat
            "delta": (j["atur_registrat_a"] - j["atur_registrat_b"]).where(
                ~(j["atur_emmascarat_a"] | j["atur_emmascarat_b"])),
            "delta_min": (j["atur_registrat_min_a"] - j["atur_registrat_max_b"]).astype(float),
            "delta_max": (j["atur_registrat_max_a"] - j["atur_registrat_min_b"]).astype(float),
        }))
    esperat = pd.concat(esperat_rows, ignore_index=True)
    got = df[df["metric"] == "atur_registrat"][
        ["ine5", "metric", "comparacio", "periode_actual", "periode_anterior",
         "delta", "delta_min", "delta_max"]
    ]
    check(len(got) == len(esperat),
          f"files d'atur al mart = {len(got)} ≠ {len(esperat)} recalculades a mà")
    merged = got.merge(esperat, on=["ine5", "metric", "comparacio"],
                       suffixes=("_mart", "_ma"), how="outer", indicator=True)
    check((merged["_merge"] == "both").all(),
          f"{int((merged['_merge'] != 'both').sum())} files d'atur que no casen per clau")
    for col in ("periode_actual", "periode_anterior"):
        bad = merged[merged[f"{col}_mart"] != merged[f"{col}_ma"]]
        check(bad.empty, f"{len(bad)} files amb {col} diferent del recalculat a mà")
    for col in ("delta", "delta_min", "delta_max"):
        m, h = merged[f"{col}_mart"], merged[f"{col}_ma"]
        bad = merged[~((m.isna() & h.isna()) | (m == h))]
        check(bad.empty,
              f"{len(bad)} files amb {col} ≠ el recalculat a mà des de mart_pols_mensual "
              f"(p. ex. {bad[['ine5', 'comparacio']].head(3).values.tolist()})")

    # --- 6. Àncores A MÀ (la Pobla): les dues comparacions, signes oposats ---
    pobla = df[(df["ine5"] == "08166") & (df["metric"] == "atur_registrat")]
    check(not pobla.empty, "la Pobla (08166) sense tendència d'atur")
    for comparacio, esp in POBLA_ATUR.items():
        row = pobla[pobla["comparacio"] == comparacio]
        if row.empty:
            fails.append(f"àncora Pobla atur/{comparacio}: fila absent")
            continue
        r = row.iloc[0]
        for camp, val in esp.items():
            got_v = r[camp]
            ok = (str(got_v) == str(val)) if isinstance(val, str) else (float(got_v) == float(val))
            if not ok:
                fails.append(f"àncora Pobla atur/{comparacio}.{camp}: "
                             f"esperava {val!r}, tinc {got_v!r}")
    # el senyal estacional que justifica les DUES comparacions
    dirs = dict(zip(pobla["comparacio"], pobla["direccio"]))
    check(dirs.get("mes_anterior") == "puja" and dirs.get("mateix_mes_any_anterior") == "baixa",
          "l'àncora d'estacionalitat de la Pobla ha canviat de signe "
          f"({dirs}) — revisa-la abans de tocar el llindar")

    # --- 7. Àncora d'origen byte-match amb les esmenes de Bea (§2) ---
    for metric, esperat_delta in POBLA_ORIGEN.items():
        row = df[(df["ine5"] == "08166") & (df["metric"] == metric)]
        if row.empty:
            fails.append(f"àncora Pobla origen/{metric}: fila absent")
            continue
        r = row.iloc[0]
        if round(float(r["delta"]), 2) != esperat_delta:
            fails.append(f"àncora Pobla origen/{metric}: esperava {esperat_delta}, "
                         f"tinc {r['delta']}")
        if (str(r["periode_anterior"]), str(r["periode_actual"])) != ("2021", "2025"):
            fails.append(f"àncora Pobla origen/{metric}: finestra "
                         f"{r['periode_anterior']}→{r['periode_actual']} ≠ 2021→2025")

    if fails:
        print("VERIFICACIÓ mart_tendencia: FALLA", file=sys.stderr)
        for f in fails:
            print(f"  [x] {f}", file=sys.stderr)
        return 1

    n_emm = int(df["delta_emmascarat"].sum())
    n_indet = int((df["direccio"] == "indeterminat").sum())
    print(f"VERIFICACIÓ mart_tendencia: OK — {len(df)} files "
          f"({df['ine5'].nunique()} municipis), "
          f"{len(AMB_SERIE)} mètriques amb sèrie i {len(SENSE_SERIE)} declarades sense, "
          f"{len(got)} deltes d'atur recalculats a mà byte-match, "
          f"{n_emm} amb interval per «<5» ({n_indet} indeterminats, dits com a tals), "
          f"cap fletxa sense període.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
