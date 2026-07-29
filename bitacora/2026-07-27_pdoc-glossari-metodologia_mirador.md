# P-DOC — Glossari i metodologia, tornats al dia del contracte (Mirador)

**Data:** 2026-07-29 (auditoria de Talaia: 2026-07-27) · **Branca:** `mirador/pdoc-glossari-metodologia` · **Abast:** `packages/web/` + el job `web` del CI.

## Què passava

1. **El glossari descartava 9 mètriques EN SILENCI.** La pàgina agrupava per una `DIM_ORDER`
   escrita a mà que no coneixia ni `treball` ni `origen`: l'atur registrat i les 8 mètriques
   d'origen es publicaven al tauler i el diccionari les callava. Capçalera verificada al render:
   **«26 indicadors»** amb **35 publicables** al contracte. La mateixa forma de bug que D10 va
   tancar al mart: una llista fixa que la propera novetat torna a trencar, sense que res es posi
   vermell.
2. **10 targetes vives del tauler sense fitxa metodològica**: `atur_registrat` (amb la doctrina
   del «<5»!), les 4 franges d'edat (amb la 15-64 DERIVADA per resta), `index_envelliment`,
   `renda_neta_persona`, `serveis_estab`, `rtc_per_100hab_viv` (amb el caveat de barreja de
   vintages) i `rtc_hut`.
3. **Emmarcament enganyós**: `kg_hab_any`, `kwh_hab`, `vidre_hab` i `restauracio_estab` — targetes
   VIVES del tauler (E2 de Bea) — només existien dins el bloc «model aparcat / annex de recerca».
   Un lector n'hauria conclòs que són recerca aparcada.
4. **El 500 latent seguia armat**: `/metodologia` renderitzava `dataset.metrics[key]` sense guarda;
   una clau fantasma als blocs petava el render amb el build verd (ja va passar amb `index_turisme`).
