#!/usr/bin/env python3
"""Export marts → JSON per al web (Mirador). Pas de pipeline repetible.

Llegeix els marts reals que produeix `packages/transform`
(`data/marts/mart_municipi.parquet` + `mart_electoral.parquet`) i el contracte
semàntic (`semantic/metrics.yml`), i emet un únic artefacte JSON amb la forma
EXACTA que espera el frontend: `MunicipisDataset`
(`packages/web/src/lib/contract/types.ts`, implementada al mock
`packages/web/src/lib/mock/municipis.ts`).

Sortida: `data/web/municipis.bergueda.json` — els 31 municipis del Berguedà amb
dades REALS, llest perquè Mirador substitueixi el mock per un loader sense canviar
la forma.

Frontera honesta (cap valor inventat):
  · El catàleg `metrics` surt del contracte (`metrics.yml`): label/unit/nota/date/
    dimension/status NO es codifiquen aquí, vénen del contracte. Només el `format`
    de presentació i la cadena `source` llegible es resolen amb un mapa fix (mirall
    de com Mirador ja els pinta).
  · `pct_icaen_EFG` = null per a tots: requereix el connector de certificats ICAEN
    (`j6ii-t3w2`), fora d'aquest PR. És un buit honest marcat (status del contracte),
    no un placeholder.
  · Qualsevol valor absent al mart s'emet com a `null` (n. d.), mai s'omple.

Ús:
    python tools/export_web_municipis.py            # des de l'arrel del repo
    python tools/export_web_municipis.py --check     # no escriu; falla si caldria

Requereix: pandas, pyarrow, pyyaml. Els marts han d'existir (executa abans
`packages/transform`: `dbt build`).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
MART_MUNI = REPO / "data" / "marts" / "mart_municipi.parquet"
MART_DEMOG = REPO / "data" / "marts" / "mart_demografia.parquet"
METRICS_YML = REPO / "semantic" / "metrics.yml"
# Sortida per abast (F3): el pilot profund del Berguedà (31, amb política/origen/OSM) i l'espina de
# tot Catalunya (947 — presència/residus/IETR/confiança per a tots; els extres només al Berguedà).
OUT_BERGUEDA = REPO / "data" / "web" / "municipis.bergueda.json"
OUT_CATALUNYA = REPO / "data" / "web" / "municipis.catalunya.json"

# Ordre i claus de mètrica del contracte (= MetricKey a types.ts). Determina
# l'ordre del catàleg `metrics` al JSON (estable → diffs nets).
METRIC_KEYS = [
    "poblacio",
    # Franges d'edat (E12): ja s'ingerien i el mart les llençava; ara es publiquen.
    # pob_15_64 és derivada per resta i pot venir buida si no quadra (mai fabricada).
    "pob_0_14", "pob_15_64", "pob_65_84", "pob_85_mes", "pob_65_mes",
    "hab_total", "hab_principal", "hab_noprincipal",
    "pct_noprincipal", "hab_per_hab", "index_envelliment", "densitat_hab_km2", "renda_neta_persona",
    # Treball (D10). Al contracte hi era des de D1 (`atur_registrat`, amb el seu caveat i la
    # doctrina del «<5»), però NO arribava aquí: conseqüència, l'etiqueta i la font de la
    # targeta d'atur del tauler eren les DUES ÚNIQUES cadenes escrites al codi del front i no
    # llegides del contracte — una violació del mecanisme de la regla de ferro de Bea (C6 §8.1),
    # que exigeix que cada xifra porti la seva font O fórmula i que aquestes surtin del contracte.
    # Només entra al CATÀLEG: el seu valor viu a mart_pols_mensual i se serveix per
    # `tauler.bergueda.json` (cadència mensual pròpia), no a `values` d'aquest fitxer.
    "atur_registrat",
    # Origen: composició i arrelament (capa sensible; lectura ecològica, mai individual).
    "poblacio_nascuda_catalunya", "poblacio_nascuda_resta_espanya",
    "poblacio_nascuda_estranger", "pct_nascuda_estranger",
    "pct_nacionalitat_estrangera", "bretxa_naturalitzacio",
    "delta_pct_estrangera_finestra", "confianca_origen",
    "rtc_total", "rtc_hut", "rtc_per_1000hab", "rtc_per_100hab_viv",
    "kg_hab_any",
    # Senyals físics per càpita (inputs de les 3 capes).
    "kwh_hab", "vidre_hab",
    # Base-ratios: pressió ABSOLUTA vs base residencial (complement dels z-scores comarcals).
    "residu_base_ratio", "kwh_base_ratio", "vidre_base_ratio",
    # 2n proxy d'hostaleria de la capa L3 (restauració OSM, complement del vidre).
    "restauracio_estab", "restauracio_per_1000hab",
    # Senyal de CENTRALITAT funcional (comerç i serveis OSM) — redefineix capital_serveis.
    "serveis_estab", "serveis_per_1000hab",
    # Indicador estrella: MODEL DE 3 CAPES (derived, inferència).
    # L1 població pernocta (la nova «població invisible»):
    "poblacio_pernocta_est", "gap_pernocta", "gap_pernocta_pct",
    # L2 càrrega per residus · denominador funcional (max L1,L2) · confiança.
    # `index_turisme` DEPRECAT (status: deprecated al contracte, #267): FORA dels
    # publicadors (D4) — satura a 100 en 47 munis i és re-escala lossy de vidre_hab;
    # useu vidre_hab (kg/hab). El mart el pot seguir calculant com a rastre.
    "carrega_total_est", "carrega_funcional_est", "confianca",
    # Compatibilitat (model anterior d'una capa), reenquadrades:
    "poblacio_real_est", "gap_abs", "gap_pct", "poblacio_real_rel",
    "pct_icaen_EFG", "IETR", "IETR_rank",
    # FASE 1 · 3 derivats nous (endurir el model): IETR dual + tipologia + score.
    "IETR_stock", "IETR_impact", "tipologia", "confianca_score", "divergencia_senyals",
]

# Format de presentació per clau (MetricFormat a types.ts). No és al contracte
# (és de presentació); mirall de com Mirador ja pinta cada mètrica al mock.
FORMAT_BY_KEY = {
    "poblacio": "integer",
    "pob_0_14": "integer", "pob_15_64": "integer", "pob_65_84": "integer",
    "pob_85_mes": "integer", "pob_65_mes": "integer",
    "hab_total": "integer", "hab_principal": "integer",
    "hab_noprincipal": "integer", "pct_noprincipal": "percent",
    "hab_per_hab": "ratio", "index_envelliment": "decimal", "densitat_hab_km2": "decimal",
    "renda_neta_persona": "integer",
    # Treball: recompte de persones (l'interval del «<5» el pinta el tauler, no el format).
    "atur_registrat": "integer",
    # Origen (composició i arrelament): comptes enters, %s en 0-100, bretxa/delta en punts.
    "poblacio_nascuda_catalunya": "integer", "poblacio_nascuda_resta_espanya": "integer",
    "poblacio_nascuda_estranger": "integer", "pct_nascuda_estranger": "percent",
    "pct_nacionalitat_estrangera": "percent", "bretxa_naturalitzacio": "decimal",
    "delta_pct_estrangera_finestra": "decimal", "confianca_origen": "text",
    "rtc_total": "integer", "rtc_hut": "integer", "rtc_per_1000hab": "decimal",
    "rtc_per_100hab_viv": "decimal", "kg_hab_any": "decimal",
    # Senyals per càpita.
    "kwh_hab": "decimal", "vidre_hab": "decimal",
    "residu_base_ratio": "decimal", "kwh_base_ratio": "decimal", "vidre_base_ratio": "decimal",
    # Restauració (2n proxy hostaleria L3): compte enter + densitat decimal.
    "restauracio_estab": "integer", "restauracio_per_1000hab": "decimal",
    # Centralitat (comerç i serveis OSM): compte enter + densitat decimal.
    "serveis_estab": "integer", "serveis_per_1000hab": "decimal",
    # 3 capes: comptes d'habitants → integer; *_pct ja en 0-100 → percent (mateixa
    # convenció que pct_noprincipal); confianca → text. (index_turisme deprecat, fora.)
    "poblacio_pernocta_est": "integer", "gap_pernocta": "integer",
    "gap_pernocta_pct": "percent", "carrega_total_est": "integer",
    "carrega_funcional_est": "integer",
    # Compatibilitat (model anterior).
    "poblacio_real_est": "integer", "gap_abs": "integer", "gap_pct": "percent",
    "poblacio_real_rel": "integer", "confianca": "text",
    "pct_icaen_EFG": "percent", "IETR": "decimal", "IETR_rank": "rank",
    # FASE 1: IETR dual 0-100 → decimal; tipologia categòrica → text; score 0-100 → decimal.
    "IETR_stock": "decimal", "IETR_impact": "decimal",
    "tipologia": "text", "confianca_score": "decimal", "divergencia_senyals": "integer",
}

# Mapa clau de mètrica → columna del mart corresponent.
COL_MUNI = {
    "poblacio": "poblacio",
    # Franges d'edat (E12).
    "pob_0_14": "pob_0_14", "pob_15_64": "pob_15_64", "pob_65_84": "pob_65_84",
    "pob_85_mes": "pob_85_mes", "pob_65_mes": "pob_65_mes",
    "hab_total": "hab_total",
    "hab_principal": "hab_principal", "hab_noprincipal": "hab_noprincipal",
    "pct_noprincipal": "pct_noprincipal", "hab_per_hab": "hab_per_hab",
    "index_envelliment": "index_envelliment", "densitat_hab_km2": "densitat_hab_km2",
    "renda_neta_persona": "renda_neta_persona",
    "rtc_total": "rtc_total",
    "rtc_hut": "rtc_hut", "rtc_per_1000hab": "rtc_per_1000hab",
    "rtc_per_100hab_viv": "rtc_per_100hab_viv", "kg_hab_any": "kg_hab_any",
    # Senyals per càpita.
    "kwh_hab": "kwh_hab", "vidre_hab": "vidre_hab",
    "residu_base_ratio": "residu_base_ratio", "kwh_base_ratio": "kwh_base_ratio", "vidre_base_ratio": "vidre_base_ratio",
    # Restauració (2n proxy hostaleria L3).
    "restauracio_estab": "restauracio_estab",
    "restauracio_per_1000hab": "restauracio_per_1000hab",
    # Centralitat (comerç i serveis OSM).
    "serveis_estab": "serveis_estab",
    "serveis_per_1000hab": "serveis_per_1000hab",
    # Indicador estrella: model de 3 capes.
    "poblacio_pernocta_est": "poblacio_pernocta_est", "gap_pernocta": "gap_pernocta",
    "gap_pernocta_pct": "gap_pernocta_pct", "carrega_total_est": "carrega_total_est",
    "carrega_funcional_est": "carrega_funcional_est",
    # index_turisme deprecat (#267): fora del publicador — no s'emet ni al catàleg ni als valors.
    # Compatibilitat (model anterior d'una capa).
    "poblacio_real_est": "poblacio_real_est", "gap_abs": "gap_abs",
    "gap_pct": "gap_pct", "poblacio_real_rel": "poblacio_real_rel",
    "confianca": "confianca",
    "pct_icaen_EFG": "pct_icaen_EFG", "IETR": "IETR", "IETR_rank": "IETR_rank",
    # FASE 1 · 3 derivats nous.
    "IETR_stock": "IETR_stock", "IETR_impact": "IETR_impact",
    "tipologia": "tipologia", "confianca_score": "confianca_score",
    "divergencia_senyals": "divergencia_senyals",
}

# Columnes de mart_municipi que són TEXT (no numèriques) → no passen per _num().
TEXT_COLS_MUNI = {"confianca", "tipologia"}

# Capa d'origen (mart_demografia), unida per ine5 com l'electoral. Lectura ECOLÒGICA;
# el secret estadístic dels micromunicipis ja ve cuit com a NULL del connector.
COL_DEMOG = {
    "poblacio_nascuda_catalunya": "poblacio_nascuda_catalunya",
    "poblacio_nascuda_resta_espanya": "poblacio_nascuda_resta_espanya",
    "poblacio_nascuda_estranger": "poblacio_nascuda_estranger",
    "pct_nascuda_estranger": "pct_nascuda_estranger",
    "pct_nacionalitat_estrangera": "pct_nacionalitat_estrangera",
    "bretxa_naturalitzacio": "bretxa_naturalitzacio",
    "delta_pct_estrangera_finestra": "delta_pct_estrangera_finestra",
    "confianca_origen": "confianca_origen",
}
TEXT_COLS_DEMOG = {"confianca_origen"}

# Mètriques de recompte (suma comarcal) vs derivades (no se sumen).
COMARCA_SUM = ["poblacio", "hab_total", "rtc_total"]


def _localized(node: Any) -> dict[str, str] | None:
    """Normalitza un camp del contracte a {ca, es}. Accepta dict o escalar
    (p. ex. unit: "%" → mateix valor a tots dos locales)."""
    if node is None:
        return None
    if isinstance(node, dict):
        return {"ca": str(node.get("ca", "")), "es": str(node.get("es", ""))}
    s = str(node)
    return {"ca": s, "es": s}


def _source_label(spec: dict, sources: dict) -> str:
    """Cadena llegible de la font (mirall del mock): organisme — producte, amb
    `origin_source` afegit per a derivades de datapoble."""
    src = sources.get(spec.get("source", ""), {})
    org = src.get("organisme", spec.get("source", ""))
    prod = src.get("producte")
    label = f"{org} — {prod}" if prod else org
    origin = spec.get("origin_source")
    if origin and origin in sources:
        label += f" · {sources[origin].get('organisme', origin)}"
    return label


def resolve_frescor(spec: dict, sources: dict) -> dict[str, Any]:
    """Frescor d'una mètrica (E5 · esmenes de Bea §3): cada quan s'actualitza, quan es
    va carregar per darrer cop i QUI la refresca.

    Resolució (mai inventada):
      · `actualitzacio` — el que digui la mètrica si té override (p. ex. el bloc del Cens
        d'habitatge 2021, que és decennal encara que EMEX es refresqui cada any); si no,
        el de la seva font.
      · Les DERIVADES (`source: datapoble`) no tenen cadència pròpia: hereten la del seu
        `origin_source`. Si una derivada no en declara cap, s'emet null — un buit visible,
        no un «anual» de consol.
      · `darrera_carrega` i `proces_refresc` vénen SEMPRE de la font efectiva.
        `proces_refresc: "cap"` és una declaració, no un forat: vol dir que aquesta font
        s'actualitza a mà. El tauler l'ha de poder dir.
    """
    src_key = spec.get("source", "")
    src = sources.get(src_key, {})
    # Derivada → la font efectiva de la frescor és l'origen.
    if src.get("actualitzacio") == "derivada":
        origin_key = spec.get("origin_source")
        if origin_key and origin_key in sources:
            src_key, src = origin_key, sources[origin_key]
        else:
            src = {}
    actualitzacio = spec.get("actualitzacio") or src.get("actualitzacio")
    return {
        "actualitzacio": actualitzacio,
        "darrera_carrega": src.get("darrera_carrega"),
        "proces_refresc": src.get("proces_refresc"),
        "font_frescor": src_key or None,
    }


# --- GUARDA DE FRESCOR (D10 · serrell b) ------------------------------------------------
# Una derivada (`source: datapoble`) hereta la cadència del seu `origin_source`. Si no en
# declara cap, `resolve_frescor` emet `actualitzacio: null` — un buit visible, sí, però al
# tauler es tradueix en una targeta que no pot dir de quan és la seva xifra. `rtc_per_1000hab`
# n'és una I ÉS TARGETA VIVA del tauler.
#
# El fix és al contracte (`semantic/metrics.yml`) i el contracte és de Talaia: aquí no s'edita,
# es PROPOSA (bitàcola 2026-07-20, amb el diff exacte). Mentrestant la guarda ja corre, amb les
# excepcions ESCRITES i amb data — que és el contrari de callar-les:
#
#   · IETR / IETR_rank — el null és HONEST i s'hi queda: l'IETR composa residus + ICAEN + RTC
#     + padró; no té UN origen del qual heretar cadència, i triar-ne un seria mentir sobre
#     quan es refresca. La seva absència és la resposta correcta.
#   · rtc_per_1000hab / rtc_per_100hab_viv / hab_per_hab — PENDENTS del contracte. Aquestes
#     SÍ que tenen un origen únic i clar; falta escriure'l. Quan Talaia hi baixi l'`origin_source`,
#     aquesta llista s'ha de buidar sola: si una clau d'aquí deixa d'estar trencada, la guarda
#     també cau (una excepció que sobreviu al seu motiu és una mentida amb bona intenció).
FRESCOR_NULL_HONEST = {"IETR", "IETR_rank"}
FRESCOR_NULL_PENDENT_CONTRACTE = {"rtc_per_1000hab", "rtc_per_100hab_viv", "hab_per_hab"}

# Claus del catàleg que NO porten valor a `values` (no són columnes de cap mart d'aquí).
# Han de ser DECLARADES: un catàleg que promet una mètrica i no la serveix enlloc és una
# altra manera de callar.
#   · atur_registrat — viu a `mart_pols_mensual`; se serveix per `tauler.bergueda.json`
#     amb la seva pròpia cadència mensual (D7). Aquí només n'entra la fitxa del contracte
#     (etiqueta, font, data, caveat), que és el que la targeta del tauler ha de llegir.
SENSE_VALOR_AL_DATASET = {"atur_registrat"}


def check_catalog(metrics: dict[str, dict]) -> list[str]:
    """Guardes del catàleg servit. Retorna la llista d'errors (buida = OK)."""
    errs: list[str] = []

    # 1 · cada clau del catàleg té valor al dataset, o consta com a excepció declarada.
    amb_valor = set(COL_MUNI) | set(COL_DEMOG)
    for key in METRIC_KEYS:
        if key not in amb_valor and key not in SENSE_VALOR_AL_DATASET:
            errs.append(f"{key}: al catàleg però sense valor a `values` ni declarada a "
                        f"SENSE_VALOR_AL_DATASET (el web la prometria i no la trobaria)")
    for key in sorted(SENSE_VALOR_AL_DATASET & amb_valor):
        errs.append(f"{key}: declarada sense valor però SÍ que en té — excepció rància, treu-la")

    # 2 · cap mètrica sense cadència declarada, tret de les excepcions escrites a dalt.
    nulls = {k for k, m in metrics.items() if m["frescor"]["actualitzacio"] is None}
    inesperats = nulls - FRESCOR_NULL_HONEST - FRESCOR_NULL_PENDENT_CONTRACTE
    for key in sorted(inesperats):
        errs.append(f"{key}: `frescor.actualitzacio` null i no declarat — si és derivada, "
                    f"li falta `origin_source` al contracte; la targeta no es podria datar (E5)")
    # Excepcions que ja no calen: es retiren, no s'hereten.
    for key in sorted(FRESCOR_NULL_PENDENT_CONTRACTE - nulls):
        errs.append(f"{key}: ja té cadència al contracte — treu-la de FRESCOR_NULL_PENDENT_CONTRACTE "
                    f"(una excepció que sobreviu al seu motiu amaga el pròxim forat)")
    for key in sorted(FRESCOR_NULL_HONEST - nulls):
        errs.append(f"{key}: declarada com a null honest però ara té cadència — revisa la declaració")
    return errs


def build_metrics(contract: dict) -> dict[str, dict]:
    """Catàleg `metrics` (Record<MetricKey, MetricDef>) des del contracte."""
    raw = contract["metrics"]
    sources = contract.get("sources", {})
    out: dict[str, dict] = {}
    for key in METRIC_KEYS:
        spec = raw[key]
        m: dict[str, Any] = {
            "key": key,
            "label": _localized(spec.get("label")),
            "unit": _localized(spec.get("unit")),
            "dimension": spec.get("dimension"),
            "format": FORMAT_BY_KEY[key],
            "source": _source_label(spec, sources),
        }
        if spec.get("date"):
            m["date"] = str(spec["date"])
        # FRESCOR (E5): `date` diu QUAN és la dada; això diu CADA QUAN es refresca, quan
        # es va carregar i quin procés la manté (o `cap`). Additiu: MetricDef.frescor?
        m["frescor"] = resolve_frescor(spec, sources)
        # formula: REGLA DE FERRO de Bea (C6 §8.1) — cada xifra amb la seva font O fórmula.
        # El contracte porta `formula:` a TOTA mètrica (cadena plana, p. ex. "hab_noprincipal
        # / hab_total * 100" o "directe"). L'emetem tal qual perquè D5 pugui mostrar la
        # procedència de les inferides. Additiu (MetricDef.formula? opcional).
        formula = spec.get("formula")
        if formula:
            m["formula"] = str(formula)
        # definicio: text canònic del «diccionari» que pinta el glossari
        # (definicio.ca/.es del contracte). S'emet només si hi és; si falta, el
        # web recau en `note` (MetricDef.definicio? és opcional).
        definicio = _localized(spec.get("definicio"))
        if definicio:
            m["definicio"] = definicio
        # Unificació 2026-07-17: la clau del contracte és `caveat` (nota queda com a
        # fallback llegat). El camp del JSON web segueix dient-se `note` (contracte del
        # frontend, no es toca): ara hi arriben els 27 caveats, inclosos els que abans
        # es perdien (note:/caveat: mai llegits per aquest export).
        note = _localized(spec.get("caveat") or spec.get("nota"))
        if note:
            m["note"] = note
        # status: explícit al contracte (planned) o public per defecte (visibility).
        m["status"] = spec.get("status") or (
            "public" if spec.get("visibility") == "public" else "planned"
        )
        out[key] = m
    return out


def _num(v: Any) -> Any:
    """Cast a int/float net per a JSON, o None si NaN/None. Enters sense .0."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if pd.isna(v):
        return None
    f = float(v)
    return int(f) if f.is_integer() else f


def build_municipis(muni: pd.DataFrame, demog: pd.DataFrame) -> dict[str, dict]:
    """Files per municipi (Record<Ine5, MunicipiRow>), dades reals."""
    demog_by = demog.set_index("ine5")
    out: dict[str, dict] = {}
    sense_est: list[str] = []  # munis amb confiança però SENSE estimació de pernocta (sanejat)
    for _, r in muni.iterrows():
        ine5 = str(r["ine5"])
        values: dict[str, Any] = {}
        for key, col in COL_MUNI.items():
            if col not in muni.columns:
                values[key] = None
            elif col in TEXT_COLS_MUNI:
                v = r[col]
                values[key] = None if pd.isna(v) else str(v)
            else:
                values[key] = _num(r[col])
        # Capa d'origen des de mart_demografia (unida per ine5). confianca_origen és text;
        # els valors absents (secret estadístic) ja vénen com a NULL.
        if ine5 in demog_by.index:
            dr = demog_by.loc[ine5]
            for key, col in COL_DEMOG.items():
                if col not in demog.columns:
                    values[key] = None
                elif col in TEXT_COLS_DEMOG:
                    v = dr[col]
                    values[key] = None if pd.isna(v) else str(v)
                else:
                    values[key] = _num(dr[col])
        else:
            for key in COL_DEMOG:
                values[key] = None
        # Sanejat d'honestedat: la `confianca` és la confiança EN l'estimació de pernocta (L1 del
        # model de 3 capes). Si no hi ha estimació (poblacio_pernocta_est = null —micromunis sense
        # covariables, exclosos de nivellc_regressio: són el forat 947→927), una confiança és buida;
        # l'anul·lem a la dada publicada. L'IETR NO es toca (es deriva independent: resid/turisme).
        # No és destructiu: el mart (font) conserva l'original; aquí declinem publicar-la i ho registrem.
        if values.get("poblacio_pernocta_est") is None:
            if any(values.get(k) is not None for k in ("confianca", "confianca_score", "divergencia_senyals")):
                sense_est.append(ine5)
            for k in ("confianca", "confianca_score", "divergencia_senyals"):
                values[k] = None
        out[ine5] = {
            "ine5": ine5,
            "nom": str(r["municipi"]),
            "idescat6": str(r["codi6"]),
            "values": values,
        }
    if sense_est:
        mostra = ", ".join(sorted(sense_est)[:5])
        print(f"Sanejat: {len(sense_est)} munis sense estimació de pernocta → confiança anul·lada "
              f"({mostra}{'…' if len(sense_est) > 5 else ''}).", file=sys.stderr)
    return out


def build_comarca(muni: pd.DataFrame, contract: dict, label: str | None = None) -> dict:
    """KPIs agregats REALS: suma per a recomptes; mitjana ponderada per població
    per a ràtios per càpita; mitjana simple per a percentatges/índex. `label` força el
    nom del resum (p. ex. «Catalunya» per a l'abast tot-CAT); si no, el topònim del pilot."""
    pop = muni["poblacio"].astype(float)
    tot_pop = float(pop.sum())
    tot_viv = float(muni["hab_total"].astype(float).sum())

    def wmean_pc(col: str, denom: float, scale: float) -> float:
        # ràtio comarcal = suma(numerador) / denominador comarcal (coherent amb
        # la definició per càpita, no mitjana de ràtios municipals).
        # numerador = ràtio_muni * denom_muni / scale  → reconstrucció robusta.
        num = (muni[col].astype(float) * (pop if "1000" in col else muni["hab_total"].astype(float)) / scale).sum()
        return round(num / denom * scale, 2) if denom else None

    vals: dict[str, Any] = {
        "poblacio": int(tot_pop),
        "hab_total": int(tot_viv),
        "pct_noprincipal": round(
            float(muni["hab_noprincipal"].astype(float).sum()) / tot_viv * 100, 1
        ) if tot_viv else None,
        "rtc_total": int(muni["rtc_total"].astype(float).sum()),
        "rtc_per_1000hab": round(
            float(muni["rtc_total"].astype(float).sum()) / tot_pop * 1000, 2
        ) if tot_pop else None,
        # kg_hab_any comarcal: mitjana ponderada per població (càrrega mitjana real).
        "kg_hab_any": round(
            float((muni["kg_hab_any"].astype(float) * pop).sum()) / tot_pop, 1
        ) if tot_pop else None,
        # IETR comarcal: mediana de la distribució normalitzada (definició del contracte).
        "IETR": round(float(muni["IETR"].astype(float).median()), 1),
    }
    # Nom del resum: forçat (`label`, p. ex. «Catalunya») o el topònim del pilot. Igual en ca/es.
    comarca_nom = label or (str(muni["comarca"].iloc[0]) if "comarca" in muni.columns else "Berguedà")
    return {
        "label": {"ca": comarca_nom, "es": comarca_nom},
        "num_municipis": int(len(muni)),
        "values": vals,
    }


def build_dataset(scope: str = "bergueda") -> dict:
    contract = yaml.safe_load(METRICS_YML.read_text(encoding="utf-8"))
    muni = pd.read_parquet(MART_MUNI)
    demog = pd.read_parquet(MART_DEMOG)

    if scope == "bergueda":
        # Pilot profund: es cenyeix al Berguedà (per comarca real del mart). Manté el resum comarcal.
        muni = muni[muni["comarca"] == "Berguedà"].copy()
        n = len(muni)
        if n != 31:
            print(f"AVÍS: el Berguedà té {n} files (s'esperaven 31).", file=sys.stderr)
        scope_label = "Berguedà (31 municipis)"
        comarca = build_comarca(muni, contract)
    else:  # catalunya: tots els munis; resum agregat a escala «Catalunya».
        n = len(muni)
        if n < 900:
            print(f"AVÍS: tot CAT té {n} files (s'esperaven ~947).", file=sys.stderr)
        scope_label = f"Catalunya ({n} municipis)"
        comarca = build_comarca(muni, contract, label="Catalunya")

    metrics = build_metrics(contract)
    # Les guardes corren SOBRE EL CATÀLEG REAL abans d'escriure'l. Si alguna cau no s'emet
    # res: val més un export que peta que un catàleg que promet el que no pot servir.
    if errs := check_catalog(metrics):
        print(f"FALLA: {len(errs)} guardes del catàleg trencades:", file=sys.stderr)
        for e in errs:
            print(f"  · {e}", file=sys.stderr)
        raise SystemExit(1)

    return {
        "contractVersion": str(contract["meta"]["version"]),
        "scope": scope_label,
        "metrics": metrics,
        "municipis": build_municipis(muni, demog),
        "comarca": comarca,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="export_web_municipis")
    ap.add_argument(
        "--scope", choices=["bergueda", "catalunya"], default="bergueda",
        help="abast: 'bergueda' (pilot profund, 31) o 'catalunya' (espina, 947)",
    )
    ap.add_argument(
        "--check", action="store_true",
        help="no escriu; falla (codi 1) si el JSON al disc no coincideix amb el generat",
    )
    args = ap.parse_args(argv)

    for p in (MART_MUNI, MART_DEMOG, METRICS_YML):
        if not p.exists():
            print(f"FALLA: no existeix {p} (executa abans el pipeline transform)", file=sys.stderr)
            return 2

    out = OUT_BERGUEDA if args.scope == "bergueda" else OUT_CATALUNYA
    dataset = build_dataset(args.scope)
    payload = json.dumps(dataset, ensure_ascii=False, indent=2) + "\n"

    if args.check:
        if not out.exists():
            print(f"FALLA (--check): no existeix {out}", file=sys.stderr)
            return 1
        # Llegim SENSE traducció de finals de línia (newline="") perquè la
        # comparació sigui estable a Windows/Linux: el fitxer sempre s'escriu amb
        # LF (coherent amb `.gitattributes` eol=lf).
        with out.open("r", encoding="utf-8", newline="") as fh:
            on_disk = fh.read()
        if on_disk != payload:
            print(f"FALLA (--check): {out} està desactualitzat (re-executa sense --check)", file=sys.stderr)
            return 1
        print(f"OK (--check): {out} al dia ({len(dataset['municipis'])} municipis).")
        return 0

    out.parent.mkdir(parents=True, exist_ok=True)
    # newline="\n": LF explícit (no CRLF a Windows) → byte-estable amb eol=lf.
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(payload)
    n_muni = len(dataset["municipis"])
    n_metrics = len(dataset["metrics"])
    print(f"Escrit {out.relative_to(REPO).as_posix()} · {n_muni} municipis · {n_metrics} mètriques.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
