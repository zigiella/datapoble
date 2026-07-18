# C3 · Fitxa de subvenció normalitzada + perfil municipal — contracte de disseny

**De:** Talaia (owner) · **Implementen:** Sondeig (R1/R2/R5) · **Data:** 2026-07-16
**Font de veritat:** `docs/spec-ajuntaments-v1.md` §3-C3, amb les esmenes del §10 (E5) manant sobre el §3.
**Ordre:** aquest contracte es fusiona **abans** de cap línia de connector (R1 BDNS, R2 filtre, R5 CIDO). El dedupe i l'activació no són detalls d'implementació: són el que impedeix que «dues fonts» es converteixi en «dues alertes» i que un perfil dorment es converteixi en una sortida no autoritzada.

> La fitxa de subvenció és un **senyal germà** de la taula `events` de `packages/signals` (vegeu `schema.py`, `events.py`, `provenance.py`): mateixa disciplina — traçabilitat sempre, vocabularis tancats, cap número inventat, sidecar de procedència per càrrega — però **taula pròpia**. No s'encaixona a `EVENT_COLUMNS`: una convocatòria té `estat` que muta i pot acumular N procedències; un event és immutable.

## 1. La fitxa normalitzada (el contracte de la fila)

Tota font (BDNS, CIDO, les que vinguin) normalitza a **exactament** aquests camps:

| camp | tipus | regla |
|---|---|---|
| `id_bdns` | str \| NULL | codi BDNS quan la font el dona; mai inventat |
| `fonts` | llista, ≥1 | cada procedència = `{font_clau, font_url, data_vista}`; `font_url` **MAI NULL** (disciplina heretada d'events) |
| `organisme` | str | convocant, tal com el publica la font |
| `objecte` | str | títol/objecte de la convocatòria |
| `beneficiaris` | str | tipus de beneficiari segons la font |
| `ambit_territorial` | str | àmbit declarat (estatal/CAT/província/comarca/municipi) |
| `import` | float \| NULL | € de la convocatòria; NULL si la font no el dona |
| `cofinancament` | float \| NULL | % a càrrec del beneficiari; NULL si no consta |
| `data_publicacio` | date | — |
| `termini` | date \| NULL | fi del termini de sol·licitud. **`NULL` vol dir «la font no en dona data estructurada», MAI «no hi ha termini»** (esmena de R1, §2 bis) |
| `termini_text` | text \| NULL | el termini **tal com el diu la font**, literal, quan no és una data (p. ex. «Finaliza el 15 de septiembre de 2026», «15 Dies Hàbils»). Es transcriu; **no es parseja** |
| `enllac` | str | URL canònica de la convocatòria |
| `estat` | enum | `oberta` \| `tancada` \| `anul·lada` (vocabulari tancat; derivat de font + termini) |

**Materialització:** `data/subvencions/subvencions_bergueda.parquet` via DuckDB amb casts explícits (mateix patró que `events.py`) + `_provenance.json` per càrrega (patró `write_provenance`). BDNS i CIDO s'alta al registre `SOURCES` de `datapoble_signals/config.py` amb organisme, URL i llicència, com contractació i sequera.

## 2 bis. El `termini` ambigu — esmena de R1 (Talaia, 2026-07-16)

**Mesurat en viu per Sondeig sobre 26 convocatòries reals de la BDNS:** només **8/26** porten data
estructurada (`fechaFinSolicitud`); **11/26** la porten **en prosa** (`textFin`: «Finaliza el 15 de
septiembre de 2026», «15 Dies Hàbils»…); la resta, res.

**Decisió (ratifica la negativa de Sondeig a escriure un parser):**
- `termini` (date) només s'omple des del camp **estructurat** de la font. **Cap parser de prosa.**
  Deduir una data d'un text lliure seria **inferència servida com a fet, al camp que decideix si s'hi
  és a temps** — el pitjor lloc possible per inventar.
- El text literal es transcriu a **`termini_text`** (nou). La UI i el correu poden mostrar-lo tal qual.
- **`termini: NULL` ≠ «no hi ha termini».** Vol dir «la font no en dona data». **R2 NO pot descartar
  per `termini` NULL** (seria un FN de sistema, C4 §1) i **R4 ha de marcar-les com a «termini per
  confirmar — mira l'enllaç»**: és una mirada humana, no un descart automàtic.
- `estat` (`oberta|tancada|anul·lada`) **no es deriva d'un `termini` NULL**: sense data, l'estat el
  mana la font o queda indeterminat; mai «tancada» per absència de dada.
- El dedupe no canvia: la clau normalitzada ja preveia el literal `sense-termini` per al NULL.

## 2. La clau d'identitat (dedupe interfonts) — decisió tancada

- **Si `id_bdns` existeix** (el porti BDNS o el citi CIDO): la clau és `bdns:<id_bdns>`.
- **Si no:** `h:<sha256[:16]>` sobre la cadena `organisme|objecte|termini` **normalitzada**: minúscules, sense accents, espais col·lapsats a un, `termini` en ISO-8601 (o el literal `sense-termini` si és NULL).
- **Una convocatòria vista a 2 fonts = 1 fitxa amb 2 entrades a `fonts`.** En conflicte de valors d'un camp, mana BDNS (font registral); CIDO complementa. Conflicte no resoluble → es conserva el valor BDNS i es registra el discrepant al log amb la seva font.
- **Dedupe conservador:** cap fusió per similitud tova (fuzzy) en v1. Si dues fonts sense id difereixen en la clau normalitzada, són 2 fitxes; millor un duplicat visible que una fusió silenciosa equivocada.

## 3. El perfil municipal — `config/municipis/<ine5>-<slug>.yaml`

| camp | tipus |
|---|---|
| `tipus_beneficiari` | str (v1: `ajuntament`) |
| `poblacio` | int + `poblacio_any` (padró citat) |
| `territori` | llista d'etiquetes d'àmbit que encaixen (municipi, comarca, província, CAT, estatal) |
| `materies` | llista `{nom, pes}` amb `pes` ∈ [0,1] |
| `projectes_en_cartera` | llista de str lliures |
| `cofinancament_max` | float (% màxim assumible) |
| `destinataris` | llista de CLAUS SIMBÒLIQUES (p. ex. `[BEA]`), MAI correus en clar — §6 bis |
| `actiu` | bool **obligatori** (cap default implícit) |

**Semàntica EXACTA d'`actiu`:** la ingesta (R1/R5) i el filtre+puntuació (R2) corren per a **tots** els perfils, actius o no; les **sortides** (correu R4 i qualsevol futura publicació) es generen **només** per als perfils `actiu: true`. **v1: actiu només `08166-lillet`; `08052-castellar` i `_default` preparats i dorments** (`actiu: false`).

**Validació al load (fail fast):** camp desconegut → error; `pes` fora de [0,1] → error; `actiu` absent → error. `_default` és plantilla copiable: **cap herència ni merge de perfils en v1**.

## 4. E5 · `config/` — la primera convenció declarativa del repo

`config/` és el **primer directori de perfils declaratius** del repo: fins avui tota configuració viu *hardcoded* en codi — el registre `SOURCES` de `datapoble_signals/config.py` n'és el precedent, i `BERGUEDA_INE5` viu duplicada als `municipis.py` d'ingestion i de signals.

Relació fixada: **els perfils NO substitueixen `BERGUEDA_INE5` en v1.** La llista dels 31 segueix sent l'única font del filtre territorial dels connectors; el perfil YAML només decideix *match i sortida* per municipi. Coherència obligatòria: l'`<ine5>` del nom de fitxer ha d'existir a `BERGUEDA_INE5` (test). **Deute anotat:** unificar municipis+perfils en una sola font canònica queda fora de v1 (s'apunta a la bitàcora, no es tapa aquí).

