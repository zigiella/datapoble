"""Motor de convergència del cabal — creua **turisme** × **sequera** per municipi.

La hipòtesi del nord de *riusdegent* (a provar, NO a assumir): la **pressió
turística / segona residència** —que infla la població real per damunt del padró
(el principi dels *kg de residus*)— hauria de **co-ocórrer amb tensió hídrica**
(més població real → més consum d'aigua → més tensió quan l'embassament baixa).
Aquest mòdul materialitza la lectura de co-ocurrència per als 31 municipis del
Berguedà, **graduada i honesta**: és una hipòtesi, no una causalitat provada.

Entrades (totes **read-only**; el motor no reescriu cap):
  - ``data/events/events_bergueda.parquet``          — rastre de contractació.
  - ``data/events/events_sequera_bergueda.parquet``  — rastre de sequera (ACA).
  - ``data/marts/mart_municipi.parquet``             — mart de Sondeig (pilar 1).

Sortida:
  - ``data/events/convergencia_bergueda.parquet`` — 1 fila per municipi, amb els
    scores de turisme i de sequera, el score/quadrant de convergència i els
    **flags honestos** (vegeu ``CONVERGENCIA_COLUMNS``).

LA MÈTRICA (definida amb Talaia) -------------------------------------------------

1. **Unificació** dels dos rastres del cabal: ``UNION ALL`` sobre ``EVENT_COLUMNS``
   → taula ``events`` única (contractació + sequera). El motor opera sobre ella.

2. **Exposició a la sequera** per municipi (reconstrucció d'intervals). La font de
   sequera és un **històric de transicions**: un estat val fins al canvi següent.
   Ordenant per ``data`` dins de cada ``ine5`` i prenent ``LEAD(data)`` com a fi de
   l'interval (l'últim estat val fins a ``PERIODE_FI``), derivem per municipi:
     - ``sequera_severitat_mitjana`` — mitjana de la severitat (la ``confianca``
       ordinal de l'escala del Pla) **ponderada per dies** de vigència.
     - ``sequera_severitat_pic`` — severitat màxima assolida.
     - ``sequera_mesos_alerta`` — mesos (de 30 dies) en severitat ≥ ``LLINDAR_ALERTA``.

3. **Pressió turística** per municipi, en DOS angles independents (convergència de
   *mètodes*, no només de fonts):
     - **primari, robust** — ``index_turisme`` de Sondeig (0-100, hostaleria
       validada) + ``gap_pernocta_pct`` (població invisible que pernocta).
     - **secundari, feble** — events ``turisme_cultura_events`` de contractació
       del cabal mateix (compte i €). **És FEBLE als micromunicipis**: els pobles
       petits no contracten (Castellar de n'Hug = 0 contractes de turisme propis
       malgrat el Tren del Ciment). Per això NO condueix el senyal; el primari sí.

4. **Lectura de convergència**: turisme (primari ``index_turisme``) × exposició a
   la sequera (``sequera_severitat_mitjana``) → un ``convergencia_score`` (producte
   de tots dos eixos normalitzats a 0-1) i un ``quadrant``. El quadrant alt×alt
   (``alt_turisme_alta_sequera``) és el candidat a «pressió hídrica amplificada per
   població invisible».

FRONTERA HONESTA (disciplina de Talaia, innegociable) --------------------------

  - **Co-ocurrència, NO causalitat.** El score gradua una hipòtesi; no la prova.
  - **La sequera és per Unitat d'Explotació (zona) en origen.** L'ACA declara
    l'estat per UE; tots els municipis d'una UE comparteixen trajectòria (verificat:
    els 31 del Berguedà cauen en 3 UEs — 06 Capçalera, 10 Embassament, 16 Mig
    Llobregat— i dins de cada UE la severitat és **idèntica**). Per tant la sequera
    **NO discrimina entre municipis de la mateixa UE**: aporta el *denominador de
    tensió de la zona*, no una mesura local. La variació fina municipal ve del
    turisme. Cada fila ho marca amb ``flag_sequera_per_zona`` (sempre cert aquí) i
    ``sequera_unitat_explotacio`` (la zona compartida).
  - **Soroll als micromunicipis.** ``index_turisme`` satura a 100 en pobles de
    N petit (el ràtio RTC/habitant es dispara amb pocs habitants), sovint amb
    ``confianca`` baixa al mart. ``flag_turisme_poc_fiable`` ho marca (població <
    ``LLINDAR_POBLACIO_PETITA`` **o** confiança del mart 'baixa').

El motor **no afirma** que la convergència existeixi: la mesura i, si NO surt, ho
diu (vegeu el resum de ``run`` i la bitàcola). Un «no» honest val tant com un «sí».
"""
from __future__ import annotations

