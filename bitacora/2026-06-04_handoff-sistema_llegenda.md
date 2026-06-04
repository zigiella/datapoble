# Integració del handoff de direcció d'art al sistema de disseny

**Data:** 2026-06-04
**Autora:** Llegenda (direcció d'art)
**Para:** Talaia (review + merge) · Bea (vot de marca, encara pendent)
**Tema:** baixar el handoff professional de la Directora d'Art humana a `packages/design-system` i reconciliar-lo amb l'estat del PR #10.
**Status:** avance

## Contexto
La Directora d'Art humana ha tornat un **handoff** complet (registre visual *Quota*, full topogràfic)
que passa a ser la **identitat canònica** de riusdegent. El PR #10 ja tenia la primera identitat (logo,
favicon SVG, guia, tokens base). Calia integrar el handoff sense trencar el contracte de tokens que ja
consumeix Mirador.

## Qué hicimos / decidimos
- **Tokens (forest + Archivo):**
  - `tokens.css`: `--dp-teal`/`--dp-teal-600` passen de teal antic (`#2A7B7B`/`#216262`) a **forest**
    (`#2F6B4F`/`#255741`). Es **manté el nom** `--dp-teal*` pel contracte; el valor és forest.
  - Afegit `--dp-font-display: 'Archivo', …` (títols/display, 700/800) i `--dp-fw-extrabold: 800`.
  - `tokens.json`: reconciliat `support.teal`/`teal-600` al valor forest (ALIAS de forest, documentat),
    afegit `typography.fontFamily.display` i `fontWeight.extrabold`. `$meta` documenta el handoff i el
    **renombrat diferit a F2** (`--dp-teal*` → `--dp-support-*`).
- **Sistema:** portats `sistema/sistema.css` (biblioteca de components CSS pur) i `sistema/sistema.js`
  (tema persistent, corbes de nivell, ordre de taula, tabs).
- **Referències:** les 3 pàgines a `sistema/reference/` (Fonaments, Components, Pantalles). Ajustats els
  paths relatius (`../sistema.css`, `../../tokens/`, `../../brand/`) a la nova ubicació.
- **Marca:** reemplaçats els 5 SVG (logo, -dark, -mono, mark, favicon) per la versió del handoff (verd
  **forest**).
- **Favicon `.ico`:** generat raster **16/32/48** des de `favicon.svg` (Chromium headless via Playwright
  + Pillow) i versionat a `brand/favicon.ico`. Procediment reproduïble documentat al README.
- **Decisions de Talaia (a `cartography/palette.md`):** classificació coroplètica **5 classes per
  defecte**; **cuantils** per a índexs normalitzats (IETR), **Jenks** per a magnituds crues. La rampa
  seqüencial conserva **6 stops com a recurs de color** (render per defecte 5 classes). La llegenda diu
  sempre **mètode + nº de classes + font·data**. teal→support: **diferit a F2**.

## Por qué
- **No renombrar `--dp-teal*` ara**: Mirador i `sistema.css` ja el consumeixen; canviar el nom trencaria
  el contracte en plena F1. Canviem el *valor* (forest) i deixem el renombrat per a F2, quan Style
  Dictionary regenera des del JSON i podem migrar noms de forma controlada.
- **Display com a token** (no només inline a la CSS): formalitza el contracte perquè Mirador no hagi
  d'endevinar la família de títols.
- **5 classes per defecte**: llegibilitat en municipi petit; la rampa de 5 trams és inequívoca. 6 stops
  es mantenen com a recurs (escala contínua, *swatches*).

## Verificació feta
- `tokens.json` parseja; valors clau correctes (`support.teal == forest == #2F6B4F`).
- Les 3 pàgines de `reference/` carreguen amb Chromium headless **sense errors de consola**; tots els
  assets locals 200 (paths relatius resolen); `--dp-teal = #2F6B4F` i `--dp-font-display` comença per
  `'Archivo'` aplicats; `sistema.js` corre (corbes de nivell dibuixades); tema clar/fosc commuta.
- `favicon.ico` validat: 3 icones 16/32/48, PNG RGBA, transparència de cantonades preservada.

## Pendiente (honest — conservats del handoff)
- [ ] **Validació CVD** pas-a-pas de la rampa seqüencial amb simulador (proposta basada en principis, no
      verificada). **No afirmo que estigui validada.**
- [ ] **Vot de marca de Bea** (i tractament del paràgraf hero); el **dibuix** fi del traç és proposta a
      refinar per un humà.
- [ ] Estil **MapLibre** real del basemap → F2.
- [ ] **Renombrar `--dp-teal*` → `--dp-support-*`** en regenerar amb Style Dictionary → F2.

## Crèdits
La identitat canònica (registre *Quota*, forest, Archivo, component de procedència) és de la **Directora
d'Art humana**. Aquí l'he integrada al package i hi he baixat les decisions de classificació de Talaia.

## Enlaces
- PR #10 (`feat/llegenda-riusdegent`)
- `packages/design-system/README.md` · `tokens/` · `sistema/` · `cartography/palette.md`

— Llegenda
