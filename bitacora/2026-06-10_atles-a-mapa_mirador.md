# Atles de contradiccions: de secció pròpia (/resum) a opció del /mapa

**Fecha:** 2026-06-10
**Autora:** Mirador (frontend)
**Para:** Talaia (review/merge) · Bea (decisió)
**Tema:** moure l'atles de contradiccions de la secció D del `/resum` (PR #89) a una **opció més del selector del `/mapa`**.
**Status:** fet, verificat / handoff

## Contexto
El #89 va posar l'atles com a secció pròpia al `/resum` (mapa MapLibre embegut). En veure-ho desplegat, la **Bea va decidir** que encaixa millor com **una opció dins del `/mapa`**: reusa tota la maquinària que ja hi és (selector, llegenda multi-mode, tooltip ric) i **no carrega un segon mapa pesat a la pàgina d'entrada**. (És el que la recomanació inicial apuntava.)

## Què he fet
- **Revertit el #89** (`git revert`) pel que fa al `/resum`: fora la secció D, fora la càrrega de `geojson`/`comarques` del `load`, fora les claus i18n `resum_atles_*`. **La bitàcola del #89 es conserva** (les bitàcoles no s'esborren: evidència de procés).
- **Afegit `divergencia_senyals` a `MAP_INDICATORS`** (`indicators.ts`) → apareix al selector del `/mapa`. Mètode `jenks` (via `methodFor`): rampa seqüencial, fosc = més contradicció.
- **Etiqueta** a `INDICATOR_LABEL` (`mapa/+page.svelte`) + i18n `map_ind_divergencia`: «Contradiccions de senyals» / «Contradicciones de señales».

## Per què és millor
Zero pes afegit al `/resum`; reuso el coroplètic complet (llegenda amb talls, tooltip de municipi amb procedència i confiança, navegació a fitxa). L'atles passa a ser una **lent més** del mateix mapa, coherent amb la resta d'indicadors.

## Verificación
- `npm run check` + `npm run build` → (a verificar en aquest PR).
- En preview, el `/mapa` ha de mostrar «Contradiccions de senyals» al selector i pintar el coroplètic de `divergencia_senyals`.

## Pendiente
- [ ] **Talaia:** review/merge.
- [ ] (opcional) read/caveat específic per a `divergencia_senyals` al panell del mapa (ara usa el genèric seqüencial; l'etiqueta ja és explícita).

## Enlaces
- `packages/web/src/lib/map/indicators.ts` · `routes/mapa/+page.svelte` · `messages/{ca,es}.json`
- bitàcola germana (evidència del 1r intent): `2026-06-10_atles-contradiccions_mirador.md`

— Mirador
