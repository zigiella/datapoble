# Aparcaments A1–A10 — el model surt de la vista del web (Mirador, 2026-07-17)

**Mandat:** `docs/ajuntaments/fase-nova-aparcaments.md` §A (context §D/§F) + decisió de fons a
`docs/ajuntaments/gorra-alcalde-pobla.md` §1. Vot de Bea (2026-07-16): «sentit comú — el que s'ha
d'aparcar, s'ha d'aparcar». Criteri aplicat: **aparcar = retirar netament de la vista, no
destrossar** — el codi mort s'elimina (git és la memòria), els candaus dorments es conserven, la
metodologia s'etiqueta però no s'esborra.

## Peça a peça

| # | Fet |
|---|---|
| A1 | Beeswarm/waveform del gap FORA de la home i de `/comarca/[slug]` (secció + component eliminats). També fora: els xips de gap per municipi a la llista de la comarca (mateix model). |
| A2 | Fitxa: fora la banda de pernocta, els TRES REGISTRES i la veu del gap (tot el bloc `pernoctaBand`). El loader ja NOMÉS llegeix `etca_oficial` de `pernocta-catalunya.json`. |
| A3 | Avís de col·lisió fora (cau amb la banda: sense banda no té subjecte). **`distinguish.ts` ES CONSERVA dorment** com a candau per a rànquings futurs (C6 §3). |
| A4 | Bloc E «les 3 capes» fora de la fitxa. El card «qui hi dorm» dels números → **«Presència oficial (ETCA)»**: la dada d'Idescat on n'hi ha, «sense dada oficial» als <1.000. El card «càrrega per residus» (també model) surt amb el bloc: queden 4 números oficials (padró · ETCA · % no principal · renda). La secció «Lectura per a serveis» també fora (els seus denominadors eren les estimacions del model). |
| A5 | Bloc de confiança del model (bandera + score + divergència + «sense validació») fora de la fitxa. Les dades oficials porten font i data, no bandera. |
| A6 | `/mapa`: defecte → `pct_noprincipal`; `gap_pernocta_pct` fora del selector. Decisió §F.3 aplicada: **el /mapa es MANTÉ, podat (aparador oficial)** — selector amb 2 indicadors oficials (% no principal, residus). De rebot: fora la vista de cobertura comarca/vegueria (només mostrava la cobertura del Nivell C) i el velat per «confiança baixa» del model sobre dades oficials. |
| A7 | Tooltip del mapa podat: fora la banda de pernocta, la costura Idescat↔nostra i la confiança del model. Queda: nom + valor oficial + procedència + CTA fitxa. La home ja no carrega `pernocta-catalunya.json`. |
| A8 | Glossari: HIDDEN ampliat amb la família del model (`gap_pernocta*`, `poblacio_pernocta_est`, `carrega_*`, `index_turisme`, `*_base_ratio`, `confianca`, `tipologia`). La secció «Com llegim la incertesa» (doctrina σ del model) també fora — descrivia UI que ja no existeix. El recompte de capçalera ara compta només els indicadors publicats (21), no els 50 del contracte. |
| A9 | `/metodologia`: les seccions del model NO s'esborren — s'etiqueten **«Model aparcat · annex de recerca»** amb nota curta: bloc C (3 rastres), G (límits del model), H (validació ETCA), I (rang Catalunya). Les fitxes metodològiques dels indicadors oficials (A/B/D/E), intactes. |
| A10 | Stubs morts `/index` (IETR) i `/day-tripper` eliminats, amb `StubScreen` i el `Nav.svelte` mort que hi enllaçava. |

## Codi mort eliminat (git és la memòria)

`Beeswarm.svelte`, `StockImpactScatter.svelte`, `MapLegend.svelte`, `MapIndicatorPicker.svelte`,
`Nav.svelte`, `StubScreen.svelte`, `analysis/troballes.ts`, `analysis/mirall.ts` (tots o bé
model-família o bé orfes que hi enllaçaven). **Conservats a consciència:** `distinguish.ts`
(candau dorment), `MetodologiaModel.svelte` (el fa servir l'annex G), `MirallConstel` + artefacte
mirall (B2, es regenera fora d'aquest lot), lectures-IA P1/P2 (B1), xips de /pregunta-li (B3,
cua de Brúixola), `KpiCard`/`MunicipiCard`/`MetricRow` (orfes però genèrics: candidats per a D5).

## Dades

- `validats.json` ja no es genera (només servia per capar la confiança del model).
- `pernocta-catalunya.json` se segueix servint amb UNA frontera: la fitxa en llegeix només
  `etca_oficial` (documentat a `copy-data.mjs`). Cap fitxer font esborrat del repo.
- i18n: −161 claus òrfenes (ca+es), +7 de noves, 11 de reescrites.

## Verificació (llistó)

`npm run check` → **0 errors, 0 warnings** · build **verd** (947 fitxes ×2 locales) · DOM del
build servit en local, transcrit:

- la Pobla de Lillet: «Presència oficial (ETCA) **1.121** hab.» · cap banda (726/1.037 absents),
  cap 852, cap col·lisió, cap bloc de confiança.
- Gósol i Castellar de n'Hug: «Presència oficial (ETCA) → **sense dada oficial**» ([es]: «sin
  dato oficial») · cap banda.
- Home: sense Beeswarm, mapa oficial viu. /comarca/bergueda: 31 xips sense gap.
- /glossari: 21 termes, cap família del model, cap doctrina σ.
- /metodologia: 4 seccions etiquetades «Model aparcat · annex de recerca», oficials intactes.
- /mapa: selector = [% habitatge no principal, residus]; cap paraula del model.
- Cap error de consola a cap de les pàgines visitades.

## Copy nou — vot narratiu de Bea PENDENT

Claus noves: `muni_nums_title` («Els números clau»), `muni_num_etca` («Presència oficial
(ETCA)»), `muni_sense_dada_oficial` («sense dada oficial»), `muni_etca_srcline`, `map_lede`,
`met_annex_badge`, `met_annex_note`. Reescrites sòbries: `home_map_scope`,
`home_porta_proxim_sub`, `muni_lede`, `muni_lede_cat`, `muni_meta_desc`, `muni_honesty`,
`map_legend_estimat`, `map_outside_scope`, `comarca_sub`, `comarca_meta`, `glo_intro_note`
(ca+es). Cap titular inventat.

## Dubtes deixats per escrit (Talaia arbitra)

1. **Pastilla de tipologia al cercador de la home** (MuniSearch): la tipologia és inferència del
   model però el doc §A no la llista → CONSERVADA. Si també s'aparca, és un retoc petit.
2. **Notes del contracte semàntic** de `kwh_hab`, `vidre_hab`, `restauracio_per_1000hab` al
   glossari encara diuen «senyal de la capa L1/L3» — text del contracte (`semantic/metrics.yml`),
   no del web. **Handoff a: Sondeig** (esmena de contracte) si es vol netejar.
3. **`narrativa_mare`** al hero de /metodologia («El padró diu qui consta. Els rastres diuen qui
   hi és…») — narrativa votada de Bea; l'he deixada (la pàgina conserva el model com a annex).
4. Lectures-IA (P1/P2) i preguntes suggerides encara citen el model a les fitxes del Berguedà —
   és **B1** (regenerar amb `gen_fitxa.py` sobre oficials), explícitament fora d'aquest lot.

— Mirador
