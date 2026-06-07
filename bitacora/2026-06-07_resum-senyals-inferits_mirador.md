# Resum — senyals inferits a les fitxes dels «Dos extrems»

**Fecha:** 2026-06-07
**Autora:** Mirador
**Para:** Talaia (review + merge), Bea (és qui demana que els inferits es vegin)
**Tema:** Les **dues fitxes de municipi** del bloc «Dos extrems» (Castellar de n'Hug vs Berga) de la pàgina **Resum** ara mostren, sota els senyals mesurats de sempre, **els senyals INFERITS** —el cor del projecte: la població invisible— agrupats i visualment separats dels mesurats.
**Status:** avance / handoff

## Contexto
La fitxa només ensenyava 9 files mesurades (`fichaKeys`: habitatge, RTC, residus). Bea vol que els
senyals inferits (les 3 capes del mètode v2) també hi surtin: la dada ja és al dataset
(`data/web/municipis.bergueda.json`, cada municipi té tot el contracte), només calia **mostrar-la**.
Mirador només la pinta; no toca data ni contracte.

## Qué hicimos / decidimos

**1. Dos subgrups nous sota els mesurats, amb rètol mono i separació pedagògica (mesura → inferència).**
Les 9 files mesurades es queden tal qual. A continuació, dins de `.ex__rows`, dos subgrups, cadascun
amb un encapçalament `.ex__grp` (mono, majúscules, color subtil, divisòria superior — la mateixa pell
que `.ex__rank`/`.ex__meta`):
- **«Senyals físics · per càpita»** → `kwh_hab`, `vidre_hab`, `restauracio_per_1000hab`.
- **«Les 3 capes · inferència»** → `gap_pernocta_pct`, `carrega_total_est`, `index_turisme`.
Es renderitzen amb un **snippet `fichaRow`** reusat (mesurats + subgrups comparteixen exactament la
pell `.ex__row`, sense duplicar markup). L'ordre i els codis surten de `fichaGroups`.

**2. El punt de procedència NO es força: el determina el contracte** via `provenanceOf` (mateixa regla
del mapa). Resultat verificat a les dues fitxes:
- Físics: `kwh_hab` **slate** (ICAEN), `vidre_hab` **slate** (ARC). Mesures oficials → mesurada.
- `restauracio_per_1000hab` surt **porpra** perquè la seva `source` del contracte és «datapoble
  (calculat) … OSM via Overpass» → derivada. **És correcte i és el que demanava la tasca** («deixa que
  ho determini el contracte, NO forcis»). És un derivat, no una mesura directa, encara que visqui al
  subgrup «físics» com a input de la capa L3.
- Les 3 capes: `gap_pernocta_pct`, `carrega_total_est`, `index_turisme` totes **porpra** (calculat).

**3. `gap_pernocta_pct` ressaltada** (afegida a `highlightRows`): és la mètrica estrella (població
invisible). Surt amb la banda `.ex__row.hl` a les dues fitxes.

**4. Honestedat amb `restauracio_per_1000hab` (recompte OSM, no cens).** Centralitzat: per a les claus
de `ZERO_IS_ABSENT` un **0 es tracta com a absent** (`null`) → es mostra «n. d.»
(`value_not_available()`), no «0,0», i el punt passa a «sense dada». Helper `effectiveValue(row,key)`
del qual pengen `fmt` i `prov` perquè valor i punt siguin coherents. Castellar (18,1) i Berga (1,6)
tenen valor, així que aquí no s'activa; protegeix qualsevol municipi futur amb 0 d'OSM.

**5. i18n ca/es:** només els 2 rètols nous —`resum_grp_fisics` («Senyals físics · per càpita» /
«Señales físicas · per cápita») i `resum_grp_capes` («Les 3 capes · inferència» / «Las 3 capas ·
inferencia»). Els labels de mètrica segueixen venint del contracte (no codificats).

**6. Bloc A (KPI comarcals): NO tocat.** `dataset.comarca.values` **no** conté `gap_pernocta_pct` ni
`index_turisme` (comprovat), així que —tal com indicava la tasca— no es forcen al Bloc A.

**7. CSS:** una sola regla nova, `.ex__grp`, afegida a `packages/design-system/aplicacio/aplicacio.css`
just després de `.ex__row.hl` (és on viu tota la pell `.ex__*`; així el component queda en un sol lloc).
Tokens existents: `--dp-font-mono`, `--dp-text-subtle`, `--dp-border`. Cap color nou.

## Por qué
La separació mesura→inferència amb dues divisòries mono fa **honesta i llegible** una fitxa més llarga:
es veu d'un cop d'ull què és senyal físic i què és estimació, reforçat pel codi de punts slate/porpra
que ja existia. Reusar el snippet i la pell `.ex__row` garanteix que no s'introdueix cap deute visual.

## Verificación (vite preview del worktree, port 5174)
- `npm ci` (a `packages/web`) OK. **`npm run check` → 0 errors, 0 warnings** (906 fitxers).
  **`npm run build` → prerender net** amb `adapter-static`.
- Les **dues fitxes** mostren els **6 senyals nous** amb els dos subgrups i els punts correctes
  (físics: kwh/vidre slate, restauració porpra; capes: les 3 porpra). `gap_pernocta_pct` ressaltada.
- i18n: `/es/resum` (200) serveix els dos rètols en castellà; cap clau sense resoldre.

## Incidencia detectada (FORA de jurisdicció — flag per a Talaia/dades)
`gap_pernocta_pct` (i `gap_pct`) estan emmagatzemats al dataset com a **fracció 0–1** (Castellar
0.313, Berga -0.021), però el contracte de format del frontend tracta `format: percent` com a **escala
0–100** (vegeu `formatPercent` a `packages/web/src/lib/format.ts`: «els valors ja vénen en 0-100»; i de
fet `pct_noprincipal = 74.28` → «74,3 %» correcte). Conseqüència: la població invisible es mostra com
«0,3 %» quan vol dir **+31,3 %**. La incoherència és **aigua amunt** (el mart calculat desa fracció on
el contracte espera 0–100), no al web.
**No ho he «arreglat» al component amb un ×100 ad-hoc**: trencaria la disciplina «cap component cuina
números», seria inconsistent amb `gap_pct`, i és data/contracte/pipeline (fora de Mirador). **Flagejat
com a tasca a part** perquè es corregeixi a `semantic/metrics.yml` + l'export de Sondeig (o, alternativa,
canviar la convenció a 0–1 i adaptar `formatPercent` + totes les percent).

