# design-system — Llegenda

Sistema visual de **datapoble** (observatori territorial). Font de veritat del que el públic veu:
marca, design tokens, cartografia, dataviz, capa editorial i a11y. S'entrega com a **contractes**
(tokens, estils, specs) que el frontend **Mirador** consumeix; no implementem el frontend aquí.

Brief complet: `docs/art-direction.md` · Spec d'aquest encàrrec: `bitacora/2026-06-02_spec-identitat-tokens_talaia-a-llegenda.md`

## Què hi ha (F1 + handoff de direcció d'art)

```
packages/design-system/
├─ brand/
│  ├─ identity-routes.md      # 3 rutes d'identitat (1r encàrrec; nom ja triat → riusdegent)
│  ├─ brand-guide.md          # guia de marca d'1 pàgina (logo, paleta, to, hero)
│  ├─ riusdegent-logo.svg     # logotip principal (clar) · -dark · -mono  (verd = forest)
│  ├─ riusdegent-mark.svg     # marca / símbol sol (hidrogràfic, forest)
│  ├─ favicon.svg             # favicon (SVG)
│  ├─ favicon.ico             # favicon raster 16/32/48 (generat des de favicon.svg)
│  └─ hero-mockup.html        # mockup de referència del hero (no producte)
├─ tokens/
│  ├─ tokens.json            # contracte visual (W3C DTCG / Style Dictionary): color, tipografia,
│  │                         #   espaiat, radis, ombres, breakpoints, moviment + paletes de dada
│  └─ tokens.css             # variables CSS (--dp-*), espill del JSON, tema clar/fosc, reduced-motion
├─ sistema/                  # biblioteca de components (registre QUOTA) — handoff de direcció d'art
│  ├─ sistema.css            # components en CSS pur (.btn .input .card .tbl .legend .prov…) sobre els --dp-*
│  ├─ sistema.js             # comportament compartit (tema persistent, corbes de nivell, ordre de taula, tabs)
│  └─ reference/             # pàgines de referència de disseny (NO producte; Mirador les recrea)
│     ├─ Fonaments.html      #   color, tipografia, espai, radis, ombres, moviment
│     ├─ Components.html     #   tots els components, vius
│     └─ Pantalles.html      #   web Mirador (3 columnes) + mòbil consulta
└─ cartography/
   └─ palette.md             # spec paleta coroplètica + classificació (cuantils/Jenks, 5 classes)
```

> Les pàgines de `sistema/reference/` són **referències de disseny** (prototips HTML), no codi de
> producció. Enllacen els contractes reals per ruta relativa (`../sistema.css`, `../../tokens/tokens.css`,
> `../../brand/`); obre-les amb un servidor de fitxers estàtic des de l'arrel del package.

## Com ho consumeix Mirador

1. Importar `tokens/tokens.css` a l'arrel de l'app → totes les variables `--dp-*` disponibles.
2. Usar els **àlies semàntics** (`--dp-bg`, `--dp-text`, `--dp-border`, `--dp-link`…) als components,
   no els primitius directament, perquè el tema (clar/fosc) funcioni sol.
3. **Components:** `sistema/sistema.css` és la biblioteca en CSS pur (framework-agnòstica). Importar tal
   qual, o envoltar cada classe en un component del framework. `sistema/sistema.js` és el comportament
   compartit (tema persistit a `localStorage['rdg-theme']`, corbes de nivell, ordre de taula, tabs).
4. **Tipografia:** títols/display en `--dp-font-display` (Archivo 700/800); UI i dada en `--dp-font-sans`
   (Inter). Carregar Archivo + Inter + IBM Plex Serif/Mono (veure `<link>` de Google Fonts a les pàgines
   de `sistema/reference/`).
5. Mapes/charts: paletes de dada a `--dp-exposure-*` (seqüencial), `--dp-div-*` (diverging),
   `--dp-cat-*` (qualitativa). Mètode de classificació segons `cartography/palette.md`.
6. Superfícies amb número: classe `.dp-tnum` o `font-variant-numeric: tabular-nums` (cifres tabulars).

## Decisions clau

- **Registre visual "Quota"** (full topogràfic: corbes de nivell, cotes, tipus de mapa). El materialitza
  `sistema/` sobre els tokens.
- **Tipografia:** **Archivo** (700/800, `--dp-font-display`) per a títols/display — afegit per direcció
  d'art. Inter (UI/dada, cifres tabulars, `--dp-font-sans`) + IBM Plex Serif (lectura llarga) + IBM Plex
  Mono. Totes amb diacrítiques catalanes completes (à è é í ï ò ó ú ü ç l·l) i `tnum`.
- **Verd de marca = forest `#2F6B4F`** (direcció d'art: abans teal `#2A7B7B`). Es manté el nom de token
  `--dp-teal*` pel contracte, però el **valor és forest**; renombrat a `--dp-support-*` diferit a F2
  (veure "Estat i abast").
- **Procedència del dada:** component signatura `.prov--measured/-derived/-negative` (tokens
  `--dp-prov-*`) que materialitza el contracte editorial **cap número sense origen**.
- **Paleta de dada:** seqüencial terra "exposició" (6 stops com a recurs; **render per defecte 5
  classes**) i diverging teal↔marró, **sense vermell-verd** (segures per a daltonisme). Classificació
  acordada amb Talaia: **cuantils** per a índexs normalitzats (IETR), **Jenks** per a magnituds crues,
  **5 classes per defecte**; la llegenda diu sempre mètode + nº de classes + font·data. Detall a
  `cartography/palette.md`.
- **Marca:** nom públic tancat = **`riusdegent`** (*rius de gent* — el cabal humà que omple o buida el
  territori). Identitat de sortida a `brand/` (logo SVG clar/fosc/mono, marca, favicon SVG+ICO, guia d'1
  pàgina); **aplica** els tokens sense redefinir-los. El **dibuix** del traç és proposta a refinar per un
  humà; el vot final de marca és de Bea.

## Estat i abast

- **Validat:** estructura del contracte, àlies semàntics, cobertura tipogràfica; SVG de marca
  *well-formed*; favicon `.ico` (16/32/48) rasteritzat des del SVG.
- **Acordat amb Talaia:** mètode de classificació coroplètica (cuantils/Jenks, 5 classes). Veure
  `cartography/palette.md` §5.
- **Proposta (no validat encara):** seguretat CVD pas-a-pas de la rampa seqüencial (proposta basada en
  principis i famílies de referència, no verificada amb simulador); el **dibuix** fi del traç de marca i
  el tractament del hero (vot de Bea); l'estil MapLibre real. Veure "Pendent" a `cartography/palette.md`
  i la guia de marca.
- **F2:** estil MapLibre custom + sistema de dataviz (Observable Plot) + Storybook. **Renombrar
  `--dp-teal*` → `--dp-support-*`** en regenerar amb Style Dictionary (el valor ja és forest; vegeu
  `tokens.json` `$meta.renaming`).
- **F3:** editorial/scrollytelling + a11y/perf full + i18n visual.

Tokens escrits a mà a F1 per desbloquejar Mirador sense build; a F2 es regeneren amb **Style
Dictionary** des de `tokens.json` (mateixa nomenclatura `--dp-*`, el contracte no canvia).

### Com es regenera el favicon `.ico`

Raster 16/32/48 des de `brand/favicon.svg` (Chromium headless via Playwright + Pillow). Reproducible —
re-executar-ho dona el mateix ICO. Si canvia el SVG, regenerar amb el mateix procediment.
