# R-FUNC · El radar de subvencions vist des de secretaria
## Especificació funcional per a l'ajuntament d'un poble com la Pobla de Lillet

**De:** Marea (consultora externa) · **Per a:** Bea (direcció) i, si ella ho decideix, Talaia (adopció)
**Data:** juliol 2026 · **Relació amb el repo:** aquest document **no és un contracte**: omple de contingut real (fonts, perfil, correu, calendari, model d'accés) el que **C3 i C4 regulen en forma**. On xoqui amb C3/C4 o amb l'spec adoptada, **manen ells**.
**Nota de revisió (contra main #257):** escrit inicialment contra #243; revisat després del cicle #244–#257. **L'Annex A queda SUPERAT** per `docs/ajuntaments/banc-c4-etiquetatge.md` (#251), que ja fixa el criteri amb matisos millors apresos de les 26 candidates reals de R1. El que segueix aportant: §2 (mapa de finançadors verificat: PUOSC, Leader/ADRCatCentral, memòria de cicle), §3 (perfil proposat — `config/municipis/` encara no existeix), §4 (anatomia del correu), §8 (mètrica dels dies de marge) i **§9–9.2 (decisions de direcció de Bea: privat per disseny, entorn de dev, espai del radar)**.

---

## 1. L'usuari real i la regla dels 90 segons

A un municipi de 1.106 habitants, qui gestiona subvencions és **secretaria-intervenció** (sovint compartida amb altres municipis o coberta amb suport del Consell Comarcal/SAT de la Diputació) més l'alcaldia. Temps disponible per a "vigilar convocatòries": **zero** — per això existeix el radar.

**Regla de disseny #1 — els 90 segons:** el correu del radar s'ha de poder llegir i decidir («ens interessa / no») amb el cafè, en 90 segons. Tot el que no hi cap (bases senceres, tecnicismes, històrics) va darrere d'un enllaç, mai al cos.

**Regla de disseny #2 — el marge és or:** una convocatòria detectada amb 3 dies de termini és gairebé inútil (un ple, un informe d'intervenció i una memòria no surten en 3 dies). El radar reporta sempre **dies naturals de marge** i la mètrica d'utilitat el mesura (§8).

---

## 2. Mapa real de finançadors (verificat juliol 2026)

| Finançador | Línies que importen a un poble XS | On es publica | Ho veu el radar v1? |
|---|---|---|---|
| **Diputació de Barcelona** | Catàleg de serveis (2026: ~325 recursos, 114 M€; finestra principal ~gener-febrer per la majoria de recursos), fons de prestació, línies sectorials | Cercador del Catàleg + seu electrònica; **els ajuts econòmics es publiquen a BDNS i RAISC** | ✅ via BDNS (R1) + CIDO (R5) com a xarxa de seguretat catalana |
| **Generalitat** | Departaments (Cultura, Territori, Acció Climàtica, Drets Socials…), línies a ens locals | DOGC + RAISC + BDNS | ✅ via BDNS/CIDO |
| **PUOSC** | LA línia d'inversió municipal (2025-2029: 500 M€, concurrència **no competitiva**) | Convocatòria única DOGC 11-02-2025 (Res. PRE/381/2025), via EACAT | ⚠️ **ja convocat i tancat**: no és detecció, és **memòria de cicle** (§5) |
| **Estat** | IDAE/MITECO (enllumenat, eficiència), 1,5% cultural, MPT, Next Generation romanents | BOE + BDNS | ✅ via BDNS |
| **Leader / ADRCatCentral** | Ajuts Leader (2026 **oberta ara**, ~600 k€/any al Berguedà, ens públics elegibles; via SIDER) | Web del GAL (catcentral.cat) + DOGC/BDNS (DARP) | ✅ via BDNS; el web del GAL queda com a font d'**anticipació** (§5) |
| **Consell Comarcal / Agència de Desenvolupament del Berguedà** | Ajuts i traspassos comarcals, borses | Taulers propis | ⚠️ parcial: si passa per BDNS sí; el tauler propi és forat conegut de v1 (anotat, no tapat) |
| **UE directa** (Interreg, LIFE…) | Rarament a l'abast d'un XS sense soci | Portals UE | ❌ fora v1 (soroll >> senyal per a aquest perfil) |

**Lectura honesta:** BDNS cobreix el 80-90% del que un poble XS pot demanar (Diba inclosa — verificat). CIDO (R5) no és redundant: és la xarxa de seguretat catalana i sovint porta el context en català. Els forats reals de v1 són els **taulers comarcals** i l'**anticipació de finestres** — tots dos anotats aquí perquè ningú es pensi que el radar hi veu.

---

## 3. El perfil real de la Pobla — proposta de `config/municipis/08166-lillet.yaml`

*(Valors proposats per Marea des del coneixement del projecte; **la llista final la valida l'Ajuntament** — és exactament la pregunta «quines són les tres feines que més temps us mengen?» de la reunió amb en Jordi.)*

```yaml
tipus_beneficiari: ajuntament
poblacio: 1106
poblacio_any: 2025          # padró, catàleg canònic del repo
territori: [municipi:08166, comarca:bergueda, provincia:barcelona, catalunya, estatal]
materies:
  - { nom: turisme i patrimoni,              pes: 0.9 }   # Jardins Artigas, tren, monestir
  - { nom: envelliment i serveis socials,     pes: 0.9 }   # 35% +65: prioritat social
  - { nom: eficiencia energetica i enllumenat, pes: 0.8 }
  - { nom: digitalitzacio i administracio,    pes: 0.8 }   # SeTDIBA, videoactes, dades
  - { nom: cultura i memoria,                 pes: 0.7 }   # arxiu, memòria oral
  - { nom: camins, natura i espais publics,   pes: 0.7 }
  - { nom: habitatge,                         pes: 0.6 }   # tesi datapoble: pressió residencial
  - { nom: ocupacio i promocio economica,     pes: 0.5 }
projectes_en_cartera:       # llista VIVA — l'actualitza l'equip de govern, no el radar
  - "guia turística QR multilingüe (amb Castellar de n'Hug)"
  - "digitalització d'arxiu i memòria oral"
  - "millora enllumenat públic"
  - "videoactes i transparència del ple"
cofinancament_max: 20000    # € — llindar prudent; a validar amb intervenció
destinataris: [<correu de Bea>]   # v1 experimental, per C3 §6
actiu: true
```

**Per què els pesos importen:** no filtren (això és el filtre dur de R2, determinista) — **ordenen** el correu i graduen el semàfor dels casos frontera. Una convocatòria d'habitatge (0.6) elegible surt igualment; surt més avall i en groc si és dubtosa.

---

## 4. El correu (el producte de debò)

**Assumpte:** `Radar subvencions · dj 17/07 · 1 verda, 2 grogues`

```
🟢 VERDA · Diputació de Barcelona — Millora de l'enllumenat públic exterior
   Import: fins a 40.000 € · Cofinançament: 0 % · Termini: 30/09 (74 dies de marge)
   Per què encaixa: matèria "eficiència energètica" (pes 0,8) + beneficiari ens local
   <5.000 hab. + tens "millora enllumenat" en cartera.
   Següent pas: sol·licitud via PMT. → [enllaç oficial] · [afegir termini al calendari .ics]
   📎 Esborrany de memòria adjunt (esquelet, 2 pàgines — el completa secretaria).

🟡 GROGUES (mirar si hi ha temps)
   · DARP/Leader — Diversificació econòmica zones rurals · fins 100.000 € · termini 15/09
     Dubte: el projecte de guia QR podria encaixar-hi, però exigeix inversió ≥ X €. [enllaç]
   · Cultura — Digitalització de patrimoni documental · termini 05/09 · Dubte: cal conveni
     amb arxiu comarcal? [enllaç]

⚪ DESCARTADES AVUI (3) — un motiu per línia, revisable en 2 minuts
   · MITECO — Flotes de transport urbà → beneficiari: municipis >20.000 hab.
   · Diba — Fons escoles bressol municipals → la Pobla no en té de titularitat pròpia.
   · Cultura — Festivals de música >3 edicions → no hi ha projecte en cartera que hi encaixi.
```

**Regles del correu (funcionals, dins del marc C3/C4):**
1. **Cadència:** correu **només quan hi ha verdes o grogues**; els **divendres**, resum setmanal sempre (encara que sigui «res de nou aquesta setmana — 14 vistes, 14 descartades»). El silenci regular també construeix confiança: demostra que el radar treballa.
2. Cada verda porta: import, cofinançament, **dies de marge**, el *per què* en una frase que cita el perfil, el següent pas administratiu i l'enllaç oficial. Mai el text de les bases al cos.
3. L'esborrany de memòria (R6) és **adjunt i sota demanda o per a verdes**, mai un enviament a tercers (porta humana C3 §6).
4. Les descartades **sempre** hi són amb el seu motiu d'una línia (mandat C4: auditables una a una).
5. Llengua del correu: català. La convocatòria s'enllaça en la llengua original (la BDNS és majoritàriament en castellà — el banc C4 ja ho reflecteix).

---

## 5. La memòria de cicle (el que la BDNS no sap)

Les convocatòries més importants per a un poble XS són **previsibles**: el Catàleg de la Diba obre la finestra gran al ~gener; el Leader surt cada estiu-tardor; el PUOSC és quinquennal (proper cicle: ~2029-2030). La BDNS només veu el present; el radar pot recordar el futur amb un fitxer petit:

`config/calendari-finestres.yaml` (comarcal, un per a tothom): llista de finestres històriques `{finançador, línia, mes_habitual, nota}`. El correu del divendres inclou, quan toca: *«📅 Anticipació: el Catàleg Diba 2027 sol obrir al gener — si voleu demanar per a la guia QR, la memòria s'hauria de començar al desembre.»*

**Estat:** proposta **post-v1 o R4.5** — barata (cap IA, cap font nova, un YAML i 10 línies al compositor del correu), però és abast: que Talaia decideixi si entra a v1 o s'encua. La documento perquè és el tipus de valor que un secretari reconeix a l'instant.

---

## 6. Annex A — Esborrany del criteri operatiu d'elegibilitat (per al banc C4)

> **⚠️ SUPERAT (#251):** Talaia ja ha fixat el full d'etiquetatge real a `docs/ajuntaments/banc-c4-etiquetatge.md`, amb el criteri operatiu i matisos millors apresos de dades reals (p. ex. «AJUNTAMENT DE X com a convocant ≠ ajuntaments com a beneficiaris»; frontera = dubtar >30 segons). Es conserva aquest annex només com a traça; **mana el full de Talaia**. La «regla d'or» del final (dubte → frontera) hi queda recollida.

*(C4 §2 mana: «Bea rep una pàgina amb la definició operativa d'elegible i etiqueta CONTRA el criteri». Aquest és l'esborrany d'aquesta pàgina — el fixa Talaia.)*

Una convocatòria és **ELEGIBLE** per al perfil de la Pobla si, i només si, **totes quatre**:

1. **Beneficiari:** els ajuntaments (o «ens locals», «entitats locals», «municipis») hi poden concórrer directament. *Nominatives o concessió directa a tercer concret: NO. Línies només per a entitats/empreses: NO (anotables com a «per al teixit local», fora del banc v1).*
2. **Territori:** l'àmbit inclou la Pobla (estatal, Catalunya, província de Barcelona, Berguedà o el municipi). *Restriccions per població («municipis de més de X hab.») s'apliquen amb el padró citat al perfil (1.106, 2025).*
3. **Matèria:** encaixa amb ≥1 matèria del perfil **o** amb ≥1 projecte en cartera. *En cas de dubte raonable entre matèries: és cas frontera, no descartable.*
4. **Termini:** obert en la **data de referència del banc** (congelada amb el banc), o obertura futura certa i datada.

**Semàfor esperat de les elegibles:** `verd` si el lligam amb matèria de pes ≥0,7 o amb un projecte en cartera és directe; `groc` si l'encaix demana interpretació (matèria de pes <0,7, requisits d'inversió mínima, consorcis/convenis previs).

**Regla d'or de l'etiquetadora:** en dubte entre descartable i frontera → **frontera**. El pecat greu del sistema és el FN (C4 §1); el del banc seria ensenyar-li que dubtar és descartar.

---

## 7. Casos límit funcionals (perquè ningú els descobreixi en producció)

| Cas | Tractament v1 |
|---|---|
| **PUOSC i convocatòries úniques plurianuals ja passades** | `estat: tancada` — mai al correu com a oportunitat; sí a la memòria de cicle (§5) |
| **Bases reguladores publicades sense convocatòria** | No són sol·licitables: no generen verda. Anotable com a anticipació (§5) si la línia encaixa fort |
| **Convocatòries obertes tot l'any / fins a exhauriment** | Verda amb marge = «obert (exhauriment)»; recordatori mensual al resum de divendres mentre segueixi oberta |
| **Concessions nominatives / directes** (la BDNS en publica moltes) | Fora — el filtre dur les mata per tipus; mai al correu |
| **Ajuts per a entitats, comerços o particulars del poble** | Fora del correu de l'ajuntament (v1, no-objectiu vinculant), però el filtre les VEU: queden anotades per al futur «radar del teixit local» (i per a la sessió 2 del pilot formatiu) |
| **Convocatòria vista només a CIDO amb id BDNS citat** | C3 §2 mana: clau `bdns:`, una fitxa, dues procedències |
| **El radar no tramita mai res** | C3 §6, innegociable — i és el que es diu a l'Ajuntament amb aquestes paraules: *«el radar avisa; les persones decideixen i signen»* |

---

## 8. Mètriques d'utilitat per a l'ajuntament (a sobre del recall de C4)

C4 posseeix el número de la demo (recall del pipeline). Per a l'*ajuntament*, la utilitat es mesura amb:

1. **Dies de marge mitjà** en el moment de l'avís de cada verda (objectiu: ≥ 30 dies naturals).
2. **€ elegibles detectats/mes** (suma d'imports de verdes) — el número que entén un ple.
3. **Convocatòries sol·licitades** gràcies a un avís del radar (l'omple Bea/secretaria a mà; és LA mètrica del pilot).
4. **Temps de lectura** del correu (la regla dels 90 segons, verificable amb el disseny, no amb cronòmetre).

---

## 9. Model d'accés — el radar és privat per disseny

**Decisió de producte proposada (Bea confirma):** el radar **no es publica mai en obert** al web de datapoble. No només per model de negoci: els `projectes_en_cartera` d'un perfil són **estratègia municipal** — publicar les verdes d'un municipi revela què vol demanar i on vol invertir. El flux del radar té destinatari, no audiència.

| Capa | Què | Accés |
|---|---|---|
| **Flux viu** (verdes, grogues, esborranys, anticipacions) | El producte | **Privat**: correu als `destinataris` del perfil (v1 — ja és accés específic, zero infra); si mai cal interfície, API amb token per municipi (el web estàtic NO protegeix res — lliçó E1) o canal Telegram per ajuntament |
| **Agregats no accionables** («aquest mes: 214 convocatòries vistes, N encaixos al Berguedà», € detectats/any) | Màrqueting i transparència del servei | Públic, amb retard |
| **Arxiu de convocatòries tancades** | Valor documental per a l'observatori | Públic — reforça datapoble sense regalar el flux |

**Replicabilitat** (Castellar, Guardiola, la resta): el pipeline és 100% comú; l'específic és el perfil — matèries+pesos, projectes en cartera (la conversa de 2-3 h amb cada ajuntament, que és el servei), llindars econòmics i destinataris. **Candidats a camps de perfil v2** apresos del cas XS extrem (Castellar, ~160 hab.): `inversio_minima_max` i capacitat de **bestreta** (línies que paguen per justificació queden fora de l'abast real d'un micropressupost encara que siguin «elegibles»). Canals de desplegament, no excloents: quota per municipi · contracte amb el Consell Comarcal (31) · servei supramunicipal via Diba/SeTDIBA.

### 9.1 Privat però testejable — l'entorn de desenvolupament

**Principi: en dev, el radar no envia — escriu.** Requisits (per a R1–R4, no extres):

1. **Dry-run local, ordre única**: `--data <dia> --perfil <ine5> --sortida out/` → `correu.md` + log de descartades + parquet, en directori gitignorat. BDNS no demana clau: corre en qualsevol portàtil. Sense `OPENROUTER_API_KEY` → filtre dur + semàfor stub (offline-first, patró Brúixola); amb `.env` local → semàfor real.
2. **Fixtures rejugables**: cada run arxiva les respostes crues BDNS/CIDO (el banc C4 les necessita igualment) → «rejuga'm el dijous passat» determinista i offline. Iterar el perfil = rejugar i comparar.
3. **Snapshot test del correu**: compositor + fixture congelada → correu *golden* versionat; el format s'itera llegint el diff (patró `test_parafrasis.py`).
4. **Correu real només via `workflow_dispatch`** amb assumpte `[DEV]` i destinatari Bea (secret SMTP del daily-report).

### 9.2 «L'espai del radar» — requisit de Bea (accés web privat amb accions)

Bea vol poder **veure, refrescar i enviar-se** el radar des del navegador. Dues fases:

1. **Fase dev (amb R4):** repo **privat** de sortides (`datapoble-radar-out` o equivalent) on el workflow escriu el `correu-<data>.md` de cada dia → GitHub el renderitza; historial per dies; «refresca ara» = botó *Run workflow*. És el «magatzem privat del workflow» d'E1 fet lloc visitable. Zero infra nova.
2. **Fase pilot (amb X2):** ruta **`/radar`** al servei de Render (el mateix que servirà el xat), protegida per **token per municipi**: últim correu + selector de dies + botó «Refresca ara» (dispara pipeline, amb límit de freqüència) + botó «Envia-m'ho» que envia **només als destinataris del perfil** (mai a adreça lliure — anti-relay). **Aquesta pàgina és el germen de l'accés de client del §9**: Bea l'estrena com a entorn de test i esdevé el producte per a municipis. El *com* exacte (Render vs Worker+Access) és jurisdicció de Trazo/Talaia.

**Dos forats detectats, per fixar a C3 abans de R1 (jurisdicció de Talaia):**
- **Artifacts d'Actions en repo públic són públics de facto** (qualsevol usuari GitHub loguejat els baixa): el correu del radar **mai** com a artifact — fitxer local en dev, SMTP en real. És E1 aplicat als artifacts.
- **El perfil YAML és al repo públic**: els **correus de `destinataris` no hi poden viure** (resolució via secret del workflow, p. ex. `destinataris: [BEA]` → mapa al secret); els `projectes_en_cartera` del pilot de la Pobla són públics i coneguts (acceptable), però el disseny ha de preveure l'**overlay privat** del perfil per a municipis clients (patró E1: magatzem privat del workflow).

---

## 10. Què NO farà mai el radar (el paràgraf per a en Jordi i l'alcalde)

> El radar llegeix cada matí els butlletins i registres oficials de subvencions i, quan surt una convocatòria que encaixa amb la Pobla, envia un correu de mig full amb el termini, l'import i el perquè. **No presenta sol·licituds, no signa res, no parla amb cap administració i no decideix res**: proposa, i les persones disposen. Tot el que descarta queda apuntat amb el motiu, perquè es pugui revisar en dos minuts que no se'ns escapa res. I abans de refiar-nos-en, l'haurem tingut **un mes funcionant en paral·lel** al mètode de sempre, comptant quantes en troba i quantes se li escapen — el número es dirà tal com surti.
