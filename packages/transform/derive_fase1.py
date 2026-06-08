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

# Vars del model (dbt_project.yml). Han de coincidir amb les del pipeline.
POBLACIO_MIN_CONFIANCA = 75
BASE_RESIDENCIAL = 410

# Columnes noves de la Fase 1 (ordre d'inserció just després de IETR_rank).
NEW_COLS = ["IETR_stock", "IETR_impact", "tipologia", "confianca_score"]

# Expressions SQL — MIRALL EXACTE de les CTEs de mart_municipi.sql. Es construeixen
# sobre `m` (= mart_municipi ja materialitzat) + `nrm` (A_resid/B_turis re-derivats).
SQL = f"""
with m as (select * from read_parquet('{MART.as_posix()}')),

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

-- sstats / zsig / zsig2 / tipo / conf : còpia literal de mart_municipi.sql.
sstats as (
    select
        avg(gap_pernocta_pct) gap_avg, stddev_pop(gap_pernocta_pct) gap_sd,
        avg(index_turisme) tur_avg, stddev_pop(index_turisme) tur_sd,
        avg(pct_noprincipal) np_avg, stddev_pop(pct_noprincipal) np_sd,
        avg(kg_hab_any) kg_avg, stddev_pop(kg_hab_any) kg_sd,
        avg(kwh_hab) kwh_avg, stddev_pop(kwh_hab) kwh_sd,
        avg(vidre_hab) vid_avg, stddev_pop(vidre_hab) vid_sd,
        avg(restauracio_per_1000hab) rest_avg, stddev_pop(restauracio_per_1000hab) rest_sd,
        avg(ln(poblacio)) lpop_avg, stddev_pop(ln(poblacio)) lpop_sd,
        avg(ln(carrega_total_est)) lcar_avg, stddev_pop(ln(carrega_total_est)) lcar_sd
    from m
),
zsig as (
    select m.ine5,
        (m.gap_pernocta_pct - s.gap_avg)/nullif(s.gap_sd,0) z_gap,
        (m.index_turisme - s.tur_avg)/nullif(s.tur_sd,0) z_tur,
        (m.pct_noprincipal - s.np_avg)/nullif(s.np_sd,0) z_np,
        (m.kg_hab_any - s.kg_avg)/nullif(s.kg_sd,0) z_kg,
        (m.kwh_hab - s.kwh_avg)/nullif(s.kwh_sd,0) z_kwh,
        (m.vidre_hab - s.vid_avg)/nullif(s.vid_sd,0) z_vid,
        (m.restauracio_per_1000hab - s.rest_avg)/nullif(s.rest_sd,0) z_rest,
        (ln(m.poblacio) - s.lpop_avg)/nullif(s.lpop_sd,0) z_pop,
        (ln(m.carrega_total_est) - s.lcar_avg)/nullif(s.lcar_sd,0) z_carr
    from m cross join sstats s
),
zsig2 as (select *, (z_kg+z_vid+z_rest)/3.0 as z_act from zsig),
tipo as (
    select ine5,
        case
            when z_pop >= 0.8 and z_carr >= 0.8 and z_tur <= 0.0 then 'capital_serveis'
            when z_pop <= -0.5 and z_tur <= -0.3 and z_act <= -0.2 and z_gap <= 0.2 then 'buit_administratiu'
            when z_tur >= 0.6 and z_act >= 0.4 and z_gap <= 0.4 then 'excursio'
            when z_gap >= 0.5 and (z_np >= 0.5 or z_tur >= 0.7) then 'segona_residencia'
            when z_gap >= 0.4 and z_tur <= 0.0 then 'dormitori_invisible'
            else 'indeterminat'
        end as tipologia
    from zsig2
),
conf as (
    select z.ine5,
        least(100.0, greatest(0.0,
            40.0 * least(1.0, greatest(0.0,
                (ln(m.poblacio) - ln({POBLACIO_MIN_CONFIANCA}))
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
        )) as confianca_score
    from zsig2 z join m using (ine5)
)

select m.*,
    round(nrm.A_resid, 2) as IETR_stock,
    round(nrm.B_turis, 2) as IETR_impact,
    tipo.tipologia,
    round(conf.confianca_score, 1) as confianca_score
from m
join nrm  using (ine5)
join tipo using (ine5)
join conf using (ine5)
order by m.ine5
"""


def build() -> pd.DataFrame:
    con = duckdb.connect()
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
        missing = [c for c in NEW_COLS if c not in cur.columns]
        if missing:
            print(f"FALLA (--check): falten columnes {missing} (re-executa sense --check)", file=sys.stderr)
            return 1
        # Compara els derivats (la resta de columnes no canvia).
        a = cur[["ine5", *NEW_COLS]].sort_values("ine5").reset_index(drop=True)
        b = new[["ine5", *NEW_COLS]].sort_values("ine5").reset_index(drop=True)
        if not a.equals(b):
            print(f"FALLA (--check): {MART} té derivats desactualitzats (re-executa sense --check)", file=sys.stderr)
            return 1
        print(f"OK (--check): {MART.name} al dia · {len(new)} municipis · {len(NEW_COLS)} derivats.")
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
