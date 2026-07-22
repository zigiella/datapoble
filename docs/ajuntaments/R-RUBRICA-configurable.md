# El radar com a rúbrica única configurable
## Idea de Bea, desenvolupada — perfil per municipi + senyal de veïns + historial de guanyades

**De:** Marea, sobre una idea de Bea · **Data:** juliol 2026 · **Estat:** nota de disseny per discutir i, si convenç, encuar via Talaia. **No és un contracte**: proposa una extensió de C3/C4 que respecta el que ja hi ha.

---

## 0. L'evidència que ho engega (cas real la Pobla)

La pàgina de publicitat de subvencions de l'Ajuntament mostra què guanya la Pobla de debò:
transició ecològica, patrimoni arqueològic (la #62 del banc), **gestió forestal sostenible**
(2021, 2022, 2024), mitigació del canvi climàtic, **espais naturals**.

**Dues d'aquestes matèries — gestió forestal i espais naturals — NO eren al perfil proposat per
intuïció.** El perfil-per-opinió té punts cecs; l'historial de guanyades els omple sols. Aquesta és
la prova que la idea de Bea no és un extra: és la manera d'evitar el fals negatiu per matèria (el
pecat greu de C4) de forma sistemàtica, no anecdòtica.

---

## 1. Les tres peces (i com encaixen amb el que ja existeix)

La proposta té tres mecanismes que **no toquen el nucli** del radar (filtre dur + rúbrica), sinó que
**alimenten el perfil** i **modulen la prioritat**:

### A · Historial de guanyades com a *ground truth* (llavor del perfil)
- **Font màquina:** la BDNS no publica només convocatòries; publica **concessions** (`concesiones`)
  per beneficiari. L'API permet consultar les concessions d'un NIF/municipi → l'historial de què ha
  guanyat cada ajuntament, sense scraping. La pàgina de transparència municipal és la versió humana
  del mateix.
- **Ús:** de l'historial es deriva el **fingerprint de matèries real** del municipi (freqüència +
  imports per matèria). Això **sembra** els `materies`+`pes` del perfil YAML (C3), que després un
  humà ajusta. I cada convocatòria guanyada és un **exemple positiu** (com la #62 va ser ground truth
  al banc): material d'or per validar el radar sense inventar res.
- **Cost:** baix. Una passada per municipi contra l'API de concessions.

### B · Senyal de veïns / municipis semblants (col·laboratiu)
- **La idea de Bea:** «un municipi podria optar a les subvencions a què opta o guanya un municipi
  veí». És filtratge col·laboratiu.
- **La peça que ja hi és:** datapoble **ja té** el motor de semblança — la comparació entre els 31
  del Berguedà, la tipologia municipal, l'IETR, els percentils comarcals. Agrupar per «municipi de
  muntanya XS amb pressió turística» és gratis amb el que hi ha.
- **Ús:** una línia que un **peer** (Bagà, Guardiola de Berguedà, Castellar) ha guanyat és un senyal
  d'alta prioritat per a la Pobla, **encara que el seu historial propi no la tingui encara**. Puja el
  cas al capdamunt del correu amb el motiu «l'ha guanyat un municipi com el teu».
- **Guardaraïl honest (important):** el senyal de veí **modula la prioritat, no l'elegibilitat**. Que
  un veí la guanyi no et fa elegible (llindars de població, requisits...). El **filtre dur segueix
  manant**; el peer és una pista, mai un «inclou-la sí o sí».

### C · La rúbrica única configurable (el fons de la qüestió)
- **La idea de Bea:** «la clau és una rúbrica única configurable per fer després un radar
  configurable». Exacte — i és **la direcció que C3/C4 ja porten**.
- **La separació neta:**
  - **La rúbrica = doctrina invariant.** Les *dimensions* de l'elegibilitat són les mateixes per a
    tots els municipis: beneficiari (ens local hi cap?), àmbit territorial, encaix de matèria,
    temporalitat, **llindar de població**, i —candidats v2 apresos de Castellar— **inversió mínima** i
    **capacitat de bestreta**. Aquesta rúbrica és el que el **banc C4 mesura i congela**.
  - **El perfil = la configuració variable.** El YAML per municipi (C3) omple els *valors*: quina
    població, quines matèries+pesos (sembrades per A), quines etiquetes de territori, quins llindars.
  - **El radar = rúbrica(perfil, flux de convocatòries).** Una rúbrica + N perfils → N radars. És el
    principi «construir una vegada, desplegar per N» que l'spec ja té.
