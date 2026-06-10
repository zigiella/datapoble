# Constel·lació del Resum: tooltip de debò + textos planers (mantenint stock/impact)

**Fecha:** 2026-06-10
**Autora:** Mirador (frontend)
**Para:** Talaia (review/merge) · Bea (vot de copy aplicat)
**Tema:** la «Constel·lació stock × empremta» del Resum (a) prometia mouseover però no en tenia de debò, i (b) era poc llegible per a un usuari que entra fred (argot `stock`/`impact`).
**Status:** fet, verificat (build) / handoff

## Contexto
Feedback de la Bea sobre `/resum`: el gràfic stock×impact no tenia mouseover (la llegenda fins i tot el prometia: «Passa-hi el ratolí…») i els usuaris no entendrien «stock/impact». **Vot de la Bea:** conservar els termes `stock`/`impact` (vocabulari del projecte) però **acompanyar-los amb text planer**.

## Causa del «no mouseover»
Els punts usaven un `<title>` SVG natiu: tooltip del navegador lent (~1 s), pla i poc fiable → sensació d'absència. Promesa trencada a la llegenda.

## Què he fet (Mirador: 1 component + 6 textos ca/es)
- **Tooltip HTML real** a `StockImpactScatter.svelte` (substitueix el `<title>`): apareix a l'instant amb ratolí i dit (tàctil), via `onpointerenter/move/leave` + un `<div>` posicionat relatiu a la `<figure>`. Mostra nom + `què té preparat (stock): X/100` + `què ja es nota (impact): Y/100` + la **lectura del quadrant**.
- **Glosses planeres als 4 quadrants** (nom tècnic + frase planera): «Pressió consolidada» → *preparat i ja es nota*; «Capacitat latent» → *preparat, encara no es nota*; «Empremta sense stock clàssic» → *es nota sense estructura típica*; «Baixa exposició» → *tranquil pels dos costats*.
- **Eixos** reescrits mantenint el terme: `què té preparat (stock)` / `què ja es nota (impact)`.
- **Lede** reescrit: «Cada punt és un poble. Com més a la dreta, més té preparat…; com més amunt, més ja es nota…». **Llegenda**: «…(o toca) per veure els valors».

## Verificación
- `npm run check` (svelte-check) → **1100 fitxers, 0 errors, 0 warnings**.
- `npm run build` (adapter-static) → **OK**; paraglide compila les 6 claus noves/editades.
- **No provat en navegador en viu** des d'aquí: el tooltip és el patró HTML estàndard. Pendent d'ull a `npm run preview`/desplegament.

## a11y
Tooltip per a ratolí/tàctil; el lector de pantalla té el **resum del gràfic** via l'`aria-label` del SVG (igual que abans). Sense focus per punt: fer-lo accessible per teclat amb `role`/`tabindex` correctes (sense disparar `a11y_no_noninteractive_tabindex`) queda com a millora futura.

## Pendiente
- [ ] **Talaia:** review/merge.
- [ ] (millora) accés per teclat punt a punt a la constel·lació.
- [ ] (triatge) frase-lectura **IETR-família a la fitxa** del municipi — item separat, encara pendent.

## Enlaces
- `packages/web/src/lib/components/StockImpactScatter.svelte`
- `packages/web/messages/ca.json` · `es.json` (claus `constel_*`, `resum_constel_*`)

— Mirador
