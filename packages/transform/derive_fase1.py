#!/usr/bin/env python3
"""Fase 1 · regenerador OFFLINE dels 3 derivats de mart_municipi.

CONTEXT: `data/raw/` és .gitignore (es regenera des de la ingesta), de manera que
`dbt build` complet no és reproduïble en un checkout net. La definició CANÒNICA dels
3 derivats viu a `packages/transform/models/marts/mart_municipi.sql` (CTEs
`sstats`/`zsig`/`zsig2`/`tipo`/`conf` i les columnes IETR_stock/IETR_impact/
tipologia/confianca_score). Aquest script aplica EXACTAMENT la mateixa lògica
—amb el MATEIX motor (DuckDB) i les MATEIXES expressions SQL— sobre el
`data/marts/mart_municipi.parquet` ja materialitzat, que conté tots els senyals
d'entrada. Així el parquet (artefacte versionat) queda al dia sense raw, i la
fidelitat amb el pipeline queda PROVADA: re-deriva A_resid/B_turis i comprova que
`0.5*IETR_stock + 0.5*IETR_impact == IETR` (la columna ja materialitzada).

Quan hi hagi raw, `dbt build` produeix el MATEIX resultat (mateixa SQL).

Ús:
    python packages/transform/derive_fase1.py            # reescriu el parquet
    python packages/transform/derive_fase1.py --check     # no escriu; falla si caldria

Requereix: duckdb, pandas, pyarrow.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import duckdb
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
MART = REPO / "data" / "marts" / "mart_municipi.parquet"
# Raw del senyal de centralitat (serveis OSM). data/raw/ és gitignored: pot NO existir
# en un checkout net. Si hi és (després de la ingesta), s'usa per BATEJAR el parquet amb
# serveis_estab/serveis_per_1000hab; si no, s'espera que el parquet ja les tingui (cas
# normal un cop materialitzades, perquè el parquet és l'artefacte versionat).
SERVEIS_RAW = REPO / "data" / "raw" / "serveis_osm" / "serveis_osm.parquet"

# Vars del model (dbt_project.yml). Han de coincidir amb les del pipeline. (La base elèctrica L1 ja
# NO és fixa: és base_pred per muni, columna del mart — vegeu kwh_base_ratio.)
POBLACIO_MIN_CONFIANCA = 75
BASE_RESIDENCIAL = 410
BASE_VIDRE = 26.5

# Columnes noves de la Fase 1 (ordre d'inserció just després de IETR_rank).
NEW_COLS = ["IETR_stock", "IETR_impact", "tipologia", "confianca_score", "divergencia_senyals",
            "carrega_funcional_est",
            "residu_base_ratio", "kwh_base_ratio", "vidre_base_ratio"]

# Columnes base del senyal de centralitat (serveis OSM). Es materialitzen al mart just
# després de restauracio_per_1000hab (vegeu mart_municipi.sql · CTE `serveis` + SELECT).
SERVEIS_COLS = ["serveis_estab", "serveis_per_1000hab"]

# Expressions SQL — MIRALL EXACTE de les CTEs de mart_municipi.sql. Es construeixen
# sobre `m` (= mart_municipi ja materialitzat, AUGMENTAT amb serveis_estab/
# serveis_per_1000hab per _load_base) + `nrm` (A_resid/B_turis re-derivats). `m` ve
# d'una relació registrada (m_base), no de read_parquet directe, perquè el senyal de
# centralitat es bateja en pandas abans (vegeu _load_base).
SQL = f"""
with m as (select * from m_base),

-- Re-derivació de l'IETR (winsorització p5/p95 → A_resid/B_turis), idèntica al
-- CTE `norm`+`ietr` del model. quantile_cont = interpolació lineal (= pandas linear).
q as (
    select quantile_cont(pct_noprincipal,0.05) p5_np, quantile_cont(pct_noprincipal,0.95) p95_np,
           quantile_cont(hab_per_hab,0.05)     p5_hh, quantile_cont(hab_per_hab,0.95)     p95_hh,
           quantile_cont(rtc_per_1000hab,0.05) p5_r1, quantile_cont(rtc_per_1000hab,0.95) p95_r1,
           quantile_cont(rtc_per_100hab_viv,0.05) p5_r2, quantile_cont(rtc_per_100hab_viv,0.95) p95_r2
    from m
),
norm as (
    select m.ine5,
      case when q.p95_np=q.p5_np then 0 else (least(greatest(m.pct_noprincipal,q.p5_np),q.p95_np)-q.p5_np)/(q.p95_np-q.p5_np)*100 end as n_np,
      case when q.p95_hh=q.p5_hh then 0 else (least(greatest(m.hab_per_hab,q.p5_hh),q.p95_hh)-q.p5_hh)/(q.p95_hh-q.p5_hh)*100 end as n_hh,
      case when q.p95_r1=q.p5_r1 then 0 else (least(greatest(m.rtc_per_1000hab,q.p5_r1),q.p95_r1)-q.p5_r1)/(q.p95_r1-q.p5_r1)*100 end as n_r1,
      case when q.p95_r2=q.p5_r2 then 0 else (least(greatest(m.rtc_per_100hab_viv,q.p5_r2),q.p95_r2)-q.p5_r2)/(q.p95_r2-q.p5_r2)*100 end as n_r2
    from m cross join q
),
nrm as (
    select ine5, (n_np+n_hh)/2.0 as A_resid, (n_r1+n_r2)/2.0 as B_turis from norm
),