5. Comentaris estàles («l'export encara NO emet `definicio`» — fals des de D4: 55/55) i el «—» com a
   resposta habitual del COM quan el contracte ja emet `formula` a 55/55.

## Què he canviat

### Composició com a font única (patró `kpis.js`)
- **`src/lib/glossari/dims.js`** (nou): `GLOSSARI_DIMS` (ara amb `treball` i `origen`) +
  `GLOSSARI_HIDDEN`. JS pur, importat per la pàgina I pel verificador.
- **`src/lib/metodologia/blocs.js`** (nou): `METODOLOGIA_BLOCS` — 8 blocs, refs A–H:
  A demografia i habitatge (10 fitxes, franges + envelliment + renda incloses) · B **Treball**
  (atur, amb el «<5» al seu advertiment) · C turisme reglat (+`rtc_hut`, +`rtc_per_100hab_viv`) ·
  D **Comerç, serveis i restauració** (els dos comptes OSM + densitats) · E **El pols de la vida
  diària** (residus, elèctric, vidre — VIUS, fora de l'annex) · F energia · G transformació
  demogràfica · H **annex** (només les peces del model: ràtios de base, gap de pernocta,
  càrregues, bandera de confiança).

### `/glossari`
- Agrupa per `GLOSSARI_DIMS`; etiquetes noves `glo_dim_treball` / `glo_dim_origen` (ca+es; la
  d'origen reutilitza el copy ja aprovat de metodologia, «Transformació demogràfica»).
- **Recompte de capçalera: 26 → 35** (derivat, es recalcula sol; verificat al DOM prerenderitzat).
- Comentari estale del capçal esmenat (l'export SÍ emet `definicio`, 55/55).
- Fallback honest si una dimensió llistada quedés sense etiqueta cablada: es pinta la clau del
  contracte (lleig i visible), mai un petament — i el verificador ja ha caigut abans.

### `/metodologia`
- Fitxes noves per a les 10 mètriques vives que no en tenien; el QUÈ surt del **fallback del
  contracte** (`def.definicio`, que ja arriba) — cap definició inventada al front.
- **Indicadors de vida FORA de l'annex** (bloc E viu); les *ràtios* del model es queden a l'annex,
  que és on toca. El copy antic L1/L2/L3 d'aquestes fitxes (`met_kwh_*`, `met_residus_*`,
  `met_vidre_*`, `met_restauracio_*`) retirat: emmarcava targetes vives com a senyals del model
  aparcat; ara parla el contracte. També retirats `met_turisme_what/how`, que ja estaven ORFES
  (cap referència al codi des de la deprecació d'`index_turisme`).
- **El 500 latent, desarmat**: les claus absents del dataset es FILTREN amb un `console.warn` al
  build (prerender); qui cau és la verificació local (`verify-docs.mjs`), mai la pàgina.
- **Fallback del COM en cascada**: copy i18n → fórmula curta → **`def.formula` del contracte** →
  el «—» només com a darrer recurs real. `directe` no es pinta com a literal: es diu amb paraules
  (`met_how_directe`, ca+es), coherent amb `provenanceLine` del tauler.
- **La fitxa ara pinta l'ADVERTIMENT del contracte (`note`)**: hi viatgen la doctrina del «<5» de
  l'atur, la barreja de vintages de `rtc_per_100hab_viv`, el «MÍNIM observat, NO un cens» d'OSM i
  la derivació verificada de `pob_15_64`.
- Seccions posteriors reletrades (model I · ETCA J · rang K).

### Guarda nova: `scripts/verify-docs.mjs` (+ `npm run verify:docs` + pas al job `web` del CI)
Perquè la propera dimensió/targeta no desaparegui en silenci:
1. dimensió del dataset amb mètriques publicables fora de `GLOSSARI_DIMS` → **CAU** (amb els noms);
2. etiqueta `glo_dim_<dim>` absent de ca/es o no cablada a la pàgina → CAU;
3. clau fantasma o duplicada als blocs de metodologia → CAU (el 500 latent, ara vermell en local);
4. targeta VIVA del tauler (`GOVERN_KPIS`, atur i serveis inclosos) sense fitxa en bloc viu → CAU;
5. peça del model aparcat en bloc viu, o mètrica viva dins l'annex → CAU (l'emmarcament, guardat
   pels dos costats);
6. higiene i18n: el copy L1/L2/L3 retirat no pot reaparèixer; les claus noves han d'existir ca+es.

**Provada EN NEGATIU, 4/4** (trencar → caure amb el nom exacte → restaurar → verd):
- treure `treball` de `GLOSSARI_DIMS` → `[x] la dimensió 'treball' té 1 mètriques publicables (atur_registrat) i NO és a GLOSSARI_DIMS`;
- afegir `index_turisme` (el cas real) a un bloc → `[x] la clau 'index_turisme' del bloc B NO és al dataset` (+ la guarda d'emmarcament també el caça);
- treure `kg_hab_any` del bloc viu → `[x] la targeta VIVA del tauler 'kg_hab_any' no té fitxa a cap bloc viu`;
- posar `kwh_base_ratio` al bloc viu → `[x] peça del model aparcat dins el bloc VIU E`.

### Tipus del contracte (`src/lib/contract/types.ts`, jurisdicció meva)
- `MetricKey` += `atur_registrat` (era al JSON servit i no al mirall TS).
- `MetricDef.dimension` += `origen` i `treball` (el mirall anava 2 dimensions enrere del contracte).
- Comentari estale de `definicio` esmenat (mateixa falsedat que al glossari).

## Verificació (LOCAL, no CI — Actions avall fins el dia 1)

- `npm run check` → **0 errors / 0 warnings** (1.245 fitxers).
- `npm run verify:govern` → OK (intacte, 20 KPIs).
- `npm run verify:docs` → OK: **35 publicables / 8 dimensions**, 38 fitxes / 8 blocs, 20/20
  targetes vives amb fitxa — i les 4 proves en negatiu de dalt.
- `npm run build` → verd (vegeu sota).
- Render verificat al **DOM prerenderitzat** (fetch del HTML, no captures): `/ca/glossari` diu
  **«35 indicadors · 8 dimensions»** amb «Atur registrat» i el bloc «Transformació demogràfica»;
  `/ca/metodologia` té la fitxa d'atur amb el «<5», les franges amb la 15-64 derivada per fórmula,
  envelliment, renda, i residus/elèctric/vidre/restauració FORA de l'annex; `/es/*` espejat.
  Cap error de consola.

## Premisses del brief: una imprecisió, cap de falsa

- **«10 mètriques del tauler VIU sense fitxa» — matís:** `rtc_per_100hab_viv` i `rtc_hut` són
  mètriques **publicades al glossari** i al catàleg, però NO són targetes del tauler
  (`GOVERN_KPIS` no les porta). Les altres 8 sí que són targetes vives (l'atur i els serveis via
  els seus `kind` propis). He fet fitxa a totes 10 igualment, que és el que el brief demanava; la
  guarda 2c exigeix fitxa a les targetes REALS del tauler, així que no sobre-promet.
- De pròpia collita (mateixa lògica, no llistades al brief): fitxa també per a
  `serveis_per_1000hab` i `restauracio_per_1000hab` (aquesta SORTINT de l'annex amb el seu compte:
  són derivades vives publicades al glossari, no peces del model).

## Handoffs

- **Cap.** No ha calgut tocar cap dada ni el contracte semàntic: `definicio`/`formula`/`note`
  arribaven a 55/55 i portaven el «<5» i els vintages. (El que semblava forat de dades era tot
  forat de pintura.)

## Pendents que NO toco aquí (ja encuats a next.md)

- Neteja de les entrades mortes de prerender (`/index`, `/day-tripper`) a `svelte.config.js` —
  tasca pròpia de la cua, fora de l'abast de P-DOC.
