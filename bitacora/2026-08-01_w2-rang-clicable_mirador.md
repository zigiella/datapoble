# 2026-08-01 · W2 — el rang, clicable + el nom de la comarca a la mediana (Mirador)

**Tasca:** els punts 1-3 del bloc «🗳️ VOTS DE BEA (2026-07-31)» de `bitacora/next.md`.
**Branca:** `mirador/w2-rang-clicable` · **Entrega:** un PR · **No fusiono jo.**

---

## 1 · Els dos vots de copy, aplicats

**«mitjana de Catalunya» es queda.** No s'hi ha tocat res: el denominador ja distingeix les dues
referències («sobre 31 municipis» vs «sobre 8.012.231 habitants»).

**La mediana duu el nom de la comarca escrit.** `gov_ref_comarca` passa de «mediana comarcal» a
«mediana {comarca}», i la targeta hi posa la forma amb article: **«mediana del Berguedà»**,
«mediana de l'Alt Empordà», «mediana de la Garrotxa», «mediana de les Garrigues», «mediana
d'Osona».

### L'arrossegament de `gov_rang_cap`, resolt traient-hi el nom

`gov_rang_cap` deia « · per valor a {comarca}» **just a sobre** de la mediana. Amb el vot de Bea,
el nom de la comarca hi sortiria **dues vegades seguides** a la mateixa targeta. Decisió: el nom
es queda a la MEDIANA (que és on Bea l'ha demanat i on fa més falta — una mediana sense el seu
perímetre no vol dir res) i `gov_rang_cap` passa a **« · per valor»**, que és la informació que
aquella línia aportava de debò (l'ordre és pel valor, descendent).

Resultat a la targeta del vidre de la Pobla, verificat al HTML prerenderitzat:

> 48,6 kg · **17 de 31** · rang comarcal · per valor
> 49,8 kg **mediana del Berguedà** · sobre 31 municipis
> 22,9 kg mitjana de Catalunya · sobre 8.012.231 habitants

El nom hi surt **una sola vegada**, i `verify-govern.mjs` ho exerceix simulant el text del bloc de
rang per a **les 43 comarques × 2 locales**: si algú torna a posar `{comarca}` a `gov_rang_cap`, cau.

### L'article: una taula lèxica i una funció, no un `if` per cas

`src/lib/contract/comarca-nom.js` (JS pur, com `slug-core.js` i `kpis.js`, perquè la guarda offline
pugui importar la MATEIXA funció). La taula declara **gènere i nombre** de les 43 comarques, no la
preposició ja muntada: així el català elideix davant de vocal («de l'Alt Empordà») i el castellà no
(«del Alt Empordà») sense duplicar la llista.

**Per què una taula i no una regla:** el gènere és **lèxic**, no es dedueix de com s'escriu el nom.
Garrotxa és femenina i Garraf masculí; Selva femenina i Segrià masculí; Anoia porta article i Osona
no, i totes dues comencen per vocal. Cinc formes existeixen a Catalunya (`del` ×25, `de la` ×9,
`de l'` ×7, `de les` ×1, `d'` ×1) i les cinc estan **ancorades a la guarda**: si algú «simplifica»
la taula a una regla d'ortografia, cauen.

**Fallback honest:** una comarca que no sigui a la taula no rep un article inventat — es pinta
`gov_ref_comarca_nd` («mediana comarcal», el text d'abans). Però abans d'arribar-hi, el CI cau: la
guarda compara la taula amb les 43 comarques REALS de `municipis-territori.json` i falla tant si en
falta una com si n'hi sobra una de morta.

---

## 2 · W2 — el rang, clicable

### La ruta triada: `/comarca/[slug]/[metrica]/`

Penja de `/comarca/[slug]/`, que ja existeix i ja té el seu índex (`/comarca/`, #295). Raons:

- **El llistat és una VISTA d'una comarca, no un nivell nou de l'espina.** Així el breadcrumb surt
  sol —Catalunya › vegueria › comarca › mètrica— reutilitzant el que ja hi havia, i la pàgina de
  comarca en pot ser la porta natural el dia que Bea la vulgui.
- L'alternativa (`/metrica/[metrica]/[comarca]/`) hauria fet de la mètrica el nivell superior i
  hauria obligat a inventar un índex de mètriques que ningú ha demanat.
- **El slug de la mètrica es DERIVA de la clau del contracte** (`metricaSlug`: `vidre_hab` →
  `vidre-hab`), no d'una segona taula de noms bonics que caldria mantenir sincronitzada. No és
  bonic, però una URL i la xifra que pinta no poden divergir sense que el CI ho vegi (la guarda
  comprova que els 9 slugs són distints i que la volta retorna la clau de partida).

### El cost del build, MESURAT abans de decidir

| | abans | després | delta |
|---|---|---|---|
| fitxers a `build/` | **5.933** | **7.484** | **+1.551** |
| pàgines `index.html` | 3.016 | 4.177 | +1.161 |
| mida | 2,42 GiB | 2,42 GiB | +48,5 MB |

Desglossament del delta: **1.161 `index.html`** (43 comarques × 9 mètriques × **3 còpies**
prerenderitzades = 46,8 MB) + **387 JSON** del prebuild (1,39 MB) + el sitemap, que passa de 788 kB
a 1,15 MB.

**⚠️ Matís sobre les «3 locales» del brief:** el projecte té **2 locales** (ca, es), però el build
n'emet **3 còpies** de cada ruta — la canònica sense prefix (fallback, que `_redirects` envia a
`/ca`) i les dues amb prefix. L'aritmètica del brief (1.161) és correcta; el motiu no era el que hi
deia. Ho anoto perquè el dia que es retiri la còpia canònica, el compte cau un terç.

**Decisió: es prerenderitza tot.** 7.484 fitxers són el **37 %** del límit de 20.000 de Cloudflare
Pages: hi ha marge de sobres. I la generació sota demanda no era una opció real: el site és
`adapter-static` i **no té servidor en runtime** on generar res. Cada pàgina de llistat pesa 44 kB
perquè el seu loader fa **un sol `fetch`** (el seu propi JSON, que ja porta la vegueria, la
definició de la mètrica i els rètols de les altres 8) — SvelteKit incrusta la resposta de cada
`fetch` del loader a CADA pàgina prerenderitzada, i per això la pàgina de comarca que ja existia
pesa 1,8 MB (hi carrega la geometria). No he repetit aquell error.

**Alerta per a Talaia:** el que s'apropa al límit no és això, és el nombre de pàgines × 3 còpies. A
947 municipis + 43 comarques + 387 llistats som a 7.484; una tercera dimensió d'aquesta mida
(p. ex. una pàgina per municipi × mètrica) no hi cabria. Val la pena tenir-ho present abans de
prometre-la.

### La dada: `copy-data.mjs` la parteix, no la calcula

`buildGovernLlistes()` llegeix `data/web/govern.catalunya.json` i el reagrupa per la partició de
`municipis-territori.json` (l'autoritat declarada al capçal de `mart_govern.sql`) cap a
`static/data/govern-llista/<comarca>/<metrica>.json`. **Mateixa frontera honesta que
`buildGovernSplit()`**: la font no es modifica, només es parteix perquè cada pàgina carregui el seu
tros. `tools/` i `data/` no s'han tocat.

**L'ordre és el `rang` LLEGIT**, no un `sort` pel valor. Ordenar pel valor hauria estat calcular
l'ordre al nostre costat (C6 §4) i, pitjor, hauria **desfet els empats**: el mart en declara **220
files empatades** a Catalunya. Els empatats comparteixen rang i s'ordenen entre ells per la clau
d'ordenació de noms (`nomIndex`), que és estable i no insinua cap ordre de valor.

**Guardes que trenquen el PREBUILD** (no un avís): si dins d'una comarca les cel·les d'una mètrica
no coincideixen en vintage, denominador o referències; si `n_amb_dada` del mart no és el nombre de
files amb rang que hi hem trobat; si falta la cel·la d'un municipi; o si el contracte servit no
declara la mètrica (un llistat sense font ni fórmula no es publica). Comprovat sobre els 947:
**0 divergències** als 387 parells.

### Els municipis sense dada (esmena de Bea, arribada a mig camí)

Van en un **bloc a part al final**, **sense ordenar** i **amb el seu motiu**. Mai barrejats amb els
que tenen valor ni ordenats com si el seu valor fos 0 — el cas fundacional és la Quar, on tractar
el percentatge suprimit com un zero la pintaria l'ÚLTIMA de la comarca quan, pel seu recompte, és
de les primeres (7 estrangers de 44 habitants ≈ 15,9 %, que la faria 2a).

**⚠️ El que jo NO puc verificar d'aquest cas:** el recompte de 7 **no és a `data/web/`**. La xifra
la va verificar Talaia al mart i està anotada a `next.md` amb la seva pròpia esmena («és cert al
mart i FALS al web: `poblacio_nacionalitat_estrangera` no és al catàleg servit»). Els comentaris
del codi ja la portaven des de B3 i els he mantingut amb aquesta àncora, no com a troballa meva.
Mentre el recompte no se serveixi, la pàgina del llistat **no el pot pintar**: la Quar hi surt amb
el motiu del llindar i prou. És el mateix handoff obert a Sondeig.

Són **30 a tot Catalunya** (de 8.523 cel·les), i les **tres causes** hi són totes:

- **llindar nostre** — nacionalitat estrangera: Berguedà 27 de 31 (Fígols, Gisclareny, la Quar,
  Sant Jaume de Frontanyà), Conca de Barberà 19 de 22, Alt Urgell 18 de 19, Baix Camp 27 de 28.
- **la font que la calla** — renda: 13 comarques, 20 municipis (l'INE no la publica; p. ex. la
  Vajol a l'Alt Empordà).
- **la divisió impossible** — índex d'envelliment: la Febró (Baix Camp), on no hi viu ningú de 0 a
  14 anys.

El motiu surt del MATEIX mapa que a la targeta (`GOVERN_DENOM_REASON`): no n'hi ha cap d'escrit a
la pàgina nova. I **no es repeteix**: el recompte va a dalt (on comença la llista ordenada) i el
motiu va al bloc dels que no en tenen, que és on el lector els té davant. A la targeta van junts
perquè allà no hi ha cap llista on ensenyar-los.

### La navegació entre municipis

Cada fila del llistat és un enllaç sencer a la fitxa del municipi (`aria-label` amb el nom, perquè
«17 la Pobla de Lillet 48,6 kg» no és un destí llegible per a un lector de pantalla). Al peu, la
navegació lateral cap a les **altres 8 mètriques de la mateixa comarca** i la tornada a la pàgina
de comarca.

**El que NO he fet i per què:** al llistat, el rang de cada fila **no** és un enllaç. Bea demana
«clicar cada vegada que posi rang i accedir al llistat»; al llistat ja hi ets, i un enllaç a la
pàgina on ja ets és soroll. La fila enllaça al municipi, que és el moviment que hi té sentit.

### Duplicacions retirades pel camí

Tres coses que la pàgina nova hauria duplicat i que ara són **font única** (i amb guarda):

- `GOVERN_UNIT`/`governUnit` → de la fitxa a `kpis.js`. Dues còpies eren dues pantalles dient «kg»
  i «» del mateix vidre.
- `formatBoardValue` → de la fitxa a `$lib/format`. Dues còpies eren la mateixa dada amb dos
  nombres de decimals segons per on hi arribes.
- El cos del rang («k de n» + rètol) → un `{#snippet rangCos}` propi, perquè l'enllaç el pugui
  embolcallar **sense duplicar el marcatge** (amb enllaç / sense enllaç serien dues còpies que
  poden divergir, que és precisament el que el snippet compartit existeix per impedir).

---

## 3 · Verificació

`check` ✅ 0 errors · `build` ✅ · `verify:govern` ✅ · `verify:docs` ✅ · cap error de consola.

**`preverify:govern` nou:** el verificador ara regenera els artefactes abans de córrer. Sense això,
la guarda dels 387 llistats podria passar sobre una còpia vella — «una guarda que no s'executa
decora, no protegeix».

**Guardes noves (secció W2 de `verify-govern.mjs`), provades EN NEGATIU: 19 sabotatges, 19 cauen.**

Sobre el codi: `gov_rang_cap` recupera `{comarca}` · la mediana perd el nom · una comarca surt de
la taula d'article · el gènere d'una comarca es corromp · el castellà elideix com el català · el
rang deixa de ser enllaç · el destí del rang s'escriu a mà · el llistat ordena al front · el bloc
dels «sense dada» desapareix del marcatge · el denominador s'amaga amb `opacity: 0` · la unitat
curta es torna a duplicar · dues mètriques al mateix slug.

Sobre l'artefacte: la llista s'ordena pel valor · un municipi desapareix · un empat es pinta com a
guanyador únic · el denominador publicat no és el que es veu · un valor es retoca · la procedència
no és la del contracte · els llistats no existeixen (la guarda no es dona per verificada).

**Al navegador** (i al HTML prerenderitzat, que és on verifico de debò):

- Fitxa de **la Pobla**: els **9** rangs són enllaços. Clic al del vidre → `/ca/comarca/bergueda/
  vidre-hab/`, 31 municipis, **la Pobla 17a**, amb 49,8 (mediana del Berguedà) i 22,9 (Catalunya).
- Clic a una fila (Gósol) → `/ca/municipi/gosol/`.
- **Barcelona** → `/ca/comarca/barcelones/vidre-hab/`, 5 municipis, Barcelona 1a; «Barcelonès»
  surt **una vegada** a la targeta.
- **Nacionalitat al Berguedà** (ca i es): 27 de 31, i els 4 hi surten al final amb el motiu del
  llindar de 50.
- **Renda a l'Alt Empordà** (es): 67 de 68, «del Alt Empordà», la Vajol amb el motiu de la font.
- **Envelliment al Baix Camp**: la Febró amb el motiu de la divisió impossible.
- Cap error de consola a cap de les pàgines visitades.

---

## 4 · Premisses del brief que he trobat falses

Tres briefs seguits n'han portat una, i el brief em demanava buscar-les. N'he trobat **una i
mitja**, totes dues menors — el brief d'avui és el més sòlid dels quatre:

1. **«3 locales».** Són **2** (ca, es). El build n'emet 3 còpies perquè hi ha la ruta canònica de
   fallback. L'estimació de 1.161 pàgines és correcta, però pel motiu equivocat.
2. **«el build ja és gran (~5.900 fitxers / 2,3 GB)».** Els fitxers, clavats (5.933). La mida és
   **2,42 GiB**, no 2,3 — diferència irrellevant per a la decisió, però ho anoto perquè el número
   es va escriure sense mesurar-lo i el mateix hàbit, a una altra xifra, no seria irrellevant.

I una **confirmació** que val la pena deixar escrita, perquè el brief la donava per bona i podia no
ser-ho: **la Pobla és 17a de 31 al vidre del Berguedà** — verificat al mart i ancorat a la guarda.

---

## 5 · Idees i candidates a següent tasca (per a la tria de Talaia)

- **La pàgina de comarca no té encara cap porta cap als 9 llistats.** Hi arribes des de la fitxa
  d'un municipi (que és el que Bea demanava) i des de la navegació lateral d'un altre llistat, però
  `/comarca/[slug]/` no els enllaça. Són tres línies i tanca el cercle de l'espina.
- **`n_comarca` al mart** (handoff obert des de B3, `2026-07-31_b2-b3-copy-denominador_mirador.md`):
  ara el compto de la partició territorial a **dos** llocs (el loader de la fitxa i el prebuild del
  llistat). El lloc durador és la cel·la de govern. → **Sondeig**.
- **La pàgina de comarca pesa 1,8 MB** perquè el seu loader carrega la geometria sencera i
  SvelteKit la incrusta a cadascuna de les 129 còpies (76 MB de build per 43 pàgines). Es podria
  partir com s'han partit el govern i el tauler. → **Mirador**.
- **Copy PENDENT DEL VOT de Bea** (funciona, però la frase exacta és seva):
  - `gov_rang_cap` = « · per valor» — és el que queda després de treure-hi el nom de la comarca.
    ¿Prou clar tot sol, o millor « · ordenats pel valor»?
  - `llistat_sense_lead` = «Hi surten igualment, i no ordenats: no tenir la xifra no vol dir zero,
    i tractar-la com un 0 els pintaria últims sense ser-ho.»
  - En **castellà**, la contracció fa servir l'article castellà sobre el topònim català: «del Alt
    Empordà», «de las Garrigues», «de Osona». És l'ús estàndard, però és copy i el vot és seu.
  - `llistat_taula_title` = «Ordenats pel valor ({n})».

---

**Handoff a: Sondeig** — `n_comarca` a la cel·la de `mart_govern` (segona vegada que el demano;
ara el recompte viu duplicat a la web).
**Handoff a: Talaia** — la porta des de `/comarca/[slug]/` cap als llistats i el pes de la pàgina
de comarca, si els vol encuar.