-- CONFIANÇA per tipus_territorial (z de kg/kwh/%no-principal) — espina, tots els munis.
-- Mirall EXACTE de les CTEs sstats/zconf/conf de mart_municipi.sql (escala Catalunya, F2).
sstats as (
    select tipus_territorial,
        avg(kg_hab_any) kg_avg, stddev_pop(kg_hab_any) kg_sd,
        avg(kwh_hab) kwh_avg, stddev_pop(kwh_hab) kwh_sd,
        avg(pct_noprincipal) np_avg, stddev_pop(pct_noprincipal) np_sd
    from m where tipus_territorial is not null group by tipus_territorial
),
zconf as (
    select m.ine5,
        (m.kg_hab_any - s.kg_avg)/nullif(s.kg_sd,0) z_kg,
        (m.kwh_hab - s.kwh_avg)/nullif(s.kwh_sd,0) z_kwh,
        (m.pct_noprincipal - s.np_avg)/nullif(s.np_sd,0) z_np
    from m join sstats s using (tipus_territorial)
),
conf as (
    select z.ine5,
        least(100.0, greatest(0.0,
            40.0 * least(1.0, greatest(0.0,
                (ln(nullif(m.poblacio,0)) - ln({POBLACIO_MIN_CONFIANCA}))
                / (ln({BASE_RESIDENCIAL}) - ln({POBLACIO_MIN_CONFIANCA}))))
            + 35.0 * greatest(0.0, 1.0 -
                (greatest(z.z_kg, z.z_kwh, z.z_np) - least(z.z_kg, z.z_kwh, z.z_np)) / 3.0)
            + 15.0 * (
                (case when m.kg_hab_any is not null then 1 else 0 end
               + case when m.kwh_hab is not null then 1 else 0 end
               + case when m.vidre_hab is not null then 1 else 0 end
               + case when m.pct_noprincipal is not null then 1 else 0 end
               + case when m.poblacio is not null then 1 else 0 end) / 5.0)
            - 10.0 * least(1.0, greatest(0.0,
                (greatest(abs(z.z_kg), abs(z.z_kwh), abs(z.z_np)) - 2.0) / 1.0))
        )) as confianca_score,
        round(100.0 * least(1.0, greatest(0.0,
            (greatest(z.z_kg, z.z_kwh, z.z_np) - least(z.z_kg, z.z_kwh, z.z_np)) / 3.0)), 0) as divergencia_senyals
    from zconf z join m using (ine5)
),

