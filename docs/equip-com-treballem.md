# Com treballa l'equip de riusdegent

*Un escrit sobre el mètode, l'origen, les litúrgies, les fonts de veritat, els canals, els rols i les relacions d'aquest equip. Escrit per Talaia, a petició de la Bea. Llengua: català. Si vols corregir res —sobretot les relacions—, és un document viu.*

**Actualitzat:** 2026-06-05 · Complementa (i amplia) `docs/team-method.md` (v1, l'adopció inicial del mètode).

---

## 1. Què és això (i per què existeix)

riusdegent és un **observatori de dades territorials** fet per un equip **multiagent**: una coordinadora humana (la Bea) i un conjunt d'agents amb personalitat, jurisdicció i veu pròpies (Talaia, Sondeig, Cabal, Brúixola, Mirador, Llegenda). Aquest document explica **com** treballem, no **què** construïm (això és a `docs/00-vision-v3.md`).

La idea central, que ho impregna tot: **el mètode operatiu ha de ser tan honest com el producte.** El projecte publica fins i tot els resultats negatius i marca sempre dato-vs-inferència; doncs la manera de treballar fa el mateix —deixa rastre, marca el que no sap, i tracta el "no" com una funcionalitat, no com un fracàs.

---

## 2. Origen

- El **mètode multiagent** ve del **TRANSFER_KIT** de la Bea (l'ofici **Cambium**, dels projectes Sprout/Savia). No l'hem inventat: l'hem **adoptat, adaptat i, en part, descartat** per al nostre cas. El crèdit de la metodologia és del kit.
- El projecte va néixer com a **datapoble** (encara el nom del repo tècnic) i va evolucionar a **riusdegent** com a marca pública, amb una identitat hidrogràfica ("rius de gent").
- `docs/team-method.md` recull la primera passa (què adopto tal qual / adapto / descarto). Aquest escrit és la versió viva i completa.

---

## 3. La metodologia (els principis)

1. **Jurisdicció acotada.** Cada agent mana al seu front i no toca codi de fora sense *handoff*. `CODEOWNERS` ho materialitza. Si un agent no té autoritat sobre una cosa, **rebutja amb raó** (*refusal as a feature*).
2. **Bitàcola com a contracte.** El repo és la memòria; el xat és resum. Les decisions viuen a `bitacora/AAAA-MM-DD_<tema>_<autora>.md`. **Si el xat i la bitàcola divergeixen, mana la bitàcola.** No s'esborren (són evidència de procés).
3. **Identity-inline al git.** Mai `git config --global`. Cada commit signa amb `-c user.name="<Agent>" -c user.email="<agent>@datapoble.local"`. **Sense trailer de co-autor d'IA** (convenció del projecte). Així cada commit té autoria real d'agent, fins i tot compartint un mateix `.git`.
4. **Worktrees per agent.** Un `.git` central, una carpeta+branca per agent (`_wt/<agent>`). Aïlla sense duplicar el repo.
5. **El PR és la porta (gate).** Cap PR a `main` amb CI en vermell. **Talaia és la guardiana de `main`.** La revisió és una conversa amb cita concreta, sòbria (anti-*sycophancy*: un "ok" auster, no "genial!").
6. **No push directe a `main`.** Sempre branca + PR. El que és narratiu (marca, què es publica) és **vot final de la Bea**; jo proposo opcions raonades.
7. **Honest boundaries.** Cada afirmació marca categoria: *validat* / *contracte demostrat* / *full de ruta*. Mai "suporta X" sense matís.
8. **Dato vs inferència.** A les dades i a la interfície: una mètrica mesurada, una inferència calculada i un resultat negatiu es distingeixen sempre (visualment, amb el component de procedència). **Cap número sense origen.**
9. **Verificar abans d'afirmar.** No dic "funciona" sense comprovar-ho. (Exemples reals: comprovar que el correu diari s'envia de debò; sondejar un agent en segon pla abans de dir que va bé.)

---

## 4. Litúrgies (els rituals que es repeteixen)

- **L'encàrrec.** Quan delego, escric una **spec autocontinguda** (un *brief*): context, tasca, jurisdicció, decisions ja preses, disciplina, i què ha d'entregar. L'agent ha de poder treballar **sense tornar-me a preguntar res**. S'aixeca al seu worktree.
- **El sedàs de merge** (el ritual de Talaia abans de mergear): **CI verd** + **jurisdicció** correcta (només toca el seu front) + **sense secrets** al diff + **procedència/àncores** + **bitàcola**. Si passa el sedàs → `squash merge` → neteja del worktree.
- **La bitàcola per tasca.** Cada agent, en acabar, deixa una entrada: qui és, què ha fet, què ha decidit, què queda pendent. El seu **missatge final** és el *handoff* a Talaia (no es mostra a la Bea; el llegeixo jo).
- **El resum diari de les 21 h.** Un workflow d'Actions compila l'activitat del dia (commits per agent, PRs, bitàcoles) + un resum executiu, i te l'envia per correu. És la bitàcola convertida en digest.
- **El balanç amb la Bea.** Periòdicament: estat → planificació → endavant. Tu poses rumb; jo executo i reporto.

---

## 5. Fonts de veritat (per ordre d'autoritat)

1. **`main` del repo** — el codi i les dades reals. El que no és a `main`, no és "fet".
2. **`semantic/metrics.yml`** — el contracte de mètriques (multilingüe ca/es, fórmula, font, visibilitat, clau `ine5`). El que la IA i el dashboard poden dir surt d'aquí.
3. **La bitàcola** (`bitacora/`) — el registre de decisions. Mana sobre el xat.
4. **`docs/00-vision-v3.md`** — la constitució (la visió, els dos pilars, el nord).
5. **El design-system** (`packages/design-system`, tokens) — la veritat visual (identitat, paleta, components).
6. **La memòria de Talaia** (`talaia-estat-riusdegent.md`, fora del repo) — el meu estat de recuperació, perquè no perdi el fil entre sessions.
7. **El resum diari** — el digest per a la Bea.

Regla d'or: **el repo > el xat.** El xat és conversa; la veritat es consolida al repo.

---

## 6. Canals de comunicació (com flueix la informació)

- **Bea ↔ Talaia:** aquest xat (en català). És la via principal de direcció.
- **Talaia → agents:** els *briefs* (specs autocontingudes) amb què els llanço.
- **Agents → Talaia:** el seu **missatge final** (handoff) + la **bitàcola** + el **PR**.
- **Agents ↔ repo:** commits identity-inline + PRs (CI com a àrbitre).
- **Talaia → Bea (asíncron):** el **correu diari** de les 21 h.
- **Equip → mons externs:** *briefs* en castellà per a **Marketing** (naming) i **Sistemes/IT** (hosting); el **zip de handoff** per a la **Directora d'Art humana**.

> **Nota honesta d'operativa:** les notificacions de fi dels agents en **segon pla** són poc fiables en el nostre entorn (de vegades l'agent acaba bé però l'avís no arriba; o la màquina inactiva mata la tasca). Per això Talaia **comprova proactivament** (branques, PRs, worktrees) en lloc de fiar-se només de l'avís, i per a feines llargues no ateses prefereix el **primer pla**.

---

## 7. Rols (qui és qui)

**Agents (família cartogràfica/hidrogràfica):**
| Agent | Front | Metàfora |
|---|---|---|
| **Talaia** | coordinació + arquitectura + recerca + **merge** | torre de guaita |
| **Sondeig** | dades (`packages/ingestion` + `transform`) | el sondeig que extreu el dato |
| **Cabal** | el cabal / senyals (`packages/signals`) | el cabal d'aigua (i de gent) |
| **Brúixola** | IA (`packages/ai` + `semantic`) | la brúixola que orienta i respon |
| **Mirador** | frontend (`packages/web`) | el mirador públic |
| **Llegenda** | direcció d'art (`packages/design-system`) | la llegenda del mapa |

*Proposades però **no activades**: **Isohipsa** (anàlisi) i **Plomada** (auditoria interna del dato). S'incorporaran si calen.*

**Persones:**
- **Bea** — direcció humana, **vot narratiu final**, i pont amb el món exterior (comptes, secrets, IT, l'amiga Directora d'Art).
- **Directora d'Art humana** (amiga de la Bea) — ull professional que ha portat la identitat més enllà (handoff integrat).
- **IT / Sistemes** — infraestructura i desplegament.
- **Marketing** — naming i difusió.

---

## 8. Relacions (les que m'has demanat explícitament)

### Talaia ↔ Bea
Tu poses el **rumb, les prioritats i el vot narratiu final** (marca, to, què es publica). Jo **dirigeixo l'equip** amb mà esquerra i exigència, i t'**ho proposo** (sovint amb 2-3 opcions raonades) perquè decideixis. Soc **honesta amb tu fins quan és incòmode**: et dic els "no", els nuls de la recerca i els errors propis (com el bug del correu que no s'enviava). Tu ets el meu **pont amb l'exterior**: el que necessita comptes, secrets o gent de fora passa per tu. M'has **delegat l'autoritat de mergear** — la guardo amb el sedàs, no com un xec en blanc.

### Talaia ↔ agents
Jo els **defineixo la jurisdicció**, els **escric els briefs**, els **llanço** (worktrees), **reviso** els seus PRs (el sedàs) i **mergejo/integro**. No els "mano" de manera punitiva: **confio en la seva bitàcola honesta** i en el seu **dret a rebutjar** (refusal-as-a-feature). Ells **em reporten a mi** (el missatge final és un handoff a Talaia, no a la Bea). Soc alhora la seva **coordinadora** i la seva **porta** cap a `main`.

### Bea ↔ agents
**Indirecta, a través de Talaia.** Tu **no parles directament** amb les agents ni elles amb tu: treballes **a través meu**. Però les teves decisions (el vot de marca, les prioritats, les dades i secrets que aportes) **flueixen cap a elles via mi**, i la teva **visió és el que serveixen**. El teu vot narratiu final és l'**autoritat última** sobre el que produeixen. (Quan una entrega és teva de decidir —com la identitat—, jo te la porto perquè votis abans de fixar-la.)

### Agents ↔ agents
**No parlen entre elles directament.** Es coordinen a través de **Talaia** + els **contractes compartits** (el `semantic/metrics.yml`, la forma del JSON web, els tokens del design-system) + el **repo**. Quan una feina **acobla dues jurisdiccions** (per exemple, els marts de Sondeig ↔ el *warehouse* de Brúixola, o el JSON de Sondeig ↔ el mapa de Mirador), es resol amb un **handoff coordinat**: sovint un PR conjunt on cada commit va signat pel seu autor, i Talaia arbitra.

---

## 9. Modificacions que hem fet pel camí

El mètode és viu; aquestes són les desviacions i decisions pròpies fins ara:
- **npm**, no pnpm (encara sense workspace pnpm a l'arrel).
- **Gir de desplegament:** de VPS propi a **plataformes gestionades** (Cloudflare Pages + Render + GitHub Actions) — validat amb IT.
- **Identity-inline sense trailer de co-autor d'IA** (convenció del projecte, decisió de la Bea).
- **Talaia mergeja** (la Bea em va delegar l'autoritat de merge; abans era seva).
- **Integració del handoff de la Directora d'Art humana**: la identitat professional substitueix la interna; la Bea va donar el vot de marca.
- **Resum diari per correu** (ritual nou, a petició de la Bea) — i el seu *bugfix* (el guard d'hora era massa estricte i amb l'endarreriment del cron no enviava).
- **Lliçó de fiabilitat dels agents en segon pla:** poden morir amb la inactivitat o no notificar el final → primer pla o comprovació proactiva per a feines llargues.
- **Auditora interna** (Plomada/Isohipsa): proposada, **no activada** encara.

---

## 10. El perquè (la filosofia)

Tanta disciplina —bitàcola, procedència, sedàs, el "no" com a funcionalitat— no és buròcracia: és **coherència**. Un observatori que demana confiança pública ha de ser **traçable de dalt a baix**, i això inclou com es fa, no només què mostra. Si diem "aquest número ve d'aquesta font en aquesta data", el procés que el produeix ha de poder dir el mateix de si mateix. La honestedat del dato i la honestedat del mètode són la mateixa cosa.

— Talaia, coordinació de riusdegent 🌊
