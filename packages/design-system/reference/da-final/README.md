# Referència · Direcció d'Art FINAL (ronda 2) — target per a Mirador

> Lliurat per la **Directora d'Art** humana (ronda 2) i **aprovat sencer per Bea**.
> Integrat per **Llegenda** al design-system el 2026-06-06.

Aquesta carpeta és el **target visual exacte** de les dues pàgines reals del lloc
(`/resum` i `/mapa`), perquè Mirador les pugui recrear amb fidelitat fent servir el
contracte de tokens `--dp-*` i el mapa MapLibre real.

## Què hi ha

- **`riusdegent - Resum i Mapa.html`** — document principal (les 2 vistes + peu, totes
  les classes). Obrible directament: enllaça els fitxers **reals** del package
  (`../../tokens/tokens.css`, `../../sistema/sistema.css`, `../../aplicacio/aplicacio.css`
  i `.js`), de manera que reflecteix els tokens vigents (marca ocre + `--dp-div2-*`).
- **`assets/`** — marca, logos i favicon (SVG, una tinta **ocre** segons la decisió de Bea).
- **`captures/`** — 7 PNG de referència (estats clau renderitzats):
  1. `01-resum-ca-clar.png` — Resum · CA · clar (hero amb corbes etiquetades + KPIs)
  2. `02-resum-extrems-ca-clar.png` — Dos extrems (eix IETR + targetes Castellar/Berga)
  3. `03-mapa-ca-clar.png` — Mapa · CA · clar (marc del mapa real + lectura + llegenda divergent)
  4. `04-mapa-paletes-ca-clar.png` — Paletes per visualització (divergent destacada)
  5. `05-resum-es-fosc.png` — Resum · ES · fosc
  6. `06-mapa-es-fosc.png` — Mapa · ES · fosc
  7. `07-peu-ca-clar.png` — Peu de pàgina dissenyat (4 columnes + barra legal)

## Com s'ha d'usar (per a Mirador)

1. **No és codi de producció per copiar tal qual.** És el *target*. El CSS i els tokens
   són fidels al contracte `--dp-*` i es poden reaprofitar gairebé literalment; el **JS és
   il·lustratiu** (i18n per diccionari, selector d'indicador, generador de corbes) i s'ha de
   reimplementar amb les eines del projecte (framework d'i18n real, MapLibre real).
2. **El `.map-stage` (`.map-live`) és un placeholder**: en producció hi va el **mapa MapLibre
   real** de `riusdegent.cat/mapa` (geometria oficial INE/IGN, 31 municipis). La resta del
   chrome (selector, llegenda, lectura, `.pal-spec`) ja queda muntada al voltant.
3. **Paletes** (lliurable clau): cada visualització fa servir una paleta concreta. La taula
   indicador→paleta i la regla «sense dada = tramat / confiança baixa = color velat amb
   puntejat» són a `../../cartography/palette.md`.

## Decisions de la DA final aplicades als tokens

- **Marca = ocre `#B5612A`** (`--dp-brand`; en fosc `--dp-brand-dark #E8B567`). Es retira el
  verd com a marca.
- **Paleta divergent «gap» `--dp-div2-0…6`** (teal↔porpra, neutre = `div2-3`). La porpra lliga
  amb `--dp-prov-derived` (inferència).
- **Classificació**: Jenks 5 per al gap; seqüencial per a la resta.

La capa de pàgina canònica viu a `packages/design-system/aplicacio/` (CSS + JS); el chrome i els
components compartits, a `packages/design-system/sistema/`.