import duckdb

from .config import DATA_DIR, EVENTS_DIR, events_path
from .municipis import BERGUEDA_INE5

# Parquets d'entrada (read-only) ------------------------------------------------
CONTRACTACIO_PARQUET = "events_bergueda.parquet"
SEQUERA_PARQUET = "events_sequera_bergueda.parquet"
MART_MUNICIPI = DATA_DIR / "marts" / "mart_municipi.parquet"

# Parquet de sortida ------------------------------------------------------------
DEFAULT_OUTPUT = "convergencia_bergueda.parquet"

# Paràmetres de la mètrica (semàntics, no quantils de la mostra) ----------------
# Fi del període per a l'últim interval obert de sequera. El dataset de l'ACA
# cobreix fins al 2025-05-16 (últim canvi observat al Berguedà); l'estat vigent en
# aquesta data val fins aquí. NO inventem futur més enllà de l'observat.
PERIODE_FI = "2025-05-16"

# Severitat ≥ això compta com a "ALERTA o pitjor" (escala del Pla de sequera:
# ALERTA=0.6). Mesura els mesos de restricció efectiva.
LLINDAR_ALERTA = 0.6

# Llindars del quadrant. **Ancorats a l'escala, no a la mediana de la mostra** —
# perquè la sequera pren només 3 valors (un per UE) i una mediana hi seria
# degenerada (cauria al valor mínim i tot quedaria "alta"). Decisió explícita:
#   - turisme alt: index_turisme ≥ 50 (meitat superior de l'escala 0-100 del mart).
#   - sequera alta: severitat mitjana ≥ 0.45 — separa la capçalera (UE 06, 0.364,
#     que va tocar excepcionalitat només puntualment) del corredor que va seure en
#     excepcionalitat/emergència ~2 anys (UE 10 ≈ 0.49, UE 16 ≈ 0.52).
LLINDAR_TURISME_ALT = 50.0
LLINDAR_SEQUERA_ALTA = 0.45

# Per sota d'aquesta població el senyal de turisme del mart és poc fiable (N petit
# → ràtios per capita que saturen). Marca, no exclou.
LLINDAR_POBLACIO_PETITA = 300

# Etiquetes dels quadrants (vocabulari controlat de la sortida).
QUADRANTS = (
    "alt_turisme_alta_sequera",    # la hipòtesi: candidat a pressió amplificada
    "alt_turisme_baixa_sequera",   # turisme sense tensió hídrica forta
    "baix_turisme_alta_sequera",   # tensió hídrica no explicada per turisme
    "baix_turisme_baixa_sequera",  # ni l'un ni l'altre
)

