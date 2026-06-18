# Pla de llançament — sortida online amb un producte bo

*Talaia, 2026-06-18 (v2, decisions de Bea resoltes). Encàrrec: «sortida online amb un producte bo ·
tota Catalunya · web sòlida · licitacions com a pàgina en construcció». Aquest pla TANCA la línia de
llançament. El **vot narratiu és de la Bea**; el §0 recull les decisions que ha pres.*

> **Nota de mètode:** l'auditoria s'havia de fer amb un workflow de 7 agents; va fallar tot (límit de
> despesa mensual del compte). L'he fet inline sobre el repo real, amb cada troballa ancorada en
> fitxers. El que NO he pogut verificar ho marco com a tal.

## Principi rector
Per a «un producte bo», **la solidesa i l'honestedat pesen més que cap feature**. «Tota Catalunya» no
és tenir-ho tot el dia 1; és que la web sigui **digna a tota escala**: que qualsevol veí trobi el seu
poble amb dada (rang) o amb un «sense dades encara» ben explicat, sense puntes trencades.

**Decisió d'abast (Bea):** *tot l'spec al llançament* + *cobertura de dades a tot Catalunya (tots els
munis)* + *4 llengües*. És un llançament RIC i, per tant, GRAN: aquest pla el fa visible i el seqüencia.
**`P0` = bloqueja el llançament; `P1` = al llançament però no bloqueja el dia exacte.**

---

## §0 · Decisions de la Bea (2026-06-18) — RESOLTES

1. **Abast:** *tot l'spec al llançament* (dades obertes §9, visualitzacions noves §4, espina §7,
   pregunta-li super beta… entren al dia 1, no es retallen).
2. **Cobertura de dades:** *tot Catalunya, tots els munis* — estendre Nivell C a les 43 comarques i
   baixar el llindar dels 1.000 hab (Palanca 1 + 2, §1).
3. **Fitxes:** *prerenderitzar TOTS els munis* (conseqüència de 2: la majoria portaran rang; la resta,
   buit honest).
4. **Licitacions:** *al PEU, com a «en construcció»* (fora de la nav principal; §3).
5. **Llengües:** *ca/es + aranès + anglès al dia 1* (§6).

---

## Estat real (snapshot 2026-06-18)

| Capa | Estat | Evidència |
|---|---|---|
| Dades Berguedà (31) | ✅ completes | `data/web/municipis.bergueda.json` + lectures-IA |
| Presència en RANG | 🟡 82 munis, 5 comarques | Nivell C; cal estendre a 43 comarques + <1.000 hab |
| Cercador | 🔴 només 31 munis | `MuniSearch.svelte` cerca `dataset.municipis` |
| Prerender fitxes | 🟡 113 de ~947 | `municipi/[slug]/+page.ts` `entries()`; resta = fallback SPA (404) |
| Licitacions | 🟢 viu (cal aparcar al peu) | `/licitacions`, troballa home, secció fitxa, nav+peu |
| Stubs | 🟡 inerts | `/index`,`/day-tripper`,`/politica` (`StubScreen`) |
| SEO/indexació | 🔴 noindex a 3 llocs | `app.html:15`, `static/robots.txt`, `static/_headers` |
| og:image | 🔴 no n'hi ha | `+layout.svelte` (og:* sense imatge) |
| i18n | 🟡 ca/es ok; oc/en no | hreflang+canonical+LangSwitcher; falten aranès/anglès |
| Spec ric (dades obertes, viz, espina) | ⬜ pendent | §13.6-9 de la revisió estratègica |
| Analytics | ✅ sense cookies | Simple Analytics |
| Deploy/CI | 🟢 verd | `.github/workflows/{ci,deploy-web}.yml` |

---

## §1 · Cobertura de dades «tota Catalunya» (P0) — Sondeig
*Carril dades. Pur Python + dades obertes (numpy + Socrata/INE), ZERO IA → **NO bloquejat pel límit
de despesa**.*

Per què avui falten ~834: el model Nivell C només s'ha corregut sobre **5 comarques**
(`nivellc_analisi.py:47`) i només per a munis amb **ETCA** (≥1.000 hab). Les fonts són de tot
Catalunya; només cal ampliar l'abast.

- **Palanca 1 — 43 comarques.** Ampliar `COMARQUES`, re-fetch (`fetch_electric`/`fetch_gas`/…),
  re-córrer `nivellc_analisi.py` → `nivellc_regressio.py` → `export_pernocta_catalunya.py`.
- **Palanca 2 — sota 1.000 hab.** L'estimació és `est = consum / base_pred` (l'ETCA s'anul·la, només
  valida; verificat a `export_pernocta_catalunya.py:91`). Cal calcular `est` directe del consum per
  als munis sense ETCA, marcats **«sense validació oficial»** i amb **banda més ampla**.
- **Honestedat (innegociable):** cada comarca/tipus nou es **re-valida held-out abans de publicar**;
  el sostre de l'estacionalitat del litoral fa que alguns munis de costa quedin amb banda ampla o
  **sense publicar** (mai una xifra que no aguanti). Documentar a `docs/analisi-escala-nivellc.md`.

**Criteri de sortida:** `pernocta-catalunya.json` cobreix la gran majoria de munis de Catalunya en
rang, cada tipus validat o marcat; cap rang publicat sense aguantar la validació.

## §2 · Solidesa de la web (P0/P1) — Mirador
1. **Cercador tota Catalunya (P0).** `MuniSearch` indexa els ~947 munis (geojson `{ine5,nom}`), no
   els 31. Cada resultat → `/municipi/[slug]`.
