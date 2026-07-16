# C1 · Extensió de `semantic/metrics.yml` — contracte de disseny

**De:** Talaia (owner) · **Implementen:** Sondeig (ingesta, D1/D2) i Brúixola (consum xat, X3) · **Data:** 2026-07-16
**Font de veritat:** `docs/spec-ajuntaments-v1.md` §3 (C1), amb les esmenes §10 (E4, E5) manant sobre el §3.
**Ordre:** aquest contracte es fusiona **abans** que cap PR toqui `metrics.yml` per a les famílies d'aquí sota. Les entrades YAML les escriuen els PR implementadors (D1, D2), no aquest document — però amb aquest format i cap altre.

> La regla mare no es toca: **cap mètrica sense fórmula, font i data. Cap número sense procedència.** (capçalera de `metrics.yml`). Tot el que segueix són decisions tancades, no opcions.

## 1. Famílies noves (6) — font, llicència i freqüència exactes

### 1.1 `atur_registrat` — font PRIMÀRIA, mensual
- **Font:** Observatori del Treball i Model Productiu (Generalitat), atur registrat per municipis, via Socrata (`analisi.transparenciacatalunya.cat`). **Llicència:** Dades Obertes de Catalunya. **Freqüència:** mensual.
- El `dataset_id` **no s'inventa aquí**: el fixa Sondeig a D1 amb consulta en viu i byte-match de 3 municipis contra la font (llistó de D1). Cap mètrica pot citar `source: otreball` fins que el bloc `sources:` porti `organisme`, `producte`, `dataset_id` i `llicencia` complets.
- **Client (E5):** es reutilitza el client Socrata de `packages/signals` (`datapoble_signals/socrata.py`). **Prohibit** escriure'n un tercer.
- Destí: `mart_pols_mensual`. Camp `date` en format **`"YYYY-MM"`** (darrer mes carregat, actualitzat pel workflow existent) — primera mètrica mensual del catàleg; el format queda fixat aquí.

### 1.2 Les cinc d'HERMES — font SECUNDÀRIA (agregador), anuals
`rfdb`, `irpf_base`, `habitatges_iniciats`, `habitatges_acabats`, `parc_vehicles`.
- **Font citada:** HERMES (Diputació de Barcelona), dataset «Indicadors socioeconòmics», **sempre com a FONT SECUNDÀRIA/agregador**: la `note` de cada mètrica fa constar l'organisme d'origen que HERMES cita (RFDB → Idescat; IRPF → AEAT; habitatges iniciats/acabats → Dept. de Territori; vehicles → DGT). **Llicència:** condicions del portal HERMES — Sondeig la verifica literalment a D2 i la registra a `sources:` (patró «verificar» de `docs/data-sources.md`); si no és reutilitzable, la família cau i es diu.
- **Freqüència:** anual (camp `date` = `"YYYY"` del període del valor).
- **Regla d'absència (vinculant, del §3):** només famílies **absents de fonts primàries del repo**. Cap mètrica `source: hermes_diba` pot duplicar una família ja coberta per font primària (p. ex. renda ADRH existent ≠ RFDB: conceptes diferents, es mantenen totes dues amb nota de distinció). Si mai una primària entra al repo per una d'aquestes famílies, la mètrica s'hi re-apunta conservant `column` i deixant nota de ruptura de font.
- **Cobertura honesta:** la `note` de cada mètrica declara quants dels 31 municipis tenen valor; on no n'hi ha, **NULL, mai 0**.
- Destí: `mart_municipi`. Els percentils comarcals (D4, `mart_govern`) són transformacions de vista, **no** mètriques noves d'aquest contracte.

Unitats tancades: `atur_registrat` → persones · `rfdb` → €/habitant · `irpf_base` → €/declarant · `habitatges_iniciats`/`habitatges_acabats` → habitatges/any · `parc_vehicles` → vehicles.
Dimensions: `treball` (nova) per a l'atur · `renda` (nova) per a `rfdb`/`irpf_base` · `vivenda` (existent) per als habitatges · `mobilitat` (nova) per als vehicles. `renda_neta_persona` NO es migra de dimensió en aquest contracte.

## 2. Format d'entrada — el del fitxer real, cap camp inventat

