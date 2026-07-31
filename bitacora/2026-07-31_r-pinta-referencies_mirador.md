# R-PINTA — les dues referències a cada targeta amb rang (Mirador, 2026-07-31)

**Tasca:** R-PINTA, decisió B+D de Bea («ponderada de Catalunya + mediana de la comarca»).
Branca: `mirador/r-pinta-referencies`. **No fusiono jo.** Jurisdicció tocada: només `packages/web/`.

---

## 0 · Resum en una pantalla

- Cada targeta **amb rang** pinta ara **dues referències**: la **mediana comarcal** (mateix
  perímetre que el rang) i la **mitjana de Catalunya** (la ponderada, ancoratge oficial), cadascuna
  **amb el seu denominador**. `poblacio` en pinta **una** —no té ponderada— i no hi queda cap buit.
- **⛔ UNA PREMISSA DEL BRIEF ÉS FALSA I ERA LA PEÇA CENTRAL.** El brief diu: «una **ponderada**
  es diu "sobre N **habitants**"». **No és cert a 2 de les 9 mètriques amb rang.** El mart pondera
  cada mètrica pel SEU pes (`pes_ponderada`), i n'hi ha **cinc** de diferents: tres són gent, però
  `pct_noprincipal` es pondera per **HABITATGES** (3.915.127) i `index_envelliment` per **MENORS
  DE 15 ANYS** (1.079.859). Escriure «habitants» sota aquelles dues hauria estat exactament el
  defecte que la regla de ferro (C6 §8.1) existeix per impedir: una procedència falsa, ben
  maquetada. Vegeu §2 — és la troballa d'aquesta passada.
- Jerarquia triada i mesurada al navegador: les dues referències viuen **dins el bloc del rang**
  (§3). La primera versió que vaig maquetar ocupava **95 px** per targeta amb salts de línia
  irregulars; la que entrega, **61 px** i sense cap salt lleig (§3.2).
- **Guardes noves a `verify-govern.mjs`**, exercides sobre les **16.039 referències pintables** dels
  947 municipis, i **provades EN NEGATIU 14/14** (§5).
- ⚠️ **EL COPY NOU ÉS PENDENT DEL VOT NARRATIU DE BEA** (§6, amb el mirall en es).

---

## 1 · Què mana i què s'ha fet

La doctrina vinculant és al capçal de `semantic/metrics.yml`, bloc **«QUINES ES PINTEN»** (vot de
Bea «farem B+D» + la correcció mesurada de Talaia). En curt:

| família | què respon | denominador | es pinta? |
|---|---|---|---|
| `ponderada_catalunya` | «quant li toca a cada habitant» (= com ho publiquen ARC/ICAEN/Idescat) | `hab_ponderada_catalunya`, **en unitats del seu pes** | **SÍ** |
| `mediana_comarca` | «com és un municipi típic **d'aquí**» | `n_amb_dada` **municipis** | **SÍ** |
| `mediana_franja` | «com són els municipis de la meva mida» | `n_franja` | **NO** (la comarca explica millor a 8 de 9) |

No ha calgut cap dada nova: `govern.catalunya.json` ja ho serveix tot per municipi i mètrica, i
`copy-data.mjs` ja el parteix per shard. **No he tocat `tools/` ni `data/`.**

Fitxers tocats (6, tots a `packages/web/`):

| fitxer | què hi entra |
|---|---|
| `src/lib/contract/govern.ts` | els camps nous de `GovernCell` tipats i documentats (inclosos els servits-i-no-pintats, amb el motiu) |
| `src/lib/govern/kpis.js` | `GOVERN_PES_DENOM`, `GOVERN_REF_DENOM_MUNIS` i `governReferences()` — font única compartida amb el verificador |
| `src/routes/municipi/[slug]/+page.svelte` | resolució de textos, marcatge dins el snippet `rangComarcal` i CSS |
| `messages/{ca,es}.json` | 6 claus noves ×2 idiomes |
| `scripts/verify-govern.mjs` | la secció R-PINTA de guardes |

---

## 2 · La premissa falsa del brief: «una ponderada es diu sobre N habitants»

El brief ho dona per fet dues vegades («els números hi són: `n_amb_dada`,
`hab_ponderada_catalunya`»). Vaig anar a comptar-ho a la dada servida abans d'escriure el copy:

