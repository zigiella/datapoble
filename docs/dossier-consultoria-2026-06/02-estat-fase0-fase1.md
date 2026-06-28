# Estat per a la consultoria — Fase 0 + Fase 1 executades

**Data:** 2026-06-28 · **De:** Talaia (coordinació) · **Per a:** Rapaz (consultoria) + Bea (direcció).

> Resposta executada a la reconducció i a les sis notes. **Fase 0 ✅. Fase 1 ✅ (nucli epistèmic).**
> Tot fusionat a `main` (#182–#192) i **desplegat**. Queda **una sola superfície**: la costura a la fitxa.

---

## Què s'ha fet (per nota)

**Reconducció adoptada.** Rumbo «l'observatori que sap el que no sap»; contracte d'abast (mapa públic
**11 → ~3 indicadors**: gap reenquadrat + % habitatge no principal + residus). Frase i decisions fixades
al repo (`01-reconduccio.md`, `contracte-abast.md`).

**Fase 0 — congelar abast i matar el que trenca.**
- Mapa públic curat als 3 que aguanten (tipologia/pressió/IETR/contradiccions/restauració/densitat/renda
  fora del mapa CAT).
- **Política fora de tot el web** (ruta, blocs de fitxa i metodologia, glossari, nav i peu).
- Gap reenquadrat com a hipòtesi (eix «hi dorm menys/més del que consta», fora «població que el padró
  no veu»).

**Fase 1 — el nucli epistèmic.**
- **Calibració real.** La banda (p10–p90 del residual held-out per tipus) és honesta: l'interval
  nominal del **80% cobreix el 78,4% empíric** (held-out, n=486). Reliability diagram complet.
  *Pendent menor:* dos tipus metropolitans petits (corona n=9, litoral n=7) queden infracoberts
  (55–57%); en públic ho cobreix la costura (≥1.000 = Idescat).
- **Partició dels 151 de signe oposat.** Per l'interval per-muni: **8 senyal · 142 soroll**. El «31%»
  real és **~1,6%**. La resta era el nostre propi marge d'error disfressat de fenomen.
- **El Prat i el règim dens.** L'aeroport no era la causa (el consum domèstic és baix, no inflat).
  La raó de fons: en nuclis densos el consum domèstic per càpita és baix i la `base_pred` ho
  **infra-corregeix** → el gap negatiu dens (Barcelona −18%, el Prat −23%) pot ser **artefacte**, no
  presència. **No ho podem distingir** → Barcelona deixa de ser cas de contrast (és el més contaminat):
  **li traiem l'etiqueta a tot arreu** i passa a ser l'**exemple de la secció de límits**.
- **/metodologia · secció «límits del model»** amb tres gràfics germans: reliability, scatter
  ETCA↔pernocta (la **banda de soroll** és la protagonista: 142/150 hi cauen dins), i **règim dens**
  (consum/càpita vs densitat amb la mediana de calibració). *«Marquem on falla el nostre model.»*
- **Validació canònica.** «Validat **als 9 munis ≥1.000 hab del Berguedà** (de 31), ρ=0,967, error
  8,2% **dins de mostra**; la generalització és la banda **held-out 80%→78,4%**, no el 8,2%.» Una
  sola font (i18n `met_valid_canon` + contracte d'abast); la resta hi apunta.
- **Costura present-vs-padró**, decidida **per superfície**:
  - *Waveform* (manifest): la **nostra pernocta** a tots els punts (la nostra mètrica distintiva no es
    cedeix); Idescat com a **contrast** al hover. Ple = contrastable (≥1.000), contorn = només nostra.
  - *Mapa* (credibilitat): **≥1.000 = mana Idescat** (Barcelona pinta **+6%**, no −18%; verificat
    online), la nostra estimació com a contrast etiquetat al tooltip; <1.000 tramats per confiança baixa.
- **Sèrie temporal multianual** (12 anys d'ICAEN a la raw, 1 tall en ús): **documentada com a futur**,
  no executada — tendència + test d'estabilitat senyal/soroll en el temps.

## Les troballes que valen (l'honestedat com a producte)

1. El «31% de discrepància» era **el nostre marge** (8 senyal reals de 486).
2. El model **falla en règim dens** i ho **marquem nosaltres**, amb nom de fenomen.
3. La validació és de **9 municipis**, no del Berguedà sencer — dit a tot arreu amb el mateix text.

## Estat al repo

Fusionat i desplegat: reconducció (#182), Fase 0 (#183–#186, #188), Fase 1 (#187, #189–#192).

## Què queda

- **Costura a la fitxa** (els 5 números + seccions del gap → mateixa regla: ≥1.000 mana Idescat). Últim
  pas de Fase 1.
- Després: la **passada d'UI/textos sense overpromise** (la que ara demanaràs).

---

## Idees per a la passada d'overpromise (per si sumen)

Punts on el web encara promet de més, vistos durant l'execució:

1. **El mapa de la HOME encara pinta `tipologia`** (Barcelona = «excursió») — és el **forat de
   credibilitat viu** que queda. Canviar-lo a **% habitatge no principal** (brief de home, Bloc 4) o,
   com a mínim, a un indicador que aguanti a escala CAT.
2. **«El que les dades criden»** (títol de troballes) sona sensacionalista; i les **targetes d'IETR i
   divergència** són indicadors **retirats**. Renombrar («Per on entrar») i treure-les (Bloc 3).
3. **«presència real (qui hi dorm)»** → «**presència estimada**» allà on aparegui: és inferència, no
   recompte. Evitar «real» com a adjectiu de la nostra xifra.
4. **Còpia d'abast de la home** («tota Catalunya, dades completes…») — afinar perquè no sob-prometi
   cobertura ara que el mapa públic són ~3 indicadors i la resta és context.
5. **«Pregunta-li»** és determinista i promet IA que no compleix (Lleida vs Girona → respon Barcelona):
   o secció experimental amb disclaimers d'al·lucinació, o desconnectar fins fer-la bé.
6. **Tooltips/llegendes del mapa**: revisar que cap parli de «validat» a seques (ja corregit el gruix
   amb la frase canònica; convé un últim repàs).

— Talaia 🌊
