# F5.1 · Origen/demografia a tot Catalunya (la capa humana a cada fitxa)

**Data:** 2026-06-24
**Autora:** Talaia (encarna Sondeig).
**Latido (Bea):** «ataquem F5» → vot: **origen/demografia a tot CAT**.
**Pla:** [docs/pla-catalunya-profund.md](../docs/pla-catalunya-profund.md) §F5 (2a onada).

## Què he fet
De-scopat `mart_demografia` als 947 (el raw d'origen ja estava baixat a F1.2b). Ara cada fitxa de
Catalunya té la **composició i l'arrelament** (lectura ecològica): % nascuda fora, % nacionalitat
estrangera, bretxa de naturalització i evolució — amb el secret estadístic dels micromunis respectat.

- **`stg_demografia_origen`**: ja no filtrava per comarca → amb el raw a 947 dona els 947 (el càlcul
  d'origen és per-muni, correcte).
- **`int_demografia_context`**: reescrit perquè el context de comarca sigui **per-muni** (cada `ine5`
  amb el valor de la SEVA comarca, que ve a la seva resposta EMEX), no un sol escalar; el de Catalunya
  és únic (broadcast).
- **`mart_demografia`**: `comarca` per-muni (de stg_residus, 1 fila/muni) i join del context per `ine5`.
- Re-exportat `municipis.catalunya.json` (origen omplert) i `bergueda.json` (sense canvis: el Berguedà
  ja el tenia).

## Verificat
- `mart_demografia` 947 munis · Girona: comarca **Gironès** (per-muni ✓), nascuda fora **29,5%**,
  nacionalitat estrangera 21,9%, bretxa 7,5, confiança alta. **938 munis amb percentatges** (9
  micromunis sota llindar → NULL honest).
- Fitxa de Girona prerenderitzada: secció **Composició · Origen · Arrelament** present.
- `dbt parse` OK · `export --check` (cat+berg) OK · `derive_fase1 --check` OK (mart_municipi intacte) ·
  `npm run build` ✔.

## Següent (resta de F5, no bloquejant)
- Electoral a tot CAT (raw baixat; aparcat per a publicació — decisió oberta).
- Indicadors cat-escala nous al mapa (densitat/renda/gas).
- OSM + subtipus de tipologia a tot CAT (el més pesat; OSM infra-mapa el rural).

— Talaia 🌊