```
index_envelliment          -> pes_ponderada = pob_0_14          (1.079.859)
kg_hab_any                 -> pes_ponderada = poblacio_residus  (8.012.231)
kwh_hab                    -> pes_ponderada = poblacio_kwh      (8.012.231)
pct_nacionalitat_estrangera-> pes_ponderada = poblacio          (8.123.780)
pct_noprincipal            -> pes_ponderada = hab_total         (3.915.127)
poblacio                   -> pes_ponderada = (cap)             — no té ponderada
renda_neta_persona         -> pes_ponderada = poblacio          (8.122.641)
rtc_per_1000hab            -> pes_ponderada = poblacio          (8.124.126)
vidre_hab                  -> pes_ponderada = poblacio_residus  (8.012.231)
```

**Cinc pesos, i dos NO són persones.** El 3.915.127 de `pct_noprincipal` són **habitatges** (és el
denominador del propi percentatge: habitatges no principals sobre habitatges totals); el 1.079.859
de l'`index_envelliment` són **menors de 15 anys** (l'índex és 65+/0-14, i el seu agregat honest és
sum(65+)/sum(0-14), tal com el capçal del contracte exigeix a la PRECISIÓ de l'arbitratge).

Si hagués seguit el brief al peu de la lletra, la fitxa hauria dit **«23,6 % · mitjana de
Catalunya · sobre 3.915.127 habitants»** sota el % d'habitatge no principal. És un número correcte
amb una procedència inventada — la mateixa forma d'error que el «500 d'Idescat» al costat de xifres
municipals que sumen 476,85.

**Com s'ha resolt, i per què així:** el nom del denominador **es deriva de `pes_ponderada`**, no
s'escriu una vegada per a totes. `GOVERN_PES_DENOM` (a `kpis.js`) mapeja pes → clau i18n. **Un pes
que no sigui al mapa no es pot nomenar → la referència NO es pinta**, i el verificador **cau**
(guarda (e), §5). Així, el dia que Sondeig serveixi una mètrica amb un pes nou, arriba amb el seu
nom o el CI s'atura: no desapareix una referència en silenci ni surt amb una etiqueta prestada.

*El brief també diu que la mediana «es diu sobre N municipis». Això sí que és cert a totes, i
`n_amb_dada` és a més exactament el conjunt que ordena el rang (l'arbitratge (a) de Talaia).*

---

## 3 · La jerarquia triada, i per què

### 3.1 · On van

Les dues referències es pinten **dins el snippet compartit `rangComarcal`**, immediatament sota el
«k de n» i la seva línia de denominador (B3). Tres raons, per ordre de pes:

1. **Comparteixen pregunta amb el rang.** «17 de 31» i «la mediana d'aquests mateixos 31» són la
   mateixa lectura —*contra qui*—; separar-les hauria trencat la unitat i, sobretot, hauria obert
   la porta a **tres còpies del marcatge**, que és el defecte que B3 acabava de tancar.
2. **Adjacència: el rang ja ha dit de quina comarca parlem.** La línia de sobre pinta «· per valor
   a Barcelonès», així que el rètol pot ser **«mediana comarcal»** sense repetir el topònim ni
   patir amb l'article (*del Berguedà* / *de l'Alt Empordà* / *de la Segarra*: en català l'article
   canvia amb el nom, i el copy actual ja arrossega aquest tema a `gov_rang_cap`). A Barcelona, on
   el brief avisava del risc de confusió, la targeta de vidre es llegeix així i no confon:
   `1 de 5 · rang comarcal · per valor a Barcelonès` → `14,6 kg · mediana comarcal · sobre 5
   municipis` → `22,9 kg · mitjana de Catalunya · sobre 8.012.231 habitants`.
3. **Hereten la posició del rang a cada punt de crida** (capçalera de presència i targeta de
   mètrica el col·loquen en llocs lleugerament diferents dins la targeta). Una sola font, cap deriva.

**Ordre dins el bloc: la COMARCAL primer, la CATALANA a sota.** La comarcal comparteix perímetre
amb la línia que el lector acaba de llegir; la catalana és l'ancoratge estable, idèntic a totes les
targetes de totes les fitxes, i per això va al peu del bloc, on el lector la troba sempre al mateix
lloc. El cas de Bea, a la fitxa real:

```
Vidre recollit selectivament kg/hab/any
48,6 kg
17 de 31 · rang comarcal · per valor a Berguedà
  49,8 kg   mediana comarcal
            sobre 31 municipis
  22,9 kg   mitjana de Catalunya
            sobre 8.012.231 habitants
```

