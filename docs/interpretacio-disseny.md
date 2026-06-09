# Disseny — Capa d'interpretació (ensemble adversarial, pre-computat)

*#65 · riusdegent. Document de **disseny** per muntar i depurar a mà (Bea) i implementar després (Talaia). Objectiu: convertir les dades fredes en una **lectura honesta en prosa** del territori, generada offline per un ensemble de models frontier, cached i transparent.*

**Estat:** disseny v0 (per iterar). No és codi encara.

---

## 0. Principi

El model **interpreta FETS, no inventa**. Tot el que pot dir ha de sortir d'un **full de fets** curat (valors + unitats + confiança + caveats). Un sol model al·lucina i sobre-llegeix; per això un **escriu** i un altre (de proveïdor diferent) **refuta**, i la **síntesi** només conserva el que sobreviu. És la honestedat del projecte aplicada a la prosa.

**Innegociable (va a TOTS els prompts):**
1. Fes servir **NOMÉS** els fets del full. Mai inventis xifres, causes ni comparacions que no hi siguin.
2. Respecta **CONFIANÇA i CAVEATS**. Inferència ≠ cens. Confiança baixa → modula («sembla», «podria»). Mai presentis una inferència com a fet dur.
3. Lectura **ECOLÒGICA**: parla del municipi/comarca, **mai d'individus**. Cap afirmació causal sobre per què la gent fa coses.
4. To d'**analista local pensatiu**: honest, planer, ni alarmista ni propagandístic. Ni fullet turístic ni catàstrofe.
5. Concís. Català primer, després castellà (traducció fidel, no re-escriptura).

> **`origen` queda FORA de la v1** (coherent amb el guard de la IA: la dimensió origen és pública al web però retinguda de la IA fins al *frontier*). La interpretació d'origen es farà a part, amb guardes de nivell *frontier*.

---

## 1. Les dades — el «full de fets» (digest)

Es construeix des del contracte + marts (`mart_municipi`, `mart_demografia` sense origen, agregats comarcals). **Format etiquetat, una línia per fet citable**, amb el tipus (mesura/inferència) i la confiança marcats. NO és un volcat SQL.

### 1a. Full de fets · MUNICIPI (exemple real, Castellar de n'Hug)
```
MUNICIPI: Castellar de n'Hug · comarca Berguedà · INE 08052
Població (padró 2025): 166 hab
TIPOLOGIA: «excursió» — turisme i activitat de dia alts, hi pernocten poc
  · CONFIANÇA: BAIXA (score 32,8/100) ⚠ senyals divergents (vegeu caveats)
CAPA 1 · pernocta (qui DORM aquí; via elèctric domèstic): gap +31% sobre el padró [INFERÈNCIA · rang]
CAPA 2 · càrrega total (inclou excursionistes de dia; via residus): molt per sobre del padró [INFERÈNCIA]
CAPA 3 · pressió turística (via vidre; 0–100, RELATIU a la comarca): 83,5 (mitjana comarcal = 50) [INFERÈNCIA]
IETR (exposició turística-residencial): 89,4 · #1 de 31 · desglossat stock 100 / impact 79
SENYALS FÍSICS: residus alt, elèctric/hab baix, vidre/hab alt, restauració 3 locals (OSM = mínim)
SERVEIS (centralitat): 4 establiments comerç+serveis (OSM = mínim) — NO és capçalera de serveis
CAVEAT CLAU: a Castellar els residus diuen «molta gent» però l'elèctric diu «poca» → calefacció de llenya
  trenca el senyal elèctric. Els senyals DIVERGEIXEN: per això la confiança és baixa. Les 3 capes són
  inferència (no cens), es llegeixen com a RANG.
CONTEXT COMARCAL: població mediana ~430 hab; el Berguedà és rural i envellit, amb un extrem turístic
  (Castellar, Gósol, Saldes) i una capital de serveis (Berga, 17.539).
```