Cada mètrica nova segueix **exactament** el format vigent de `metrics.yml`. Camps obligatoris: `label` {ca,es} · `definicio` {ca,es} · `dimension` · `unit` ({ca,es} o literal com `"%"`) · `formula` (`directe` o expressió) · `source` (clau existent al bloc `sources:`) · `date` · `table` · `column` · `visibility` · `visibilitat` (§3). Opcionals: `note` {ca,es}, `synonyms` {ca,es} (obligatori de facto per al xat: tota mètrica nova en porta perquè Brúixola la trobi), `origin_source` (només derivades `source: datapoble`). **No existeix cap camp `format`** al fitxer i aquest contracte no el crea. Entrada modèlica (la resta s'hi emmirallen):

```yaml
atur_registrat:
  label: {ca: Atur registrat, es: Paro registrado}
  definicio:
    ca: "Persones registrades com a aturades al SOC el darrer dia del mes."
    es: "Personas registradas como paradas en el SOC el último día del mes."
  dimension: treball
  unit: {ca: persones, es: personas}
  formula: directe
  source: otreball
  date: "2026-06"          # YYYY-MM, darrer mes carregat
  table: mart_pols_mensual
  column: atur_registrat
  visibility: public
  visibilitat: verd
  synonyms: {ca: [atur, aturats, desocupació], es: [paro, parados, desempleo]}
```

Mètriques derivades (ràtios sobre aquestes famílies) són **fora del mínim C1**: es permeten sota la regla existent (`source: datapoble` + `origin_source` + fórmula explícita), mai com a substitut del valor directe.

## 3. El camp `visibilitat` (E4) — es crea aquí

- `semantic/README.md` promet «visibilitat» i el fitxer no la té: el `visibility` existent és **estat de publicació** (`public`/`planned`), no capa de dades. Es resol creant el camp, no un mecanisme paral·lel.
- **`visibilitat: verd | vermell`**, segons la Convención de visibilidad de `docs/data-sources.md` §0: `verd` = pot sortir al producte; `vermell` = capa interna, mai s'exporta, només agregada. **Regla del join heretada: qualsevol creuament verd × vermell dona vermell.**
- Obligatori a **totes les mètriques noves** d'aquest contracte (les sis famílies: `verd` — tot són dades obertes). Per a les 54 existents queda **declarat com a convenció**: el backfill és un chore separat (owner Talaia), no part dels PR D1/D2.
- Distinció vinculant, escrita al bloc de comentaris de capçalera de `metrics.yml` i a `semantic/README.md` pel primer PR implementador: `visibility` (en) = estat de publicació · `visibilitat` (ca) = capa de dades. Són dos camps, no dos noms del mateix.

## 4. Criteris d'acceptació (verificables per Talaia al PR)

1. Cada entrada nova té tots els camps obligatoris del §2 no buits; `source` resol a una clau de `sources:` amb organisme, producte, accés/`dataset_id` i llicència.
2. `atur_registrat`: byte-match de 3 municipis contra la font (llistó D1) i test de la trampa de codis (Castellar = 08052, la Pobla = 08166) al connector.
3. Mètriques HERMES: `note` amb organisme d'origen + cobertura declarada (n/31); cap família duplicada amb primària existent.
4. `visibilitat` present a les sis famílies; capçalera i README actualitzats amb la convenció del §3.
5. CI verd **offline** (fixtures arxivades; cap test toca xarxa ni claus).

## 5. Dins / fora d'aquest contracte

**Dins:** les 6 famílies del §1, el format §2, la convenció `visibilitat` §3. **Fora:** les mètriques internes municipals (contracte C2), els percentils comarcals (D4), `sample_questions` i catàleg del xat per a les noves (X3, Brúixola), el backfill de `visibilitat` a les 54 existents, la sortida impresa i qualsevol mètrica no llistada aquí.

## 6. Deute anotat (es registra, no es resol aquí)

- **Dedupe dels DOS clients Socrata:** `packages/ingestion/datapoble_ingestion/socrata.py` i `packages/signals/datapoble_signals/socrata.py` són duplicats. Mandat E5: els connectors nous usen el de `signals`; la unificació en un sol client és un PR de chore post-demo. Mentre el deute visqui, cap tercer client.
- **`visibility` vs `status`:** el fitxer ja porta `status: planned` en 2 entrades, solapat amb `visibility: planned`. Fusionar-los és deute del mateix chore de neteja del catàleg, fora d'abast de C1.

*On aquest contracte xoqui amb el repo, mana el repo — i es fa saber per la bitàcora.*
