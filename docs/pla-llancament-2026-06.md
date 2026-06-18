# Pla de llançament — sortida online amb un producte bo

*Talaia, 2026-06-18. Encàrrec de Bea: «sortida online amb un producte bo · tota Catalunya · web
sòlida · probablement licitacions com a pàgina en construcció». Aquest pla TANCA la línia de
llançament: tria què surt al dia 1 i què queda per després. Reconcilia (i en alguns punts retalla)
la llista «al llançament» de `revisio-estrategia-consultora2-2026-06.md`. El **vot narratiu final és
de la Bea** (§0 són les decisions que només pot prendre ella).*

> **Nota de mètode:** aquesta auditoria s'havia de fer amb un workflow de 7 agents; va fallar tot
> (límit de despesa mensual del compte). L'he fet jo, inline, sobre el repo real. Cada afirmació
> està ancorada en fitxers. El que NO he pogut verificar ho marco com a tal.

## Principi rector
Per a «un producte bo» amb aquestes restriccions, **la solidesa i l'honestedat pesen més que les
features**. «Tota Catalunya» NO vol dir tenir dades de 947 municipis el dia 1 —no les tindrem—; vol
dir que la web sigui **digna a escala Catalunya**: que qualsevol veí trobi el seu poble, amb un
«sense dades encara» ben explicat, sense puntes trencades. Aquesta és la barra.

**Re-tall proposat (per validar amb Bea):** la revisió estratègica posava «al llançament» moltes
peces grans (dades obertes §9, visualitzacions noves §4, espina territorial §7). Per sortir SÒLIDS i
aviat, **proposo moure-les a post-llançament** i que el dia 1 sigui: web sòlida + tota Catalunya
honesta + licitacions aparcades. Menys superfície, més ferma.

---

## Estat real (snapshot 2026-06-18)

| Capa | Estat | Evidència |
|---|---|---|
| Dades Berguedà (31) | ✅ completes | `data/web/municipis.bergueda.json`, fitxes amb lectures-IA |
| Presència en RANG (82 munis nous) | ✅ publicada | Nivell C; fitxa + `/metodologia` + mapa (capa COVERED) |
| Resta de Catalunya (~834) | 🟡 geometria sí, dades no | mapa «sense dades»; fitxa degrada a «sense dades encara» |
| Cercador | 🔴 només 31 munis | `MuniSearch.svelte` cerca `dataset.municipis` (Berguedà) |
| Prerender de fitxes | 🟡 113 de ~947 | `municipi/[slug]/+page.ts` `entries()`; la resta = fallback SPA (404) |
| Licitacions | 🟢 viu (cal aparcar) | `/licitacions`, troballa a la home, secció a la fitxa |
| Stubs | 🟡 inerts | `/index`, `/day-tripper`, `/politica` (`StubScreen`, segell «stub») |
| SEO/indexació | 🔴 noindex a 3 llocs | `app.html`, `static/robots.txt`, `static/_headers` |
| og:image | 🔴 no n'hi ha | `+layout.svelte` té og:* menys imatge |
| i18n ca/es | ✅ | hreflang + canonical + LangSwitcher |
| Analytics | ✅ sense cookies | Simple Analytics a `app.html` |
| Deploy/CI | 🟢 a verificar | `.github/workflows/{ci,deploy-web}.yml` |

---

## §0 · Decisions de la Bea (desbloquegen el pla)

1. **Abast del re-tall.** Confirmes sortir LEAN (web sòlida + tota Catalunya + licitacions
   aparcades) i moure dades obertes / viz noves / espina a post-llançament? (recomanat) O vols
   alguna d'aquestes peces SÍ al dia 1?
2. **Fitxes de tota Catalunya.** Per als ~834 munis sense dades, dues opcions:
   (a) **prerenderitzar-los tots** amb un «sense dades encara» digne (URL real per a cada poble,
   bo per a SEO i enllaços directes) — recomanat; o (b) deixar-los al fallback SPA (404) i polir
   només el fallback. (a) és més sòlid; (b) és menys feina.
