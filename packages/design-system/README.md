# design-system — Llegenda

Sistema visual de **datapoble** (observatori territorial). Font de veritat del que el públic veu:
marca, design tokens, cartografia, dataviz, capa editorial i a11y. S'entrega com a **contractes**
(tokens, estils, specs) que el frontend **Mirador** consumeix; no implementem el frontend aquí.

Brief complet: `docs/art-direction.md` · Spec d'aquest encàrrec: `bitacora/2026-06-02_spec-identitat-tokens_talaia-a-llegenda.md`

## Què hi ha (F1 — primer encàrrec)

```
packages/design-system/
├─ brand/
│  └─ identity-routes.md     # 3 rutes d'identitat perquè Bea n'esculli una (proposta)
├─ tokens/
│  ├─ tokens.json            # contracte visual (W3C DTCG / Style Dictionary): color, tipografia,
│  │                         #   espaiat, radis, ombres, breakpoints, moviment + paletes de dada
│  └─ tokens.css             # variables CSS (--dp-*), espill del JSON, tema clar/fosc, reduced-motion
└─ cartography/
   └─ palette.md             # spec paleta coroplètica + recomanació classificació (cuantils vs Jenks)
```

## Com ho consumeix Mirador

1. Importar `tokens/tokens.css` a l'arrel de l'app → totes les variables `--dp-*` disponibles.
2. Usar els **àlies semàntics** (`--dp-bg`, `--dp-text`, `--dp-border`, `--dp-link`…) als components,
   no els primitius directament, perquè el tema (clar/fosc) funcioni sol.
3. Mapes/charts: paletes de dada a `--dp-exposure-*` (seqüencial), `--dp-div-*` (diverging),
   `--dp-cat-*` (qualitativa). Mètode de classificació segons `cartography/palette.md`.
4. Superfícies amb número: classe `.dp-tnum` o `font-variant-numeric: tabular-nums` (cifres tabulars).

## Decisions clau

- **Tipografia:** Inter (UI/dada, cifres tabulars) + IBM Plex Serif (lectura llarga) + IBM Plex Mono.
  Totes amb diacrítiques catalanes completes (à è é í ï ò ó ú ü ç l·l) i `tnum`.
- **Paleta de dada:** seqüencial terra "exposició" (6 passos) i diverging teal↔marró, **sense
  vermell-verd** (segures per a daltonisme). Detall i hex a `cartography/palette.md`.
- **Marca:** el nom públic encara **no està decidit** — `brand/identity-routes.md` proposa 3 rutes;
  els tokens són **neutres respecte al nom**, així que la decisió de marca no bloqueja Mirador.

## Estat i abast

- **Validat:** estructura del contracte, àlies semàntics, cobertura tipogràfica.
- **Proposta (no validat encara):** seguretat CVD pas-a-pas de la rampa seqüencial, i el mètode de
  classificació definitiu (s'acorda amb Talaia). Veure "Pendent" a `cartography/palette.md`.
- **F2:** estil MapLibre custom + sistema de dataviz (Observable Plot) + Storybook.
- **F3:** editorial/scrollytelling + a11y/perf full + i18n visual.

Tokens escrits a mà a F1 per desbloquejar Mirador sense build; a F2 es regeneren amb **Style
Dictionary** des de `tokens.json` (mateixa nomenclatura `--dp-*`, el contracte no canvia).