# Ordre canònic de columnes de la taula de convergència (el contracte de sortida).
CONVERGENCIA_COLUMNS: tuple[str, ...] = (
    "ine5",                          # str  — codi INE5 (clau)
    "nom_muni",                      # str  — nom net del registre
    "comarca",                       # str
    "poblacio",                      # int  — padró (mart)
    # --- turisme (pressió de població invisible) ---
    "turisme_index",                 # float — index_turisme del mart (0-100; PRIMARI, robust)
    "turisme_gap_pernocta_pct",      # float — gap de pernocta del mart (% sobre padró)
    "turisme_score",                 # float — index_turisme/100 (0-1, normalitzat)
    "turisme_contractacio_n",        # int   — events turisme_cultura_events de contractació (SECUNDARI, feble)
    "turisme_contractacio_eur",      # float — € contractats en turisme/cultura
    # --- sequera (tensió hídrica de la zona) ---
    "sequera_unitat_explotacio",     # str   — codi UE ACA (la zona; la sequera es declara aquí)
    "sequera_severitat_mitjana",     # float — severitat mitjana ponderada per dies (0-1; SCORE de sequera)
    "sequera_severitat_pic",         # float — severitat màxima assolida (0-1)
    "sequera_mesos_alerta",          # float — mesos en severitat >= LLINDAR_ALERTA
    "sequera_score",                 # float — = sequera_severitat_mitjana (alias explícit per simetria)
    # --- convergència (la lectura creuada) ---
    "convergencia_score",            # float — turisme_score * sequera_score (0-1; tots dos alts -> alt)
    "quadrant",                      # str   — un de QUADRANTS
    # --- flags honestos (la frontera) ---
    "flag_sequera_per_zona",         # bool  — la sequera és de la UE, no discrimina dins la zona (sempre True aquí)
    "flag_turisme_poc_fiable",       # bool  — micromunicipi / confiança baixa del mart: senyal de turisme sorollós
    "flag_turisme_contractacio_feble",  # bool — el municipi no contracta turisme propi (senyal secundari mut)
)


def _exists_inputs() -> dict[str, bool]:
    """Quins parquets d'entrada hi ha (per a missatges/condicions de test)."""
    return {
        "contractacio": events_path(CONTRACTACIO_PARQUET).exists(),
        "sequera": events_path(SEQUERA_PARQUET).exists(),
        "mart_municipi": MART_MUNICIPI.exists(),
    }


def _muni_registry_relation(registry: dict[str, str] | None = None) -> str:
    """VALUES (...) amb (ine5, nom_muni) del registre net del Berguedà.

    El motor ancora els noms al registre (``BERGUEDA_INE5`` per defecte), no al text
    de cap font (que arriba amb mojibake). Garanteix també els 31 municipis presents
    encara que alguna font no en dugui algun. Els tests poden injectar un
    ``registry`` sintètic.
    """
    reg = registry if registry is not None else BERGUEDA_INE5
    rows = ",\n        ".join(
        f"('{ine5}', '{nom.replace(chr(39), chr(39) * 2)}')"
        for ine5, nom in sorted(reg.items())
    )
    return f"(VALUES\n        {rows}\n    ) AS muni(ine5, nom_muni)"