3. **Licitacions: enllaç o invisible?** La pàgina «en construcció» queda enllaçada a la nav/peu
   (honest: «això vindrà») o la treiem del tot fins que estigui? (recomano enllaçada a una pàgina
   digna «en construcció», no un grisat mort).
4. **Llengües al dia 1.** Sortim només ca/es (recomanat) i deixem aranès/anglès per a Fase 2?

---

## §1 · Aparcar licitacions net (P0) — Mirador

Objectiu: zero càlculs de licitacions a la vista, zero enllaços morts, zero xifres penjades. La
maquinària (`tools/export_licitacions.py`, artefacte, contracte, format) es CONSERVA per a Fase 2;
només es desconnecta del consum a la UI.

Superfície exacta (tots verificats):
- `packages/web/src/routes/licitacions/+page.svelte` (~289 l.) + `+page.ts` → **substituir per una
  pàgina «en construcció»** digna (no el `StubScreen` de segell «stub»; una pàgina que expliqui què
  vindrà i per què encara no hi és — coherent amb «cap xifra sense procedència»).
- Home: `src/routes/+page.ts` deixa de carregar `licitacions-bergueda.json`; `buildTroballes` rep
  `null` → la troballa `'lic'` **desapareix sola** (ja està condicionada a `lic?.municipis?.length`,
  `troballes.ts:92`). Cap codi mort.
- Fitxa: `src/routes/municipi/[slug]/+page.ts` deixa de carregar l'artefacte; `+page.svelte` amaga
  la secció de licitacions (condicional ja existent).
- Nav + peu (`+layout.svelte:93,126,162`): segons §0.3 — enllaç a «en construcció» o fora.
- `sitemap.xml/+server.ts`: que apunti la pàgina «en construcció» (o l'exclogui).
- CI: cap workflow ha de petar per l'artefacte (segueix al repo). Verificar `deploy-web.yml`.

**Criteri de sortida:** `grep -ri licitac` a la UI només troba la pàgina «en construcció» i la
maquinària desconnectada; build verd; cap enllaç a buit.

---

## §2 · Solidesa de la web (P0/P1)

1. **Cercador tota Catalunya (P0) — Mirador.** `MuniSearch` ha d'indexar els ~947 munis (del
   geojson `{ine5, nom}`), no els 31. Cada resultat porta a `/municipi/[slug]`, que ja degrada a
   «sense dades»/rang. *És el forat més greu de la promesa «tota Catalunya».*
2. **Fitxes de tots els munis (P0, depèn de §0.2) — Mirador.** Si (a): ampliar `entries()` a tots
   els munis del geojson; l'estat «sense dades encara» ja existeix. Si (b): garantir que el fallback
   retorna 200 i és digne.
3. **Stubs (P1) — Mirador.** `/index`, `/day-tripper`, `/politica`: o es treuen del build, o
   s'amaguen del tot (ja són inerts a la nav). Que ningú hi caigui i vegi un segell «stub».
4. **Estats buits i errors (P1) — Mirador + Llegenda.** Revisar cada pàgina amb dataset buit / muni
   desconegut / sense JS: que res sembli trencat.
5. **Mòbil (P1) — Mirador.** Mapa (MapLibre) i fitxes a pantalla petita; el drawer ja hi és.
6. **Rendiment (P1) — Mirador.** Pes del geojson de 947 munis a la home i `/mapa`; lazy/simplificar
   si cal.

**Criteri de sortida:** un usuari pot buscar qualsevol poble de Catalunya i arribar a una pàgina
digna; cap ruta visible mostra «stub»; build i navegació sòlids a mòbil i escriptori.

---

## §3 · «Tota Catalunya» honesta (P0/P1) — Talaia + Llegenda

1. **Missatge d'abast (P0).** Una frase clara, a la home i al mapa, que digui QUÈ cobrim avui
   (Berguedà complet · 82 munis en rang · la resta, context) i per què — perquè «sense dades» es
   llegeixi com a honestedat, no com a producte incomplet. *El mètode és el producte també aquí.*
