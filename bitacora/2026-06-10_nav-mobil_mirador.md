# Navegació mòbil: hamburger + drawer a la capçalera

**Fecha:** 2026-06-10
**Autora:** Mirador (frontend)
**Para:** Talaia (review/merge) · Bea
**Tema:** primera peça de l'**sprint de mòbil** (backlog 2026-06-10): la capçalera no estava pensada per a mòbil.
**Status:** fet, verificat (build + preview mòbil i escriptori) / handoff

## Contexto
La `.ds-nav` de `+layout.svelte` feia `flex-wrap` → a mòbil els 6 ítems + selectors s'amuntegaven. Calia un patró mòbil de debò.

## Què he fet (`+layout.svelte`, una sola jurisdicció)
- **Hamburger + drawer** a la capçalera, tot dins `+layout.svelte` (marcatge + estat `menuOpen` + CSS **scoped** a la component; no toco el design-system).
- A **≤760px** (breakpoint ja usat a la chrome): s'amaga la `.ds-nav` d'escriptori i els selectors; apareix el **burger** (dreta). El **drawer** cau sota el header (absolut, amplada completa) amb les **pàgines navegables**: Resum · Mapa · Pregunta-li · Metodologia · Glossari + selectors idioma/tema. Es tanca amb **Escape** o en triar una destinació.
- **Decisió #7 (parcial):** el drawer **omet els ítems inerts** (Índex IETR · Excursionista de dia · Política) → mòbil net sense stubs. La nava d'**escriptori NO es toca** (el rethink de seccions a escriptori és vot de la Bea, pendent).
- A escriptori (>760px): tot igual que abans; el burger queda ocult.
- i18n nou: `nav_menu` («Menú», ca/es).

## Verificación (preview)
- **375px (mòbil):** burger `flex`, `.ds-nav`/selectors `none`; drawer obre amb 5 enllaços + CA/ES, cau just sota el header (top 63 ≈ header 64), amplada completa.
- **1280px (escriptori):** burger `none`, `.ds-nav` + selectors `flex` (sense regressió).
- `npm run check` → **1103 fitxers, 0/0**. `npm run build` → OK.

## Pendiente
- [ ] **Talaia:** review/merge.
- [ ] **Bea (vot #7):** rethink de seccions a ESCRIPTORI (treure «Índex IETR»/«Excursionista de dia»? → menú-espina: Resum · Mapa · Metodologia · Pregunta-li + futur Licitacions · Transformació demogràfica).
- [ ] (sprint mòbil) #2: tap→targeta al mapa/atles/constel·lació (el hover no existeix a mòbil).

## Enlaces
- `packages/web/src/routes/+layout.svelte` · `messages/{ca,es}.json` (`nav_menu`)
- backlog: `bitacora/2026-06-10_backlog-preguntes-bea_talaia.md`

— Mirador