### 1b. Full de fets · COMARCA (Berguedà)
```
COMARCA: Berguedà · 31 municipis · població total ~38.700 hab
DISTRIBUCIÓ DE TIPOLOGIES: capital de serveis 5 (Berga, Gironella, Puig-reig, Avià, Bagà) ·
  turisme de pernocta 5 · turisme d'excursió 2 · dormitori invisible 1 · buit administratiu 2 ·
  indeterminat 16 (la meitat: territori mixt, dit honestament)
EXTREMS: + turístic Gósol/Castellar (IETR ~89–100) · capçalera Berga · més buits els micromunicipis del nord
PRESSIÓ: X munis amb gap de pernocta alt (segona residència) · Y amb càrrega de dia alta (excursió)
SENYAL HONEST («un no»): turisme × sequera NO convergeixen al Berguedà (la geografia ho inverteix)
CAVEATS: tot inferència sobre senyals físics; z-scores comarcals (no comparables entre comarques);
  micromunicipis amb confiança baixa.
```

**Decisió de disseny (per a tu):** quins fets entren al full? Proposo els de dalt. Es pot afegir/treure. El digest el genera un builder en Python des del contracte (cap xifra a mà).

---

## 2. L'ensemble — rols, models i flux

Tres rols, **proveïdors diferents** per a diversitat real (és el que caça el que un sol model no veu):

| Rol | Model proposat | Què fa |
|---|---|---|
| **Escriptor (W)** | `anthropic/claude-3.5-sonnet` | full de fets → esborrany d'interpretació (ca) |
| **Refutador (C)** | `openai/gpt-4o` | full + esborrany → llista de PROBLEMES (no-suportat, sobre-lectura, caveat ignorat, no-ecològic, sensacionalista) amb severitat |
| **Refutador 2 (C2)** *(opcional, barat)* | `google/gemini-flash-1.5` | segona mirada independent sobre l'esborrany |
| **Sintetitzador (S)** | `anthropic/claude-3.5-sonnet` | full + esborrany + problemes → interpretació FINAL (ca + es), corregint tot el marcat |

**Flux:** `W → C (+ C2) → S`. El **full de fets es passa a TOTS** (cadascú s'ancora pel seu compte; el refutador no es fia de l'esborrany, comprova contra els fets).

**Per què aquest repartiment:** l'escriptor raona i escriu; un refutador d'**un altre proveïdor** caça els biaixos que l'escriptor no es veu (la diversitat creuada és la palanca anti-al·lucinació); el sintetitzador tanca net respectant la crítica. *(Alternativa a debatre: writer=gpt-4o / critic=claude. O un 3r model de síntesi.)*

---

## 3. Els prompts (el cor — per depurar a mà)

### 3.0 SISTEMA (capçalera comuna a W, C i S)
```
Ets un analista de riusdegent, un observatori cívic de dades territorials que es pren la
HONESTEDAT abans que la xifra bonica. Interpretes un FULL DE FETS d'un territori (comarca o
municipi). Regles innegociables:
1) Fes servir NOMÉS els fets del full. Mai inventis xifres, causes ni comparacions que no hi
   siguin. Si una dada no hi és, no la diguis.
2) Respecta CONFIANÇA i CAVEATS. Inferència ≠ cens. Si la confiança és baixa o un senyal
   divergeix, modula el llenguatge («sembla», «apunta a», «podria»). Mai presentis una
   inferència com a fet dur.
3) Lectura ECOLÒGICA: parla del territori, MAI d'individus ni de col·lectius concrets. Cap
   afirmació causal sobre per què la gent fa coses.
4) To d'analista local pensatiu: honest, planer, concret. Ni alarmista ni propagandístic.
5) Català clar. Frases curtes. Res de pal·la de fusta ni de fullet.
```

### 3.1 ESCRIPTOR (W)
```
[SISTEMA]

FULL DE FETS:
<<< {fact_sheet} >>>

Escriu una interpretació de {N_PARAULES} paraules d'aquest territori: quina mena de lloc és i
com s'habita; quina tensió o quina història expliquen les dades. Comença per allò més
distintiu (la tipologia o el senyal més marcat). Teixeix-hi la lectura de les 3 capes (qui
DORM aquí vs qui l'omple de DIA) i l'IETR si és notable. Sempre RELATIU a la comarca. Marca el
que és inferència. No facis llistes: prosa.
```

### 3.2 REFUTADOR (C / C2)
```
[SISTEMA]

FULL DE FETS:
<<< {fact_sheet} >>>

ESBORRANY A AUDITAR:
<<< {draft} >>>

La teva feina és trobar TOTS els problemes de l'esborrany. Per a cada frase o afirmació que
(a) NO estigui suportada pel full de fets, (b) presenti una inferència com a fet dur, (c)
ignori un caveat o una confiança baixa, (d) faci una afirmació causal / individual / no
ecològica, o (e) sigui sensacionalista o propagandística: cita-la i explica el problema i la
severitat (ALTA/MITJANA/BAIXA). Si l'esborrany és net, digues-ho. Sigues ESTRICTE: davant del
dubte, marca-ho. Respon com a llista de problemes, res més.
```