2. **Coherència del rang (P1) — Brúixola/Talaia.** Repàs que enlloc una estimació sembli cens
   (mapa, tooltip, fitxa, `/metodologia`). Ja revisat al tram del mapa (#143); confirmar global.
3. **(Opcional, no bloqueja) estendre Nivell C** a més comarques abans del dia 1 si surt barat
   (Sondeig). No és requisit: la promesa «tota Catalunya» la compleix la web digna, no la cobertura
   de dades.

**Criteri de sortida:** la promesa «tota Catalunya» és honesta i ben comunicada; cap xifra es pot
llegir com a cens.

---

## §4 · Accessibilitat + còpia (P1) — Llegenda + Mirador

L'spec marca l'accessibilitat com a «barata d'inici, caríssima a posteriori». Mínim de dignitat:
- Teclat al mapa (i alternativa en taula ja existeix); contrast; `aria` dels controls.
- `axe-core` a CI (a `ci.yml`) com a xarxa de seguretat.
- Repàs de còpia ca/es (cap clau sense traduir; to coherent; sense jerga «above the fold»).

**Criteri de sortida:** navegable amb teclat; `axe-core` sense errors greus; còpia revisada.

---

## §5 · Ops de llançament (P0) — Talaia + Mirador

Checklist del dia D (tot ancorat, comentaris «treure al llançament» ja al codi):
- **Treure noindex als 3 llocs:** `app.html:15` (meta robots), `static/robots.txt` (→ `Allow: /` +
  `Sitemap:`), `static/_headers` (treure `X-Robots-Tag`).
- **og:image (P0):** crear la imatge de marca i afegir-la a `+layout.svelte` (avui no n'hi ha) →
  compartir a xarxes mostra targeta.
- **Sitemap complet:** que `sitemap.xml` inclogui totes les pàgines + munis publicats (i, si §0.2(a),
  tots els munis). hreflang ja hi és.
- **Deploy verd reproduïble:** `deploy-web.yml` a Cloudflare Pages; domini `riusdegent.cat`
  configurat; `_redirects`/`_headers` correctes.
- **Comprovació final:** build net, links, 404, mòbil, fosc/clar, ca/es.

**Criteri de sortida:** el lloc és indexable, comparteix bé, desplega verd al domini.

---

## Go / No-Go de llançament (tot ha de ser verd)
- [ ] Licitacions aparcades net (cap enllaç mort, cap xifra penjada).
- [ ] Cercador troba qualsevol municipi de Catalunya.
- [ ] Cap ruta visible mostra «stub»; estats buits dignes.
- [ ] Missatge d'abast «tota Catalunya» honest i clar.
- [ ] Cap xifra llegible com a cens; tota xifra amb procedència.
- [ ] noindex tret als 3 llocs; og:image; sitemap + robots de producció.
- [ ] Deploy verd al domini; ca/es; mòbil; a11y mínima.

## Riscos
- **Límit de despesa del compte** (actiu avui): bloqueja workflows multi-agent i tasques de dades
  amb IA (gen-fitxa, eval-writer, estendre Nivell C). Operatiu, no de codi; cal tenir-lo en compte
  per a qualsevol pas que depengui d'IA abans del dia D.
- **Fitxes thin** (si §0.2(a)): 834 pàgines «sense dades» són primes per a SEO; mitigació: contingut
  contextual honest + `noindex` selectiu si cal.
- **Rendiment del geojson** a escala Catalunya a mòbil.
- **Expectativa** : «tota Catalunya» pot fer esperar dades de tot arreu; el missatge d'abast ho ha de
  desactivar des del primer cop d'ull.

## Fora de llançament (post — Fase 2 de producte)
Dades obertes / xifra citable / embeds / kit premsa (§9) · visualitzacions noves (Dorling, slider,
«el riu», beeswarm, emblema doble corrent) (§4) · espina territorial + breadcrumb (§7) · pregunta-li
«super beta» genUI · llengües aranès/anglès · **licitacions de veritat** (menors → majors/diputació)
· estendre Nivell C a tot Catalunya + residus L2.

---
*Aquest pla és viu. Quan la Bea voti el §0, el converteixo en tasques a `bitacora/next.md` i obro els
PRs per fases (P0 primer). Filtre de l'spec que mantinc: «si una peça no pot explicar d'on surt, no
es publica».*
