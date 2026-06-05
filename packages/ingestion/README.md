# ingestion · Sondeig

Connectors a fonts obertes amb **metadades de procedència** (source, url,
dataset_id, fetched_at, llicència). Cada càrrega deixa la raw a
`data/raw/<source>/` i un sidecar `_provenance.json`.

**Scope:** Berguedà (31 municipis), 5 fonts actives:

| font | dataset | accés | loader |
|---|---|---|---|
| **RTC** (Registre de Turisme) | Socrata `t2h3-cgys` | analisi.transparenciacatalunya.cat | **dlt** |
| **Residus** (ARC) | Socrata `69zu-w48s` | analisi.transparenciacatalunya.cat | **dlt** |
| **Idescat EMEX** | API pròpia (no Socrata) | api.idescat.cat/emex | **requests** |
| **Electoral** (Vots) | Socrata `ntc4-rnwr` | analisi.transparenciacatalunya.cat | **dlt** |
| **ICAEN consum** (elèctric) | Socrata `8idm-becu` | analisi.transparenciacatalunya.cat | **dlt** |

> El spec demanava `dlt` si instal·la (s'usa per a totes les fonts Socrata).
> EMEX no és Socrata —és un JSON niat propi d'Idescat— així que el seu connector
> usa `requests` i aplana a format llarg. **ICAEN consum** (`8idm-becu`) és el
> proxy de presència per a "població real vs padró" (sector USOS DOMÈSTICS); la
> raw guarda tots els sectors i la selecció es fa a transform. Wikipedia pageviews
> queda per a un PR posterior.

## Com executar

```bash
cd packages/ingestion
python -m datapoble_ingestion all            # totes les fonts
python -m datapoble_ingestion rtc            # només RTC
python -m datapoble_ingestion residus
python -m datapoble_ingestion idescat_emex
```

Idempotent: les fonts Socrata fan `write_disposition="replace"`; EMEX
sobreescriu el parquet. Requereix xarxa (APIs públiques, sense autenticació).

## Sortida

```
data/raw/rtc/      rtc_establiments/*.parquet  + _provenance.json   (1 fila/establiment)
data/raw/residus/  residus_municipals/*.parquet + _provenance.json  (1 fila/municipi×any)
data/raw/idescat_emex/ idescat_emex.parquet     + _provenance.json  (long: indicador×municipi)
data/raw/electoral/ electoral_vots/*.parquet    + _provenance.json  (1 fila/convocatòria×municipi×candidatura)
data/raw/icaen_consum/ consum_electric_municipal/*.parquet + _provenance.json (1 fila/municipi×any×sector)
```

`data/raw/` és **gitignored** (es regenera amb un comando). El que es versiona és
la mart (`data/marts/`, la produeix `packages/transform`).

## Estructura

- `config.py` — registre de fonts (mirall de `semantic/metrics.yml`) + constants del pilot.
- `municipis.py` — els 31 codis Idescat del Berguedà + caveat del codi de Gósol.
- `socrata.py` — client SODA mínim (paginació `$limit`/`$offset`).
- `provenance.py` — escriptura de `_provenance.json`.
- `rtc.py`, `residus.py` — pipelines dlt (Socrata → parquet).
- `idescat_emex.py` — parser del JSON niat EMEX → long parquet.

## Procedència (exemple RTC)

```json
{
  "source": "rtc",
  "dataset_id": "t2h3-cgys",
  "url": "https://analisi.transparenciacatalunya.cat/resource/t2h3-cgys.json",
  "llicencia": "Dades Obertes de Catalunya",
  "fetched_at": "2026-06-02T08:37:03+00:00",
  "row_count": 593,
  "query": { "$where": "codi_comarca_idescat='14'" }
}
```

## RGPD

El RTC porta dades del titular (nom, cognoms, CIF). La raw les conserva (fidelitat
a la font), però la mart agregada (transform) no n'arrossega cap: el producte
només exposa **recomptes per municipi**.

## Honest boundaries

- **Corre de veritat:** RTC, residus, EMEX, electoral i **ICAEN consum**
  descarreguen, validen recomptes i escriuen procedència. Verificat contra
  `docs/data-sources.md` i `docs/poblacio-real-fonts.md`.
- **ICAEN consum (`8idm-becu`):** sèrie 2013–2024, sector USOS DOMÈSTICS amb
  cobertura completa dels 31 municipis (zero forats, sobreviu al secret estadístic
  a Castellar). ≠ el connector de **certificats** ICAEN (`j6ii-t3w2`, per a
  `pct_icaen_EFG`), que segueix pendent.
- **Pendent (altres PRs):** certificats ICAEN (`j6ii-t3w2`), Wikipedia pageviews;
  validació d'esquema amb pydantic/pandera; escala Catalunya.