«Normal aquí, el doble que a Catalunya» es llegeix d'una passada vertical perquè **les tres xifres
cauen a la mateixa columna**: el valor gran, i després les dues referències alineades a la dreta en
una **única graella** compartida (cada fila és `display: contents`), no una graella per fila.

### 3.2 · El mur, mesurat i evitat

El brief avisa: «vigila que no es converteixi en un mur». No m'ho vaig creure de memòria; ho vaig
mesurar a la targeta real (269 px d'ample al preview de producció):

| versió | alçada del bloc | com trencava |
|---|---|---|
| rètol i denominador en UNA línia (`mediana comarcal · sobre 31 municipis`) | **95 px** | irregular: 2 línies a la primera referència, 3 a la segona |
| rètol i denominador en **dues línies pròpies**, graella compartida | **61 px** | cap salt: 2 línies exactes per referència |

**−36 %**, amb el mateix text i sense amagar res. Ho paga que el denominador tingui element propi
(`.gov-kpi__refd`, un pèl més tènue que el rètol però **mai amagat**: hi ha guarda que cau si algú
li posa `opacity: 0`, `display: none` o `font-size: 0`).

Comprovat també a 375 px (mòbil): les targetes hi són **més amples** (341 px), les dues referències
hi caben igual i el bloc no desborda. *(L'`overflowX` de la pàgina a mòbil ve dels `path` del camp
de contorn del hero — és anterior a aquesta passada i no el toco.)*

**Cost mesurat:** els 9 blocs de referències ocupen **6.282 B** de la fitxa de la Pobla (**0,6 %**
de la pàgina) i 6.274 B a la de Barcelona (0,8 %). Cap petició nova: la dada ja viatjava al shard.

---

## 4 · Els casos que el brief demanava exercir

| cas | què s'ha vist a la pàgina construïda |
|---|---|
| **la Pobla de Lillet** (08166) | les 9 targetes amb rang porten les dues referències; les tres físiques: residus `759,9 / 476,8` · elèctric `1.694,6 / 1.252,1` · vidre `49,8 / 22,9`, totes amb «sobre 31 municipis» i «sobre 8.012.231 habitants» |
| **Barcelona** | rang «1 de 5 · a Barcelonès» i mediana «sobre 5 municipis» — el perímetre petit queda dit, no insinuat |
| **sense ponderada** | `poblacio` (capçalera de presència): **una sola línia**, «260 hab. · mediana comarcal · sobre 31 municipis». Cap buit, cap «n. d.» decoratiu. Verificat als **947**, no només a la Pobla |
| **denominador ≠ habitants** | `% habitatge no principal` → «sobre 3.915.127 **habitatges**» · `índex d'envelliment` → «sobre 1.079.859 **menors de 15 anys**» |
| **perímetre del rang** | `% nacionalitat estrangera` a la Pobla: rang «6 de 27» i mediana «sobre **27** municipis» — el mateix conjunt, com mana l'arbitratge (a) |
| **/es** | mirall complet: `mediana comarcal` · `media de Cataluña` · `sobre N municipios/habitantes/viviendas/menores de 15 años` |

**Un valor suprimit no porta referències**, perquè el bloc penja del rang i un valor `NULL` no en
té: a la Quar, el % de nacionalitat segueix sortint «n. d.» amb el seu motiu i sense cap
comparació al costat. És el que toca —comparar un forat no vol dir res—, però ho deixo dit per si
algú el volia veure comparat.

---

## 5 · Les guardes noves (i les proves en negatiu)

Tot a `scripts/verify-govern.mjs`, secció **R-PINTA**. La mecànica viu a `governReferences()`
(`kpis.js`), **funció pura importada pel verificador**: la guarda l'exerceix sobre els 947 × 9 en
comptes de deduir-ho del marcatge.

- **(a) cablatge** — les referències es resolen **dins** el snippet compartit; un sol marcatge.
- **(b) i18n** — cada rètol i cada denominador declarats existeixen a ca+es, **es pinten**, i cada
  denominador porta el seu `{n}`.
- **(c) els noms no s'intercanvien** — sobre el TEXT: la mediana ha de dir *municipis* i no
  *habitants*; cap ponderada pot dir *municipis*; `hab_total` ha de dir *habitatges/viviendas* i
  `pob_0_14` *menors/menores*. És la guarda que protegeix la troballa del §2 d'una passada de copy.
- **(d) l'estratificada no arriba a la pantalla** — `mediana_franja`, `n_franja` i `franja_poblacio`
  no es llegeixen al codi de la fitxa (es mira el codi **sense comentaris**, perquè el comentari que
  explica per què no es pinta pugui anomenar-la).
- **(e) tot pes servit té nom** — un `pes_ponderada` nou sense entrada a `GOVERN_PES_DENOM` faria
  desaparèixer una referència **en silenci**: ha de fer caure el CI.
- **(f) les 16.039 referències, exercides** — cap sense denominador; la mediana sempre sobre
  `n_amb_dada` municipis; la ponderada mai sobre municipis i sempre sobre el seu propi denominador;
  i **cap xifra recalculada al front** (identitat estricta amb el mart). També: cada targeta amb
  rang en té exactament 2 (1 a `poblacio`), i `n_amb_dada ≥ 2` perquè «sobre 1 municipis» no pugui
  sortir mai.
- **(g) `poblacio` sense ponderada** — als 947, `ponderada_catalunya` és NULL i la targeta pinta
  **només** la comarcal.
- **(h) l'àncora de Bea** — la Pobla: ordre comarcal→catalana, 49,8 vs 22,9, el vidre del municipi
  encara ≈ el doble de Catalunya, i el vidre ponderat per la població del dataset de l'ARC.
- **(i) el denominador es veu** — element propi i sense CSS que l'amagui.

**Provades EN NEGATIU: 14/14** (script d'un sol ús; cada cas fa un patch, corre el verificador,
exigeix vermell amb el missatge esperat i restaura):

| # | mutació | la guarda cau |
|---|---|---|
| N1 | la ponderada per població es diu «sobre {n} municipis» | ✅ |
| N2 | la mediana es diu «sobre {n} habitants» | ✅ |
| N3 | el pes d'habitatges es diu «habitantes» (es) | ✅ |
| N4 | un denominador perd el seu `{n}` | ✅ |
| N5 | s'esborra `hab_total` de `GOVERN_PES_DENOM` (pes servit sense nom) | ✅ |
| N6 | la ponderada es pinta amb el denominador de la mediana | ✅ |
| N7 | la fitxa llegeix `cell.mediana_franja` | ✅ |
| N8 | les referències deixen de resoldre's dins el snippet compartit | ✅ |
| N9 | s'inverteix l'ordre (catalana abans que comarcal) | ✅ |
| N10 | la mediana s'arrodoneix AL FRONT | ✅ |
| N11 | un rètol declarat desapareix d'un dels dos idiomes | ✅ |
| N12 | `poblacio` es queda sense cap referència | ✅ |
| N13 | el denominador s'amaga amb `opacity: 0` | ✅ |
| N14 | el denominador es fon amb el rètol (perd element propi) | ✅ |

*(N13 va caçar un error MEU mentre l'escrivia: la primera versió de la guarda casava
`font-size: 0` dins de `font-size: 0.56rem` i tombava el verd. Corregida abans d'entregar.)*

---

## 6 · ⚠️ COPY NOU — PENDENT DEL VOT NARRATIU DE BEA

Sis claus noves. **El mecanisme està tancat; la frase, no.**

| clau | ca | es |
|---|---|---|
| `gov_ref_comarca` | mediana comarcal | mediana comarcal |
| `gov_ref_catalunya` | mitjana de Catalunya | media de Cataluña |
| `gov_ref_denom_munis` | sobre {n} municipis | sobre {n} municipios |
| `gov_ref_denom_hab` | sobre {n} habitants | sobre {n} habitantes |
| `gov_ref_denom_habitatges` | sobre {n} habitatges | sobre {n} viviendas |
| `gov_ref_denom_menors15` | sobre {n} menors de 15 anys | sobre {n} menores de 15 años |

Les dues decisions de redacció que porto a votació:

1. **«mitjana de Catalunya» per a la ponderada.** El contracte diu que és «el número que un lector
   entén per *la mitjana*», i el denominador («sobre 8.012.231 habitants») és el que la fa
   ponderada sense fer servir la paraula. L'alternativa honesta i més freda seria «mitjana
   ponderada de Catalunya», que és exacta i probablement il·legible per a un alcalde.
2. **«mediana comarcal» sense el nom de la comarca.** Guanya adjacència (el rang l'acaba de dir) i
   esquiva l'article. Si Bea el vol escrit, cal resoldre abans l'article per comarca — i llavors
   convindria arreglar-ho **també** a `gov_rang_cap`, que avui diu «per valor a Berguedà».

---

## 7 · Premisses del brief, revisades

| el brief deia | veredicte |
|---|---|
| «una **ponderada** es diu *sobre N habitants*» | **⛔ FALSA a 2 de 9.** §2. És la peça que ha reorientat el disseny |
| «Ja està TOT servit a `govern.catalunya.json`» | **✅ cert**, i comprovat: 947/947, cap `mediana_comarca` nul·la on hi ha rang, cap ponderada sense el seu `hab_ponderada_catalunya` |
| «`poblacio` no té ponderada» | **✅ cert als 947** |
| «`mediana_franja` NO es pinta» | ✅ adoptat, amb guarda |
| «dues línies més» a la targeta | ⚠️ **matís mesurat**: amb el denominador obligatori són **quatre** línies de text (61 px), no dues. Amb dues de sole no hi cabia la procedència sense trencaments lletjos (§3.2) |
| «la teva assignació viu a `next.md`» (CLAUDE.md / Charter §IV) | **⛔ R-PINTA NO hi era.** Vegeu §8 |

---

## 8 · Nota de mètode (no de codi)

**L'assignació de R-PINTA no era a `bitacora/next.md`** quan he despertat: el meu bloc hi tenia la
feina de B2/B3 i W1/W5 tancada i el handoff de Sondeig encuat, però cap tasca R-PINTA. El brief va
arribar **només pel latido**, que és l'antipatró que el Charter §V anomena explícitament («passar
la tasca pel xat sense haver-la escrita abans a `next.md`»). Ho treballo perquè la decisió B+D **sí**
que és al repo (commit `a26be2a`, capçal de `semantic/metrics.yml`) i perquè la instrucció no
contradiu res del que hi ha escrit — però ho deixo dit, i afegeixo el bloc a `next.md` en aquest
mateix PR perquè la propera reconstrucció-des-del-repo la trobi.

---

## 9 · Verificació

| pas | resultat |
|---|---|
| `npm run check` | **0 errors / 0 warnings** (1.279 fitxers) |
| `npm run build` | **verd** (adapter-static, `build/` escrit) |
| `npm run verify:govern` | **OK** + la secció R-PINTA nova (16.039 referències, 1.893 amb pes no-habitants) |
| `npm run verify:docs` | **OK** |
| `python packages/transform/verify_tendencia.py` | **OK** (obligatori: he tocat `kpis.js`) — 20.802 files, cap fletxa sense període |
| guardes noves en negatiu | **14/14** |
| navegador (build de producció, servit des del MEU worktree) | la Pobla ca+es, Barcelona, capçalera de presència sense ponderada · **cap error de consola** |
| `noindex` | **intacte** (`app.html`, present a `build/index.html` i a les fitxes) |
| P1/P2 | segueixen ocults (`MOSTRA_LECTURES_IA = false`, no tocat) |

*Nota de risc #5 (recursos compartits), la mateixa cicatriu de W1/W5:* **no** he fet servir la
config `web` de `.claude/launch.json` (fa `--prefix packages/web` relatiu al cwd del procés i em pot
servir el `build/` d'un altre arbre). He aixecat `vite preview` **des del meu `packages/web`** en un
port propi i he comprovat que servia el meu build buscant-hi una classe que no existeix enlloc més.

---

## 10 · Handoffs i idees per a la cua

- **➡️ Handoff a: Bea (vot narratiu)** — les sis claus del §6, i la pregunta de si «mediana
  comarcal» ha de dur el nom de la comarca (arrossegaria `gov_rang_cap`).
- **➡️ Handoff a: Sondeig (no bloquejant)** — `pes_ponderada` arriba com a clau tècnica
  (`poblacio_kwh`, `poblacio_residus`). Avui el front la tradueix a un nom llegible amb un mapa
  propi i guardat; si algun dia el mart pogués servir **la unitat** del pes (o el `label` de la
  mètrica del pes), el front deixaria de mantenir aquest mapa. **No cal per a res ara.**
- **Idea per a la cua (Mirador):** la referència **catalana és idèntica a totes les 947 fitxes** i
  avui viatja repetida a cada shard. Si algun dia el pes de `govern.catalunya.json` torna a
  molestar, aquesta és la primera peça a factoritzar (un sidecar de 9 files) — no ho faig ara
  perquè el cost mesurat és 0,6 % de la pàgina i partir-ho afegiria una petició.
- **Encuat i NO fet aquí (ve de W1/W5):** el handoff de Sondeig sobre `GOVERN_RANK_KEYS` ja no
  aplica — `vidre_hab` i `pct_nacionalitat_estrangera` **ja hi són** i el `pendingRank` que quedava
  és el de `pct_nascuda_estranger`, que és correcte (aquella mètrica segueix sense rang al mart).