### 3.3 SINTETITZADOR (S)
```
[SISTEMA]

FULL DE FETS:
<<< {fact_sheet} >>>

ESBORRANY:
<<< {draft} >>>

PROBLEMES DETECTATS:
<<< {critique} >>>

Produeix la interpretació FINAL: corregeix o elimina CADA problema marcat, conserva el que és
sòlid. Mateixa llargada ({N_PARAULES} paraules), mateix to i mateixes regles. Retorna PRIMER
la versió en CATALÀ i, després d'una línia `---`, la versió en CASTELLÀ (traducció fidel, no
una re-escriptura). No afegeixis res més.
```

**Paràmetres a afinar (tu):** `N_PARAULES` (proposo 150 muni / 220 comarca), temperatura (proposo 0,4 W i S, 0,2 C), i si C2 entra sempre o només si C marca severitat alta.

---

## 4. Sortida + transparència (= #64)

Un JSON cached per territori (`data/web/interpretacions.json`, indexat per `ine5` i `comarca`):
```json
{
  "08052": {
    "interpretacio": { "ca": "…", "es": "…" },
    "generat": {
      "writer": "anthropic/claude-3.5-sonnet",
      "critics": ["openai/gpt-4o", "google/gemini-flash-1.5"],
      "synthesizer": "anthropic/claude-3.5-sonnet",
      "tokens": { "prompt": 5400, "completion": 900, "total": 6300 },
      "cost_usd": 0.07,
      "data_fingerprint": "sha256(full_de_fets)[:12]",
      "generat_el": "2026-06-..."
    }
  }
}
```
El web mostra **sempre** sota la interpretació: «Interpretació generada per claude-3.5-sonnet (escriptor), revisada per gpt-4o + gemini-flash · 6.300 tokens». Això satisfà el #64 (transparència: model + tokens sempre visibles).

---

## 5. Orquestració (el que implementaré jo)

Script `packages/ai/.../interpret.py` (offline; clau d'`packages/ai/.env`):
- Construeix els fulls de fets des dels marts + contracte.
- Per cada territori: `W → C (+C2) → S`, acumula tokens i cost (reusa `pricing.py` + `costcontrol.py`).
- **Cache idempotent:** si el `data_fingerprint` no ha canviat, no re-genera (`--force` per forçar). Així re-córrer és gratis quan les dades no canvien.
- **Tall de pressupost dur:** s'atura si el cost acumulat supera un cap (p. ex. `--max-usd 0.50` per a la prova).
- Escriu el JSON; el web hi té un loader (Mirador) que el mostra a la comarca i a la fitxa de municipi.

---

## 6. Abast i cost

- **v1 — comarca (Berguedà):** 1 territori. ~**$0,10**. Valida el TO i les guardes abans de gastar més.
- **v2 — 31 municipis:** ~**$2–4** (segons models i llargada). Idempotent → re-córrer és gratis.
- **`origen`:** a part, més endavant, amb guardes de nivell *frontier*.

---

## 7. Qüestions de disseny (on vull el teu criteri)

1. **Models de l'ensemble.** ¿claude-sonnet (W) + gpt-4o (C) + gemini-flash (C2) + claude (S)? ¿O un altre repartiment / models més barats per a la v1?
2. **Llargada i to.** 150/220 paraules, ¿prou? ¿Vols un to més sec o més narratiu?
3. **Què entra al full de fets.** ¿Els fets de §1 són els justos? ¿Hi afegiries política (extrema dreta × edat) o ho deixes fora de la lectura automàtica?
4. **Auditoria.** ¿Vols desar també l'esborrany + la crítica al JSON (per auditar el procés), o només la sortida final?
5. **`origen` a la interpretació.** Confirmes que queda fora de la v1 (es fa amb el *frontier*)?
6. **On es mostra.** Comarca a `/resum`? Municipi a la fitxa `/municipi/[ine5]`? Totes dues?

---

*Quan ho hagis muntat, depurat i em tornis el doc + una API KEY, ho depuro contra dades reals, l'implemento (builder de fulls + script d'ensemble + cache + loader web + transparència) i ho tanco amb un PR.*