- Historial (A) i veïns (B) entren com a **entrades de la puntuació** (modulen semàfor i ordre), mai
  com a autoritat sobre el filtre dur. La doctrina de la rúbrica no canvia d'un municipi a l'altre;
  només canvia la config.

---

## 2. Com es veu, en concret

```
config/municipis/08166-lillet.yaml        # el perfil (variable)
  poblacio: 1106
  materies:            # SEMBRADES de l'historial de guanyades (A) + ajust humà
    - {nom: gestió forestal, pes: 0.8}     # ← l'historial l'hauria descobert; la intuïció no
    - {nom: espais naturals, pes: 0.7}     # ← idem
    - {nom: patrimoni, pes: 0.9}           # #62, guanyada 2025
    - {nom: transició ecològica, pes: 0.8}
    - ...
  peers: [08009-baga, 08093-guardiola, 08052-castellar]   # per al senyal (B)
  historial_guanyades: [CLT/745/2025, ...]                # exemples positius (A)

rubrica.yaml (o codi)   # la doctrina (invariant, la mateixa per a tots)
  dimensions: [beneficiari, territori, materia, temporalitat, poblacio, inversio_minima, bestreta]
  # el banc C4 mesura AIXÒ; es congela; no varia per municipi
```

El motor: `filtre_dur(convocatòria, perfil)` (determinista, mata el 90%) →
`rúbrica(convocatòria, perfil)` (semàfor) → **modulació** per historial (A) i veïns (B) → correu.

---

## 3. Què és v1, què és després (per no obrir abast)

| Peça | Quan | Per què |
|---|---|---|
| **Rúbrica com a funció parametritzada + perfil YAML** | **Ja** (és C3/C4) | No és nou: és explicitar el que l'spec ja fa. Val la pena escriure-ho així des de R2. |
| **A · Sembra del perfil per historial de guanyades** | **v1.5, barat i alt valor** | Una passada a l'API de concessions per municipi; corregeix punts cecs; dona exemples positius per al banc. |
| **B · Senyal de veïns** | **v2** | Reutilitza la semblança que datapoble ja té, però demana definir clústers i la regla de modulació; no bloqueja la demo. |
| **Camps v2 de la rúbrica** (inversió mínima, bestreta) | v2 | Apresos de Castellar (XS extrem); milloren la precisió sense canviar la doctrina. |

---

## 4. Els guardaraïls (perquè no es converteixi en soroll o en biaix)

1. **Historial i veïns MODULEN, no decideixen.** El filtre dur i la porta humana manen. Un fals
   positiu prioritzat segueix sent un fals positiu.
2. **La rúbrica es congela; el perfil evoluciona.** Canviar el pes d'una matèria (config) no és
   canviar la doctrina (rúbrica). Només la config es toca sovint; la rúbrica, amb banc nou.
3. **El biaix del «sempre el mateix».** Sembrar el perfil amb l'historial pot reforçar el que ja es
   demana i amagar oportunitats noves — per això el senyal de veïns (B) hi juga en contra: porta el
   que el municipi **encara no** demana però un semblant sí. A i B es contrapesen.
4. **Privadesa (recordatori):** l'historial de guanyades és públic (transparència), però el perfil
   —matèries, projectes en cartera, peers— és estratègia municipal → segueix el model d'accés privat
   del radar (§9 de l'spec funcional).

---

## 5. El titular per a la demo (i per a la Diba)

«El radar no és un producte per a la Pobla: és **una rúbrica i N configuracions**. La mateixa doctrina,
sembrada amb el que cada municipi ha guanyat i amb el que guanyen els seus veïns, es desplega a
qualsevol dels 31 del Berguedà —i als 177 de la demarcació— canviant un fitxer, no el codi.» Això és
exactament el que la Magda (orientació a la dada) vol sentir: no una eina, un **mètode replicable**.
