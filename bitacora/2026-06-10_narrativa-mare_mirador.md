# Narrativa mare: la tesi de capçalera a /resum i /metodologia

**Fecha:** 2026-06-10
**Autora:** Mirador (frontend)
**Para:** Talaia (review/merge) · Bea (vot del wording)
**Tema:** ② del repàs — donar a la web la **tesi mare** que explica de què va el projecte.
**Status:** fet, verificat (build + preview) / handoff

## Contexto
El repàs del pla marcava la **narrativa mare** com a pendent (vot de la Bea). La Bea va fixar el wording:
> «El padró diu qui consta; els rastres, qui hi és de debò i quin és l'ús. Riusdegent fa visible aquesta distància.»

## Què he fet
- Clau i18n nova `narrativa_mare` (ca + es; el mirall castellà: «El padrón dice quién consta; los rastros, quién está de verdad y cuál es el uso. Riusdegent hace visible esa distancia.»).
- Renderitzada com a **tesi de capçalera** sota el lede a `/resum` i `/metodologia`, amb accent **ocre de marca** (`--dp-brand`, vora esquerra 3px, 18px). No es posa a cada fitxa (per no saturar).

## Verificación
- `npm run check` → **1101 fitxers, 0 errors, 0 warnings**. `npm run build` → OK.
- **Preview en viu**: `/resum` i `/metodologia` mostren la tesi (text exacte) amb la vora ocre `rgb(181,97,42)`.

## Pendiente
- [ ] **Talaia:** review/merge.
- [ ] (② resta) **atles de contradiccions** → secció pròpia al `/resum` (decidit per la Bea); bloc «Interpretació».

## Enlaces
- `packages/web/messages/{ca,es}.json` (`narrativa_mare`) · `routes/resum/+page.svelte` · `routes/metodologia/+page.svelte`

— Mirador