## 5. Test obligatori de la trampa de codis (tot connector: R1 i R5)

- Castellar de n'Hug = **08052** (INE/Idescat; el Cadastre diu 08051 — el test verifica que cap join usa 08051).
- la Pobla de Lillet = **08166** (Idescat 6 dígits: **081666** — el test verifica el tall `[:5]` i que 081666 mai apareix com a clau).
- Amb fixtures reals arxivades; CI verd offline, cap test depèn de xarxa.

## 6 bis. Seguretat de la sortida (esmena 2026-07-18, dels forats detectats al R-FUNC §9.1–9.2)

1. **Cap correu en clar al repo públic.** El camp `destinataris` del perfil porta claus simbòliques;
   el mapa clau→adreça viu NOMÉS als secrets del workflow (p. ex. `RADAR_DEST_BEA`). Validació del
   load: una `@` a `destinataris` → error.
2. **El correu del radar MAI com a artifact d'Actions**: en un repo públic, els artifacts són
   públics de facto (qualsevol usuari loguejat els baixa). En dev el correu s'escriu a fitxer local
   gitignorat; en real s'envia per SMTP des del workflow. És E1 aplicat als artifacts.
3. **El flux del radar és PRIVAT per disseny** (decisió de Bea, R-FUNC §9): mai al web públic — els
   `projectes_en_cartera` són estratègia municipal. Públics només: agregats no accionables amb
   retard, i l'arxiu de convocatòries tancades. El disseny preveu l'overlay privat del perfil (v2).
4. **Anti-relay** (per a la futura ruta /radar): el botó «envia-m'ho» només envia als `destinataris`
   del perfil, mai a una adreça lliure.

## 6. La porta humana (§1.1 de l'spec) — innegociable

El radar **proposa**: la seva única sortida és el correu als `destinataris` del perfil actiu (v1: Bea). **Mai** presenta, sol·licita, envia ni emplena res a cap administració — ni BDNS, ni CIDO, ni cap seu electrònica. Cap sortida per a perfils `actiu: false`; cap `radar-bergueda.json` públic ni perfil nou actiu abans de la porta del §4 de l'spec (banc C4 + mes de validació + vistiplau de Bea).

## 7. Què és dins / què és fora

- **Dins:** fitxa i vocabularis, clau d'identitat i dedupe, esquema i validació del perfil, semàntica d'`actiu`, convenció `config/`, tests de la trampa.
- **Fora:** el banc d'avaluació (contracte C4, germà), el classificador (R3), el workflow i el correu (R4), qualsevol publicació web, herència de perfils, perfils fora del Berguedà.

## 8. Criteris de verificació (el llistó d'aquest contracte)

1. Fixture amb la mateixa convocatòria a BDNS i CIDO → **1 fitxa, 2 procedències**, clau `bdns:` si alguna font porta l'id.
2. Fixture sense id i camps normalitzats iguals → 1 fitxa; amb un caràcter de diferència real a `organisme|objecte|termini` → 2 fitxes.
3. Cap fila al parquet amb `fonts` buit o `font_url` NULL.
4. Perfil amb camp desconegut, `pes`=1.2 o sense `actiu` → el load falla amb missatge llegible.
5. Amb `08052-castellar` a `actiu: false`: el log de R2 mostra el seu match, i **cap sortida** el conté.
6. Tests de la trampa de codis (§5) verds a R1 i R5.
