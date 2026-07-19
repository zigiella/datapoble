#!/usr/bin/env python3
"""LLEGAT (2026-07-18) — eina de l'era del model d'interpretació, ARA APARCAT.

Exporta un PAQUET LOCAL de la dada del Berguedà, còmode per treballar la IA (#65).

NOTA: cap workflow la crida i la seva sortida ja NO es committeja (era rància: prometia
«31 municipis» amb el mart escalat a 947). Es conserva com a utilitat local re-executable;
`data/export/` és gitignorat. Si la fase nova no la necessita, es pot retirar sencera.

Llegeix els marts reals (`data/marts/*.parquet`) i el contracte (`semantic/metrics.yml`)
i escriu a `data/export/` quatre formats del MATEIX contingut (els 31 municipis):

  · `bergueda.sqlite`          — BD local consultable amb qualsevol eina SQL (taules
                                 `municipi`, `demografia`, `electoral` + vista `v_complet`).
  · `bergueda_municipis.csv`   — pla, 1 fila/municipi, totes les mètriques (s'obre a Excel).
  · `bergueda_fact_sheets.md`  — el «full de fets» per municipi + comarca: el digest EXACTE
                                 que llegiria el model d'interpretació (per enganxar al prompt).
  · `README.md`                — què és cada fitxer i com consultar la SQLite.

Tot surt de la dada versionada; cap xifra inventada. Re-executable: `python tools/export_bergueda_bundle.py`.
Requereix: pandas, pyarrow (sqlite3 és estàndard).
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
MARTS = REPO / "data" / "marts"
OUT = REPO / "data" / "export"

# Glosses curtes dels arquetips (mirall del contracte / tipologia.ts), per al full de fets.
TIPO_GLOSS = {
    "capital_serveis": "Centre de serveis real: té el comerç i els serveis essencials que serveixen també els pobles veïns.",
    "segona_residencia": "Turisme de pernocta: molts llits (2a residència) que s'omplen caps de setmana i ponts.",
    "excursio": "Turisme d'excursió (de dia): vénen, gasten i marxen; deixen residus i ampolles, no llum de casa.",
    "dormitori_invisible": "Hi dormen sense constar al padró, però amb poca hostaleria.",
    "buit_administratiu": "Micromunicipi tranquil a tots els eixos: padró estable, sense pressió.",
    "indeterminat": "Senyals ambigus o mixtos: el model NO força una etiqueta (territori mixt).",
}


def _n(v, dec=1, suf=""):
    """Format amable d'un número (o «n.d.» si és nul)."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "n.d."
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    if isinstance(v, int):
        return f"{v:,}".replace(",", ".") + suf
    return f"{v:.{dec}f}".replace(".", ",") + suf


