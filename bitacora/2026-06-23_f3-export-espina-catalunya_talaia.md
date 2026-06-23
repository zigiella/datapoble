# F3 · Exportar l'espina a tot Catalunya (municipis.catalunya.json)

**Data:** 2026-06-23
**Autora:** Talaia (encarna Sondeig/Mirador)
**Latido (Bea):** «ataquem la F3!».
**Pla:** [docs/pla-catalunya-profund.md](../docs/pla-catalunya-profund.md) §F3.

## Què he fet
L'export del dataset profund, ara a escala Catalunya. `tools/export_web_municipis.py` guanya
`--scope {bergueda,catalunya}`:
- **`catalunya`** → `data/web/municipis.catalunya.json` (**947 munis**, 1,78 MB, mateixa forma
  `MunicipisDataset`). Cada muni porta l'**espina** (presència/gap, residus, kwh, vidre, IETR,
  index_turisme, %no-principal, confiança/divergència, tipus); els **extres** (tipologia, restauració/
  serveis OSM, política, origen) només al Berguedà, `pendent`/NULL honest a la resta. El resum
  `comarca` es relabela «Catalunya» (agregats CAT).
- **`bergueda`** (per defecte) → `municipis.bergueda.json` regenerat amb els **valors nous de F2**
  (presència per base_pred, confiança per tipus): cenyit per `comarca=='Berguedà'` del mart (31).

`copy-data.mjs` ara serveix també `municipis.catalunya.json`.

## Verificat
- `export --check` OK per als dos abasts (reproduïble).
- Mostra no-Berguedà (Girona): espina present (gap −2,9%, residus 427, IETR 11,1, confiança 66,3),
  extres `pendent`/NULL. 947 munis · scope «Catalunya».
- **`npm run build` ✔** amb les dades noves (bergueda regenerat + catalunya copiat).

## Decisió d'arquitectura (per a F4)
- Els loaders corren a **build** (prerender). La **fitxa** (per muni) pot consumir `catalunya.json`
  (build-time → incrusta NOMÉS un muni → client lleuger).
- El **mapa** (home + /mapa) incrusta el dataset client-side: amb 947 (~1,8 MB) seria pesat → seguirà
  amb artefactes **compactes** (pernocta + indicadors-catalunya, a estendre amb l'espina del tooltip).

## Següent (F4 · harmonitzar el web)
- Fitxa: llegir `catalunya.json` per a QUALSEVOL muni (espina arreu; extres on n'hi ha; `pendent`
  digne fora del Berguedà). Resol el «fitxes diferents».
- Mapa: estendre `indicadors-catalunya.json` amb l'espina del tooltip + **trames a tot CAT** (segons
  confiança). Un sol tooltip.
- Després: deprecar `municipis.bergueda.json` quan el web ja no el necessiti (o mantenir-lo per al
  /resum del Berguedà).

— Talaia 🌊