-- TIPOLOGIA (2a onada): NOMÉS munis amb OSM (serveis_estab not null = Berguedà). Referència = els
-- coberts (preserva la classificació provada). Mirall de bstats/btipo/tipo de mart_municipi.sql.
bstats as (
    select
        avg(gap_pernocta_pct) gap_avg, stddev_pop(gap_pernocta_pct) gap_sd,
        avg(index_turisme) tur_avg, stddev_pop(index_turisme) tur_sd,
        avg(pct_noprincipal) np_avg, stddev_pop(pct_noprincipal) np_sd,
        avg(kg_hab_any) kg_avg, stddev_pop(kg_hab_any) kg_sd,
        avg(vidre_hab) vid_avg, stddev_pop(vidre_hab) vid_sd,
        avg(restauracio_per_1000hab) rest_avg, stddev_pop(restauracio_per_1000hab) rest_sd,
        avg(ln(serveis_estab + 1)) lserv_avg, stddev_pop(ln(serveis_estab + 1)) lserv_sd,
        avg(ln(poblacio)) lpop_avg, stddev_pop(ln(poblacio)) lpop_sd,
        avg(ln(carrega_total_est)) lcar_avg, stddev_pop(ln(carrega_total_est)) lcar_sd
    from m where serveis_estab is not null
),
btipo as (
    select m.ine5,
        (m.gap_pernocta_pct - b.gap_avg)/nullif(b.gap_sd,0) z_gap,
        (m.index_turisme - b.tur_avg)/nullif(b.tur_sd,0) z_tur,
        (m.pct_noprincipal - b.np_avg)/nullif(b.np_sd,0) z_np,
        ((m.kg_hab_any - b.kg_avg)/nullif(b.kg_sd,0)
         + (m.vidre_hab - b.vid_avg)/nullif(b.vid_sd,0)
         + (m.restauracio_per_1000hab - b.rest_avg)/nullif(b.rest_sd,0)) / 3.0 z_act,
        (ln(m.serveis_estab + 1) - b.lserv_avg)/nullif(b.lserv_sd,0) z_serv,
        (ln(m.poblacio) - b.lpop_avg)/nullif(b.lpop_sd,0) z_pop,
        (ln(m.carrega_total_est) - b.lcar_avg)/nullif(b.lcar_sd,0) z_carr,
        m.poblacio
    from m cross join bstats b
    where m.serveis_estab is not null
),
tipo as (
    select ine5,
        case
            when poblacio >= 2000 and z_serv >= 0.8 and z_carr >= 0.5 and z_tur <= 0.3 then 'capital_serveis'
            when z_pop <= -0.5 and z_tur <= -0.3 and z_act <= -0.2 and z_gap <= 0.2 then 'buit_administratiu'
            when z_tur >= 0.6 and z_act >= 0.4 and z_gap <= 0.4 then 'excursio'
            when z_gap >= 0.5 and (z_np >= 0.5 or z_tur >= 0.7) then 'segona_residencia'
            when z_gap >= 0.4 and z_tur <= 0.0 then 'dormitori_invisible'
            else 'indeterminat'
        end as tipologia
    from btipo
)

select m.*,
    round(nrm.A_resid, 2) as IETR_stock,
    round(nrm.B_turis, 2) as IETR_impact,
    coalesce(tipo.tipologia, 'pendent') as tipologia,
    round(conf.confianca_score, 1) as confianca_score,
    conf.divergencia_senyals,
    -- DENOMINADOR FUNCIONAL: max(padró, pernocta L1, càrrega L2). coalesce a 0 (pernocta NULL
    -- on no hi ha base_pred); el padró és el SÒL. Mirall del CTE pres de mart_municipi.sql.
    cast(greatest(m.poblacio, coalesce(m.poblacio_pernocta_est,0), coalesce(m.carrega_total_est,0)) as integer) as carrega_funcional_est,
    -- BASE-RATIOS: residus/vidre vs base fixa; elèctric vs base_pred per muni (base unificada L1).
    round(m.kg_hab_any / {BASE_RESIDENCIAL}, 2) as residu_base_ratio,
    round(m.kwh_hab / nullif(m.base_pred,0), 2) as kwh_base_ratio,
    round(m.vidre_hab / {BASE_VIDRE}, 2) as vidre_base_ratio