2. **Prerender de tots els munis (P0).** Ampliar `entries()` a tot el geojson; rang on n'hi ha,
   «sense dades encara» digne a la resta. URL real per a cada poble (SEO + enllaços).
3. **Stubs fora (P1).** Treure `/index`,`/day-tripper`,`/politica` del build (o resoldre'ls dins
   l'spec ric); cap segell «stub» visible.
4. **Estats buits/errors + mòbil + rendiment (P1).** Dataset buit/muni desconegut/sense JS dignes;
   pes del geojson de 947 munis a home i `/mapa`.

## §3 · Licitacions → «en construcció» al peu (P0) — Mirador
Zero càlculs a la vista, zero enllaços morts. Maquinària conservada per a Fase 2.
- `/licitacions/{+page.svelte,+page.ts}` → pàgina **«en construcció»** digna (no el segell «stub»).
- **Treure de la nav principal** (`+layout.svelte:93,126`); **mantenir al PEU** (`:162`) cap a la
  pàgina en construcció.
- Home: `+page.ts` deixa de carregar l'artefacte → la troballa `'lic'` desapareix sola
  (`troballes.ts:92`, ja condicionada).
- Fitxa: `municipi/[slug]/+page.ts` deixa de carregar; `+page.svelte` amaga la secció.
- `sitemap.xml/+server.ts`: apuntar la pàgina en construcció (o excloure-la).

## §4 · Honestedat «tota Catalunya» (P0) — Talaia + Llegenda
- **Missatge d'abast** a home i mapa: què cobrim (rang vs context) i per què; que «sense dades» es
  llegeixi com a honestedat, no com a producte incomplet.
- **Coherència del rang:** repàs global que enlloc una estimació sembli cens (mapa/tooltip/fitxa/
  `/metodologia`).

## §5 · Spec ric al llançament (P1) — Mirador + Llegenda + Brúixola
Per decisió de Bea, entren al dia 1 (seqüenciar després dels P0):
- **Dades obertes de veritat (§9):** `/dades`, descàrrega CSV/JSON/Parquet/SQLite, **xifra citable**
  (cada número una URL), embeds, kit de premsa.
- **Visualitzacions noves (§4):** Dorling-fantasma, slider de denominador, «el riu», beeswarm,
  emblema doble corrent, glif balança.
- **Espina territorial + breadcrumb (§7).**
- **Pregunta-li «super beta»** (genUI / resposta-com-UI). *⚠️ depèn d'IA → límit de despesa.*
- **3 profunditats a cada pàgina + test CI** (§1) que falli amb jerga «above the fold».

## §6 · Llengües: ca/es/oc/en (P1) — Brúixola + Talaia
- **Aranès** (Apertium cat→oci + AINA) i **anglès**; terreny /ca ja obert (hreflang preparat).
- Repàs de **còpia ca/es** (font) abans de traduir.
- *⚠️ La traducció usa IA → subjecta al límit de despesa; planificar quan es reposi.*

## §7 · Accessibilitat (P1) — Llegenda + Mirador
Teclat al mapa (alternativa en taula ja hi és), contrast, `aria`, **`axe-core` a CI** (`ci.yml`).

## §8 · Ops de llançament (P0) — Talaia + Mirador
- **Treure noindex als 3 llocs:** `app.html:15`, `static/robots.txt` (→ `Allow: /` + `Sitemap:`),
  `static/_headers` (treure `X-Robots-Tag`).
- **og:image** (crear + afegir a `+layout.svelte`).
- **Sitemap complet** (totes les pàgines + tots els munis) · **deploy verd** a Cloudflare Pages,
  domini `riusdegent.cat` · comprovació final (links, 404, mòbil, fosc/clar, 4 llengües).

---

## Go / No-Go de llançament (tot verd)
- [ ] Cobertura de dades a tot Catalunya, cada tipus validat o marcat; cap rang sense aguantar.
- [ ] Cercador troba qualsevol municipi; totes les fitxes prerenderitzades.
- [ ] Licitacions al peu «en construcció»; cap enllaç mort ni xifra penjada.
- [ ] Missatge d'abast honest; cap xifra llegible com a cens.
- [ ] Spec ric servit (dades obertes, viz, espina, 3 profunditats).
- [ ] 4 llengües (ca/es/oc/en); còpia revisada.
- [ ] noindex tret ×3; og:image; sitemap+robots de producció; deploy verd al domini; a11y mínima.

## Riscos
- **Límit de despesa del compte** (viu): bloqueja tot el que depèn d'IA — lectures (gen-fitxa),
  pregunta-li super beta, **traducció oc/en**. NO bloqueja el carril de dades (§1) ni la web (§2,3).
  Cal reposar-lo per als P1 dependents d'IA abans del dia D.
- **Abast gran:** «tot l'spec + tot CAT + 4 llengües» és un llançament gran → més llarg. P0 primer.
- **Estacionalitat del litoral:** sostre del model; alguns munis de costa, banda ampla o sense.
- **Rendiment** del geojson de 947 munis a mòbil.

## Fora de llançament (Fase 2)
Licitacions de veritat (menors → majors/diputació) · fondària completa de fitxa (tipologia +
lectures-IA) per a tot Catalunya, no només Berguedà · fonts noves §12 (INE-mòbils, VUT, autocaravanes).

---
*Pla viu. La cua operativa (P0 primer) viu a `bitacora/next.md`. Filtre de l'spec: «si una peça no
pot explicar d'on surt, no es publica».*