def build_sql(
    *,
    contractacio_parquet: str,
    sequera_parquet: str,
    mart_parquet: str,
    periode_fi: str = PERIODE_FI,
    llindar_alerta: float = LLINDAR_ALERTA,
    llindar_turisme_alt: float = LLINDAR_TURISME_ALT,
    llindar_sequera_alta: float = LLINDAR_SEQUERA_ALTA,
    llindar_poblacio_petita: int = LLINDAR_POBLACIO_PETITA,
    muni_registry: dict[str, str] | None = None,
) -> str:
    """Construeix el SQL del motor de convergència (DuckDB).

    Tot el pipeline és una sola consulta declarativa sobre ``read_parquet`` (cap
    estat mutable): unió dels rastres → exposició de sequera per intervals →
    turisme del mart + de contractació → creuament i quadrant. Parametritzat per a
    poder-lo córrer sobre fixtures petites als tests (``muni_registry`` injecta el
    registre de municipis del cas sintètic).
    """
    muni = _muni_registry_relation(muni_registry)
    return f"""
    WITH
    -- 1) Unió dels dos rastres del cabal sobre el contracte EVENT_COLUMNS.
    events AS (
        SELECT * FROM read_parquet('{contractacio_parquet}')
        UNION ALL
        SELECT * FROM read_parquet('{sequera_parquet}')
    ),

    -- 2) Exposició a la sequera per municipi (reconstrucció d'intervals).
    --    Un estat val fins al canvi següent; l'últim, fins a PERIODE_FI.
    seq_rows AS (
        SELECT ine5, raw_id AS ue, CAST(data AS DATE) AS d, confianca AS sev
        FROM events
        WHERE tipus_senyal = 'aigua_sequera' AND ine5 IS NOT NULL
    ),
    seq_ordered AS (
        SELECT ine5, ue, d, sev,
               LEAD(d) OVER (PARTITION BY ine5 ORDER BY d) AS d_next
        FROM seq_rows
    ),
    seq_intervals AS (
        SELECT ine5, ue, sev,
               date_diff('day', d, COALESCE(d_next, DATE '{periode_fi}')) AS dies
        FROM seq_ordered
    ),
    sequera AS (
        SELECT
            ine5,
            any_value(ue) AS sequera_unitat_explotacio,
            SUM(sev * dies) / NULLIF(SUM(dies), 0) AS sequera_severitat_mitjana,
            MAX(sev) AS sequera_severitat_pic,
            SUM(CASE WHEN sev >= {llindar_alerta} THEN dies ELSE 0 END) / 30.0
                AS sequera_mesos_alerta
        FROM seq_intervals
        GROUP BY ine5
    ),

    -- 3b) Turisme secundari (FEBLE): contractació turisme/cultura per municipi.
    turisme_con AS (
        SELECT ine5,
               count(*) AS turisme_contractacio_n,
               COALESCE(SUM("import"), 0) AS turisme_contractacio_eur
        FROM events
        WHERE tipus_senyal = 'turisme_cultura_events' AND ambit = 'municipal'
              AND ine5 IS NOT NULL
        GROUP BY ine5
    ),

    -- 3a) Turisme primari (ROBUST): mart de Sondeig.
    mart AS (
        SELECT ine5, poblacio, comarca,
               index_turisme, gap_pernocta_pct, confianca AS conf_mart
        FROM read_parquet('{mart_parquet}')
    ),

    -- Base: 31 municipis del registre (ancora noms i garanteix cobertura).
    base AS (
        SELECT
            muni.ine5,
            muni.nom_muni,
            COALESCE(mart.comarca, 'Berguedà') AS comarca,
            mart.poblacio,
            mart.index_turisme AS turisme_index,
            mart.gap_pernocta_pct AS turisme_gap_pernocta_pct,
            mart.conf_mart,
            COALESCE(tc.turisme_contractacio_n, 0) AS turisme_contractacio_n,
            COALESCE(tc.turisme_contractacio_eur, 0.0) AS turisme_contractacio_eur,
            sq.sequera_unitat_explotacio,
            sq.sequera_severitat_mitjana,
            sq.sequera_severitat_pic,
            sq.sequera_mesos_alerta
        FROM {muni}
        LEFT JOIN mart      ON mart.ine5 = muni.ine5
        LEFT JOIN sequera sq ON sq.ine5  = muni.ine5
        LEFT JOIN turisme_con tc ON tc.ine5 = muni.ine5
    ),

    -- 4) Scores normalitzats + quadrant + flags.
    scored AS (
        SELECT
            ine5, nom_muni, comarca, poblacio,
            turisme_index, turisme_gap_pernocta_pct,
            CAST(turisme_index AS DOUBLE) / 100.0 AS turisme_score,
            turisme_contractacio_n, turisme_contractacio_eur,
            sequera_unitat_explotacio,
            sequera_severitat_mitjana, sequera_severitat_pic, sequera_mesos_alerta,
            sequera_severitat_mitjana AS sequera_score,
            (CAST(turisme_index AS DOUBLE) / 100.0) * sequera_severitat_mitjana
                AS convergencia_score,
            CASE
                WHEN turisme_index >= {llindar_turisme_alt}
                     AND sequera_severitat_mitjana >= {llindar_sequera_alta}
                    THEN 'alt_turisme_alta_sequera'
                WHEN turisme_index >= {llindar_turisme_alt}
                    THEN 'alt_turisme_baixa_sequera'
                WHEN sequera_severitat_mitjana >= {llindar_sequera_alta}
                    THEN 'baix_turisme_alta_sequera'
                ELSE 'baix_turisme_baixa_sequera'
            END AS quadrant,
            -- La sequera SEMPRE és de la zona (UE): mai discrimina dins la UE.
            TRUE AS flag_sequera_per_zona,
            -- Turisme poc fiable: micromunicipi O confiança baixa del mart.
            (poblacio < {llindar_poblacio_petita} OR conf_mart = 'baixa')
                AS flag_turisme_poc_fiable,
            -- El senyal secundari de contractació és mut (el poble no contracta).
            (turisme_contractacio_n = 0) AS flag_turisme_contractacio_feble
        FROM base
    )
    SELECT {", ".join(CONVERGENCIA_COLUMNS)}
    FROM scored
    ORDER BY convergencia_score DESC NULLS LAST
    """