def _sg(v, dec=0):
    """Número amb signe explícit (+/−), per als gaps."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "n.d."
    return f"{v:+.{dec}f}".replace(".", ",")


def fact_sheet(r, ctx) -> str:
    """El full de fets d'UN municipi: el digest que llegiria el model (català, citable)."""
    g = TIPO_GLOSS.get(r.get("tipologia"), "—")
    L = []
    L.append(f"### {r['municipi']}  ·  INE {r['ine5']}  ·  {r['comarca']}")
    L.append(f"Població (padró): {_n(r['poblacio'])} hab")
    L.append("")
    L.append(f"TIPOLOGIA: «{r.get('tipologia','n.d.')}» — {g}")
    L.append(f"  Confiança: {r.get('confianca','n.d.')} (score {_n(r.get('confianca_score'))}/100)")
    L.append("")
    L.append("MODEL DE 3 CAPES — INFERÈNCIA (no cens; es llegeix com a rang):")
    L.append(f"  · L1 pernocta (qui DORM aquí, via elèctric domèstic): ~{_n(r['poblacio_pernocta_est'])} hab · gap {_sg(r['gap_pernocta_pct'])}% sobre el padró")
    L.append(f"  · L2 càrrega total (inclou excursionistes de dia, via residus): ~{_n(r['carrega_total_est'])} hab")
    L.append(f"  · L3 pressió turística (via vidre; 0–100, RELATIU a la comarca, 50 = mitjana): {_n(r['index_turisme'])}")
    L.append(f"IETR (exposició turística-residencial): {_n(r['IETR'])} · #{_n(r['IETR_rank'])} de 31 · stock {_n(r['IETR_stock'])} / impact {_n(r['IETR_impact'])}")
    L.append("")
    L.append("SENYALS FÍSICS (mesura):")
    L.append(f"  · elèctric domèstic {_n(r['kwh_hab'])} kWh/hab · residus {_n(r['kg_hab_any'])} kg/hab · vidre {_n(r['vidre_hab'])} kg/hab")
    L.append(f"  · restauració {_n(r['restauracio_estab'])} locals · comerç+serveis {_n(r['serveis_estab'])} establiments  (OSM = mínim observat, no cens)")
    L.append(f"TURISME REGLAT: {_n(r['rtc_total'])} establiments ({_n(r['rtc_per_1000hab'])} per 1000 hab)")
    L.append(f"HABITATGE: {_n(r['pct_noprincipal'])}% no principal · índex d'envelliment {_n(r['index_envelliment'])}")
    L.append("")
    L.append(f"CONTEXT COMARCAL: població mediana {_n(ctx['pop_median'])} hab · IETR mitjà {_n(ctx['ietr_mean'])} · "
             "el Berguedà és rural i envellit, amb un extrem turístic (Gósol, Castellar, Saldes) i una capital de serveis (Berga).")
    mir = ctx.get("mirall", {}).get(r["ine5"], [])
    if mir:
        L.append("MUNICIPIS MIRALL (es comporten igual, no veïns de mapa): " + ", ".join(mir))
    flags = []
    l1, l2 = r.get("poblacio_pernocta_est"), r.get("carrega_total_est")
    if isinstance(l1, (int, float)) and isinstance(l2, (int, float)) and l1 > l2:
        flags.append("L1>L2 (pernocta > càrrega per residus): senyals DIVERGENTS, interpretar amb prudència")
    vid, rest = r.get("vidre_hab"), r.get("restauracio_estab")
    if isinstance(vid, (int, float)) and vid > 30 and (rest == 0 or pd.isna(rest)):
        flags.append("vidre alt amb restauració OSM = 0: probable INFRA-MAPEIG (no absència real)")
    if r.get("confianca") == "baixa":
        flags.append("confiança BAIXA")
    if isinstance(r.get("poblacio"), (int, float)) and r["poblacio"] < 75:
        flags.append("micromunicipi (padró < 75): explosió de denominador, rànquings volàtils")
    if flags:
        L.append("⚠️ FLAGS DE QUALITAT: " + " · ".join(flags))
    cav = "Confiança baixa: senyals que divergeixen o padró petit → llegeix-ho amb prudència." if r.get("confianca") == "baixa" else "Inferència sobre senyals físics, no cens."
    L.append(f"CAVEATS: les 3 capes i els gaps són INFERÈNCIA. {cav}")
    L.append("[Composició d'origen/arrelament: capa SENSIBLE, FORA de la interpretació v1 (vegeu el CSV/SQLite si la vols consultar a banda).]")
    return "\n".join(L)


def comarca_block(muni: pd.DataFrame, ctx) -> str:
    """El full de fets de la COMARCA: agregats + distribució de tipologies."""
    dist = muni["tipologia"].value_counts()
    dist_txt = " · ".join(f"{k} {int(v)}" for k, v in dist.items())
    L = ["## Full de fets · COMARCA (Berguedà)", ""]
    L.append(f"Municipis: {len(muni)} · població total {_n(int(muni['poblacio'].sum()))} hab · població mediana {_n(ctx['pop_median'])} hab")
    L.append(f"DISTRIBUCIÓ DE TIPOLOGIES: {dist_txt}")
    top = muni.nlargest(3, "IETR")[["municipi", "IETR"]]
    L.append("MÉS EXPOSATS (IETR): " + " · ".join(f"{t.municipi} {_n(t.IETR)}" for t in top.itertuples()))
    cap = muni[muni["tipologia"] == "capital_serveis"]["municipi"].tolist()
    L.append("CAPITALS DE SERVEIS: " + (", ".join(cap) if cap else "cap"))
    L.append(f"IETR mitjà comarcal: {_n(ctx['ietr_mean'])}")
    L.append("CAVEATS: z-scores i índexs són COMARCALS (no comparables entre comarques). Tot inferència sobre senyals físics.")
    return "\n".join(L)


MIRALL_FEATURES = ["gap_pernocta_pct", "kg_hab_any", "vidre_hab", "pct_noprincipal",
                   "rtc_per_1000hab", "restauracio_per_1000hab", "serveis_per_1000hab", "index_envelliment"]


