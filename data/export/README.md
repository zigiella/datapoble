# Paquet local — dada del Berguedà (riusdegent)

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