def compute(
    *,
    contractacio_parquet: str | None = None,
    sequera_parquet: str | None = None,
    mart_parquet: str | None = None,
):
    """Executa el motor i retorna el DataFrame de convergència (no escriu res)."""
    cp = contractacio_parquet or str(events_path(CONTRACTACIO_PARQUET).as_posix())
    sp = sequera_parquet or str(events_path(SEQUERA_PARQUET).as_posix())
    mp = mart_parquet or str(MART_MUNICIPI.as_posix())
    sql = build_sql(contractacio_parquet=cp, sequera_parquet=sp, mart_parquet=mp)
    con = duckdb.connect()
    try:
        return con.execute(sql).df()
    finally:
        con.close()


def _summary_from_df(df) -> dict:
    """Resum honest del resultat: comptes per quadrant + lectura de la hipòtesi.

    Inclou el senyal clau per a Talaia: **es confirma la convergència?** La
    resposta es deriva de les dades (no s'assumeix): es mira el quadrant alt×alt i
    quants dels seus municipis són fiables, i la correlació de rang turisme↔sequera.
    """
    quad = (
        df.groupby("quadrant").size().reindex(QUADRANTS, fill_value=0).to_dict()
    )
    conv = df[df["quadrant"] == "alt_turisme_alta_sequera"]
    conv_fiable = conv[~conv["flag_turisme_poc_fiable"]]

    # Correlació de rang (Spearman) turisme vs severitat de sequera sobre els 31.
    sub = df[["turisme_index", "sequera_severitat_mitjana"]].dropna()
    spearman = None
    if len(sub) >= 3 and sub["turisme_index"].nunique() > 1 and sub[
        "sequera_severitat_mitjana"
    ].nunique() > 1:
        spearman = float(
            sub["turisme_index"]
            .rank()
            .corr(sub["sequera_severitat_mitjana"].rank())
        )

    return {
        "n_municipis": int(len(df)),
        "per_quadrant": {k: int(v) for k, v in quad.items()},
        "convergents": sorted(conv["nom_muni"].tolist()),
        "convergents_fiables": sorted(conv_fiable["nom_muni"].tolist()),
        "spearman_turisme_sequera": spearman,
        "unitats_explotacio": sorted(
            x for x in df["sequera_unitat_explotacio"].dropna().unique()
        ),
    }


def run(*, output_name: str = DEFAULT_OUTPUT) -> dict:
    """CLI entrypoint: computa la convergència, escriu el parquet, retorna resum.

    Llegeix els tres parquets d'entrada (tots read-only) i materialitza
    ``data/events/<output_name>`` via DuckDB (mateix patró que ``events.py``).
    """
    inputs = _exists_inputs()
    missing = [k for k, ok in inputs.items() if not ok]
    if missing:
        raise FileNotFoundError(
            "falten parquets d'entrada per al motor de convergència: "
            + ", ".join(missing)
            + " (cal córrer els connectors del cabal i tenir el mart de Sondeig)"
        )

    df = compute()
    EVENTS_DIR.mkdir(parents=True, exist_ok=True)
    out = events_path(output_name)

    con = duckdb.connect()
    try:
        con.register("conv", df)
        con.execute("CREATE TABLE convergencia AS SELECT * FROM conv")
        con.execute("COPY convergencia TO ? (FORMAT PARQUET)", [str(out)])
    finally:
        con.close()

    summary = _summary_from_df(df)
    return {
        "source": "convergencia",
        "parquet": str(out.as_posix()),
        "rows": int(len(df)),
        **summary,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(run(), ensure_ascii=False, indent=2))