def _mirall_map(muni: pd.DataFrame, k: int = 5) -> dict:
    """Per a cada municipi, els k més semblants en COMPORTAMENT (vector per càpita/relatiu,
    z-normalitzat, distància euclidiana). Mirall del que fa lib/analysis/mirall.ts al web."""
    X = muni[MIRALL_FEATURES].astype(float)
    X = X.fillna(X.mean())
    Z = (X - X.mean()) / X.std(ddof=0).replace(0, 1)
    out = {}
    for i, row in muni.iterrows():
        d = ((Z - Z.loc[i]) ** 2).sum(axis=1) ** 0.5
        out[row["ine5"]] = [muni.loc[j, "municipi"] for j in d.sort_values().index if j != i][:k]
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    muni = pd.read_parquet(MARTS / "mart_municipi.parquet")
    demo = pd.read_parquet(MARTS / "mart_demografia.parquet")
    elec = pd.read_parquet(MARTS / "mart_electoral.parquet")

    # --- 1) SQLite: les 3 taules + una vista que les uneix per ine5 -----------
    sqlite_path = OUT / "bergueda.sqlite"
    if sqlite_path.exists():
        sqlite_path.unlink()
    con = sqlite3.connect(sqlite_path)
    muni.to_sql("municipi", con, index=False)
    demo.to_sql("demografia", con, index=False)
    elec.to_sql("electoral", con, index=False)
    # vista: municipi + columnes d'origen i electorals (prefixades) per ine5
    demo_cols = ", ".join(f"d.{c} AS demo_{c}" for c in demo.columns if c not in ("ine5", "codi6", "municipi", "comarca", "poblacio"))
    elec_cols = ", ".join(f"e.{c} AS elec_{c}" for c in elec.columns if c not in ("ine5", "municipi"))
    con.execute(f"CREATE VIEW v_complet AS SELECT m.*, {demo_cols}, {elec_cols} "
                "FROM municipi m LEFT JOIN demografia d ON m.ine5=d.ine5 LEFT JOIN electoral e ON m.ine5=e.ine5")
    con.commit()
    con.close()

    # --- 2) CSV pla (1 fila/municipi, tot unit) -------------------------------
    flat = muni.merge(
        demo.drop(columns=["codi6", "municipi", "comarca", "poblacio"]), on="ine5", how="left", suffixes=("", "_demo")
    ).merge(elec.drop(columns=["municipi"]), on="ine5", how="left", suffixes=("", "_elec"))
    flat = flat.sort_values("ine5")
    flat.to_csv(OUT / "bergueda_municipis.csv", index=False, encoding="utf-8")

    # --- 3) Fulls de fets (el digest del #65) ---------------------------------
    ctx = {"pop_median": float(muni["poblacio"].median()), "ietr_mean": float(muni["IETR"].mean())}
    ctx["mirall"] = _mirall_map(muni)
    parts = ["# Fulls de fets — Berguedà (per a la interpretació, #65)",
             "",
             "*El digest EXACTE que llegiria el model d'interpretació. Enganxa'n un al prompt d'escriptor i itera.*",
             "*Tot surt de la dada real; les 3 capes i els gaps són inferència (no cens). `origen` queda fora de la v1.*",
             "", "---", "", comarca_block(muni, ctx), "", "---", "",
             "## Fulls de fets · MUNICIPIS", ""]
    for _, r in muni.sort_values("IETR", ascending=False).iterrows():
        parts.append(fact_sheet(r, ctx))
        parts.append("")
    (OUT / "bergueda_fact_sheets.md").write_text("\n".join(parts), encoding="utf-8", newline="\n")

    # --- 4) README ------------------------------------------------------------
    readme = f"""# Paquet local — dada del Berguedà (riusdegent)

Els 31 municipis del Berguedà, en quatre formats del MATEIX contingut. Generat per
`tools/export_bergueda_bundle.py` des dels marts reals; re-executa'l quan canviï la dada.

| Fitxer | Què és | Com s'obre |
|---|---|---|
| `bergueda.sqlite` | BD local: taules `municipi`, `demografia`, `electoral` + vista `v_complet` | qualsevol client SQL, o `sqlite3 bergueda.sqlite`, o Python (`sqlite3`) / DB Browser for SQLite |
| `bergueda_municipis.csv` | Pla, 1 fila per municipi, totes les mètriques unides | Excel / Sheets / pandas |
| `bergueda_fact_sheets.md` | El «full de fets» per municipi + comarca (el digest del model #65) | qualsevol editor; enganxa'n un al prompt |
| (parquet original) | `data/marts/*.parquet` — el que la IA consulta amb DuckDB | `duckdb -c "SELECT * FROM 'data/marts/mart_municipi.parquet'"` |

**Consultar la SQLite (exemple):**
```sql
SELECT municipi, tipologia, IETR, confianca FROM municipi ORDER BY IETR DESC;
SELECT * FROM v_complet WHERE municipi = 'Berga';
```

**Significat de cada mètrica:** el diccionari canònic és `semantic/metrics.yml` (label, definició,
font, fórmula i caveat per a cada columna), també visible al **/glossari** del web.

**Honestedat:** les 3 capes (pernocta/càrrega/turisme), els gaps i l'IETR són **inferència**
sobre senyals físics, no cens. Els recomptes d'OSM (restauració, serveis) són un **mínim
observat**. La composició d'**origen** és pública però queda **fora de la interpretació v1**
de la IA (vegeu el guard a `packages/ai`).
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8", newline="\n")

    print(f"Escrit a {OUT.relative_to(REPO).as_posix()}/ : bergueda.sqlite, bergueda_municipis.csv, "
          f"bergueda_fact_sheets.md, README.md ({len(muni)} municipis).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