## Decisiones para Talaia (revisión)
1. **Restauració = porpra** al subgrup «físics»: és el que mana el contracte (derivat OSM). Si es
   prefereix que els 3 inputs físics surtin tots slate, cal canviar-ho al `source` del contracte, no
   a la UI.
2. **`.ex__grp` a `aplicacio.css`** (no estil local a la pàgina) per mantenir el component `.ex` en un
   sol fitxer. Si prefereixes estil scoped a `+page.svelte`, és trivial moure-ho.
3. **Escala de `gap_pernocta_pct`:** decisió de dades, no de frontend — vegeu la incidència i el chip
   de tasca. La fitxa quedarà bé sola quan el valor arribi en 0–100.

## Pendiente
- [ ] **Talaia:** revisar i mergear (CI verd esperat: `web build + check`).
- [ ] **Dades/Sondeig:** corregir l'escala de `gap_pernocta_pct`/`gap_pct` (tasca flagejada).

## Enlaces
- `packages/web/src/routes/resum/+page.svelte` (subgrups, snippet `fichaRow`, `effectiveValue`/`ZERO_IS_ABSENT`)
- `packages/design-system/aplicacio/aplicacio.css` (regla `.ex__grp`)
- `packages/web/messages/{ca,es}.json` (`resum_grp_fisics`, `resum_grp_capes`)
- Font de dades: `data/web/municipis.bergueda.json` (Sondeig)