from m
left join nrm  using (ine5)
left join tipo using (ine5)
left join conf using (ine5)
order by m.ine5
"""


def _load_base() -> pd.DataFrame:
    """Carrega el mart i el BATEJA amb el senyal de centralitat (serveis OSM).

    Garanteix que ``m`` (la base del mirall SQL) tingui ``serveis_estab`` i
    ``serveis_per_1000hab``, materialitzades just després de ``restauracio_per_1000hab``
    (mateixa posició que mart_municipi.sql). Dos camins, idempotents:
      · si el parquet JA les té (cas normal: són l'artefacte versionat) → no toca res;
      · si no (1a materialització, o re-ingesta amb raw fresc) → les calcula del raw de
        serveis_osm (compte absolut → serveis_estab; / poblacio * 1000 → densitat) i les
        insereix. Absència real d'un municipi al raw → 0 (com restauracio_estab).
    Si falten al parquet I no hi ha raw, FALLA amb instrucció (cal ingerir serveis_osm).
    """
    m = pd.read_parquet(MART)
    if all(c in m.columns for c in SERVEIS_COLS):
        return m

    if not SERVEIS_RAW.exists():
        raise SystemExit(
            f"FALLA: el mart no té {SERVEIS_COLS} i no existeix el raw {SERVEIS_RAW}. "
            "Executa la ingesta: python -m packages.ingestion.datapoble_ingestion serveis_osm"
        )

    raw = pd.read_parquet(SERVEIS_RAW)[["ine5", "serveis_estab"]].copy()
    raw["ine5"] = raw["ine5"].astype(str).str.zfill(5)
    m = m.merge(raw, on="ine5", how="left")
    m["serveis_estab"] = m["serveis_estab"].fillna(0).astype(int)
    m["serveis_per_1000hab"] = (
        (m["serveis_estab"] / m["poblacio"].where(m["poblacio"] != 0) * 1000)
        .round(2)
    )
    # Posiciona les dues columnes just després de restauracio_per_1000hab (diff net,
    # coherent amb l'ordre del SELECT del mart).
    cols = [c for c in m.columns if c not in SERVEIS_COLS]
    anchor = cols.index("restauracio_per_1000hab") + 1
    cols = cols[:anchor] + SERVEIS_COLS + cols[anchor:]
    return m[cols]


def build() -> pd.DataFrame:
    m_base = _load_base()
    # Idempotència: si el parquet JA porta els derivats Fase 1 (cas normal — són
    # l'artefacte versionat que aquest mateix script va escriure), treu-los abans de
    # re-derivar. Altrament `select m.*, … tipo.tipologia` xocaria amb la columna
    # homònima de m.* i DuckDB la duplicaria (tipologia_1, IETR_stock_1…), deixant el
    # parquet amb la regla VELLA passada de llarg i la nova al sufix _1. Es re-deriven
    # nets tot seguit; sense raw fresc el resultat és idèntic (mateixos inputs).
    dropped = [c for c in m_base.columns
               if any(c == nc or c.startswith(nc + "_") for nc in NEW_COLS)]
    if dropped:
        m_base = m_base.drop(columns=dropped)
    con = duckdb.connect()
    con.register("m_base", m_base)
    df = con.execute(SQL).fetchdf()
    con.close()
    # Fidelitat: l'IETR re-compost dels components ha de coincidir amb la columna
    # materialitzada. Tolerància 0.02 = el soroll d'ARRODONIMENT: IETR_stock i
    # IETR_impact estan arrodonits a 2 decimals independentment, així que la seva
    # mitjana pot diferir de round(IETR,2) fins a ~0.01 (sense arrodonir, la
    # identitat 0.5*A+0.5*B==IETR és exacta — verificat: diff màx 0.0).
    recomb = (0.5 * df["IETR_stock"] + 0.5 * df["IETR_impact"]).round(2)
    diff = (recomb - df["IETR"].round(2)).abs().max()
    if diff > 0.02:
        raise SystemExit(f"FALLA: IETR re-compost difereix del materialitzat (max {diff}).")
    return df


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="derive_fase1")
    ap.add_argument("--check", action="store_true",
                    help="no escriu; falla (codi 1) si el parquet no té els derivats al dia")
    args = ap.parse_args(argv)

    if not MART.exists():
        print(f"FALLA: no existeix {MART}", file=sys.stderr)
        return 2

    new = build()

    if args.check:
        cur = pd.read_parquet(MART)
        # El senyal de centralitat (serveis) i els derivats Fase 1 han de ser-hi i al dia.
        check_cols = [*SERVEIS_COLS, *NEW_COLS]
        missing = [c for c in check_cols if c not in cur.columns]
        if missing:
            print(f"FALLA (--check): falten columnes {missing} (re-executa sense --check)", file=sys.stderr)
            return 1
        # Compara senyal de centralitat + derivats (la resta de columnes no canvia).
        a = cur[["ine5", *check_cols]].sort_values("ine5").reset_index(drop=True)
        b = new[["ine5", *check_cols]].sort_values("ine5").reset_index(drop=True)
        if not a.equals(b):
            print(f"FALLA (--check): {MART} té columnes desactualitzades (re-executa sense --check)", file=sys.stderr)
            return 1
        print(f"OK (--check): {MART.name} al dia · {len(new)} municipis · "
              f"{len(SERVEIS_COLS)} senyal centralitat + {len(NEW_COLS)} derivats.")
        return 0

    # Reordena: insereix els nous just després de IETR_rank (estètica/diff net).
    cols = list(new.columns)
    for c in NEW_COLS:
        cols.remove(c)
    anchor = cols.index("IETR_rank") + 1
    cols = cols[:anchor] + NEW_COLS + cols[anchor:]
    new = new[cols]

    con = duckdb.connect()
    con.register("new_df", new)
    con.execute(f"COPY (SELECT * FROM new_df ORDER BY ine5) TO '{MART.as_posix()}' (FORMAT PARQUET)")
    con.close()
    print(f"Escrit {MART.relative_to(REPO).as_posix()} · {len(new)} municipis · derivats Fase 1: {', '.join(NEW_COLS)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
