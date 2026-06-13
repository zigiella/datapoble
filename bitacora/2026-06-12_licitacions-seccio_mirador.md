# Secció Licitacions al web (resum comarcal)

**Fecha:** 2026-06-12
**Autora:** Mirador (frontend)
**Para:** Talaia (review/merge) · Bea
**Tema:** segona peça de «Licitacions al web» (decisió Bea: secció + fitxa). Aquí, la **secció comarcal** `/licitacions`. El bloc de fitxa va al PR següent.
**Status:** fet, verificat (check + build + HTML prerenderitzat ca/es) / handoff

## Què he fet
- **Ruta nova `/licitacions`** (`+page.ts` carrega l'artefacte `licitacions-bergueda.json`; `+page.svelte` amb la pell del design-system: hero + ds-main).
  - **Veredicte (P1):** xifra gran «29 / 31» + lectura + **caveat enganxat** (centralització + biaix de font, NO mala gestió).
  - **Tesi:** «Una licitació és una confessió administrativa.»
  - **Taxonomia** (bloc A): 1.295 contractes (695 comarcals + 600 municipals, 42,4 M€) en barres per tema (mobilitat 195, administració 194, educació 193…).
  - **Dependència** (bloc B): taula per municipi (contractes propis · import propi · serveis del Consell · lectura). Berga i Castellar = autònoms; 29 = no contracta propi.
  - **Fronteres honestes** (bloc ★): taxonomia heurística + repartiment com a hipòtesi declarada.
- **Tipus `$lib/contract/licitacions.ts`**.
- **Nav**: «Licitacions» a la capçalera (desktop + drawer mòbil) i al peu (Explora). Espina del producte: Resum · Mapa · **Licitacions** · Pregunta-li.
- **i18n** ca/es: copy de la pàgina + 16 etiquetes de tema + 4 de lectura de dependència + `nav_licitacions`.

## Verificació
- `npm run check` → **0/0**; `npm run build` → OK (copy-data: `licitacions-bergueda.json → static (19 kB)`; pàgina prerenderitzada).
- HTML prerenderitzat `/licitacions` i `/es/licitacions`: veredicte, tesi, taxonomia (temes amb barres), taula (2 autònom · 29 no contracta propi), nav amb Licitacions. ES OK.

## Pendiente
- [ ] **Talaia:** review/merge.
- [ ] **PR següent (fitxa):** bloc de licitacions a la fitxa de municipi (la seva dependència + què rep del Consell, dels `temes_rebuts` de l'artefacte).
- [ ] Quan hi hagi la fitxa, treure l'stub inert «Política» del nav si escau (vot #7 pendent de la Bea).

## Enlaces
- `packages/web/src/routes/licitacions/{+page.ts,+page.svelte}` · `$lib/contract/licitacions.ts` · `+layout.svelte` · `messages/{ca,es}.json`
- dada: `bitacora/2026-06-12_licitacions-export_cabal.md` (#104) · `data/web/licitacions-bergueda.json`

— Mirador
