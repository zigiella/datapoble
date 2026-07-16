# Ratificacions de R1 i X1 — verificació adversarial de Talaia (2026-07-16)

Els dos fronts van entregar amb el dial a una tasca. **Els he verificat jo, independentment**, no
m'he fiat del seu handoff. Tot el que afirmen queda **confirmat**. PRs #247 (R1) i #248 (X1), fusionats.

## R1 · Sondeig — les tres decisions, RATIFICADES

**1. Incloure l'àmbit estatal (`regiones=1`) — RATIFICADA.** El llistó enumerava CAT+4 províncies i ell
hi va afegir l'estatal: **1.275 convocatòries disjuntes** (12 de 52 en un batch real d'un dia). El seu
raonament és exacte i el faig meu: un ajuntament **sí que es pot presentar** a convocatòries
ministerials, i deixar-les fora seria un **FN de sistema** — el pecat greu de C4 §1. A més, C3 §3 preveu
`estatal` com a valor d'àmbit, que sense això no casaria mai. **Ingerir de més ho arregla R2; ingerir de
menys no ho arregla ningú** — el que no entra és invisible per sempre. El revert és una línia
(`REGIONS_R1_SPEC`), documentat.

**2. La negativa a parsejar el `termini` — RATIFICADA, i el contracte s'esmena.** Mesurat: només **8/26**
porten data estructurada; **11/26** la porten en prosa. Va **refusar escriure un parser** perquè seria
«inferència servida com a fet, al camp que decideix si s'hi és a temps». Correcte. C3 s'esmena (**§2 bis**
nou): camp `termini_text` per al literal, `termini: NULL` vol dir «la font no en dona data» **≠ «no hi ha
termini»**, R2 no pot descartar per NULL, R4 les marca «termini per confirmar», i `estat` mai es deriva
d'un NULL. El forat era del contracte, no seu.

**3. La trampa de codis no aplicable a R1 — RATIFICADA.** Verificat, no suposat: la BDNS no publica cap
codi municipal. El test queda com a guarda que ho mantingui cert.

**Esmenes a l'spec que aporta (correctes):** `vpd=GE` no és obligatori · el mapa de camps és el del
detall, no el de la cerca · `urlBasesReguladoras` és text lliure, no una URL.

**La trampa és pitjor del que jo vaig especificar:** jo vaig escriure «~3/4»; el mesurament real diu
**86%** (`regiones=49` → 867 · `49,50,51,52,53` → 6.057). I va trobar que **els paràmetres desconeguts
s'ignoren en silenci** — per això el seu test **compta files** en comptes de mirar codis HTTP. Bona feina.

## X1 · Brúixola — dos forats de producció, confirmats per mi

**«Adaptat, no copiat» ben resolt.** Els marts no porten `estimacio`/`rang_baix`/`etca_oficial`/
`collision_group`; copiar hauria estat fer inventar columnes al model. El registre passa a ser **de la
cel·la** (oficial=mesurat · senyal=`categoria: derived` · soroll=`confianca: baixa`, mètrica del
contracte). **El que no sobreviu, declarat i no endevinat:** les bandes (sense intervals, la
distingibilitat es degrada a l'empat exacte) i la col·lisió (és propietat de l'estimador, no del mart).

**Forat 1 — el guanyador fals. CONFIRMAT per mi:** hi ha **47 municipis empatats a `index_turisme = 100`**
(Capolat, Castellar del Riu, Castellar de n'Hug, Gisclareny, Granera…) i el `LIMIT 1` en triava un a
l'atzar: el xat deia *«el municipi amb més pressió turística és Capolat»*. **Un guanyador fals servit
com a fet** — el pecat que l'experiment sencer combatia, viu a producció. Va fer bé d'arreglar-ho al
determinista: C5 §2 el fa **fallback de la gàbia**, i un fallback que menteix no és un fallback.

**Forat 2 — el caveat esborrat. CONFIRMAT per mi:** `caveat:` surt **14 vegades** a `metrics.yml` —
**totes les inferències**— i **cap codi del repo el llegia** (el camp del codi és `note`). Producció
servia les inferències **sense el seu caveat obligat**, incloent-hi «852 habitants (est.)» — que és, a
sobre, **el número col·lidit de la Pobla**. La collita s'ha pagat sola el primer dia.

**Evidència verificada per mi:** 187 tests verds (116+71 nous), offline · 13/13 evals originals sense
regressió · 7/7 eval nou end-to-end · `packages/geo-rag` **0 fitxers tocats** · `politics.py` **intacta**
· pin `openai>=1.30` inalterat.

## El que això destapa i queda a la cua

- **`main` és VERMELL** (`test_licitacions::test_real_parquet_cobertura_i_conservacio`, ~7,67 M€ de
  desquadre) i **ningú ho veia perquè cap test de `signals` corria a CI**. És un forat a la porta que jo
  guardo; el reconec. R1 hi ha posat els seus tests (acotats al seu fitxer, honestament). **Cua de
  Sondeig: arreglar-ho i treure l'acotació** perquè CI corri tot `signals`.
- **Saturació dels índexs** (Sondeig): 47 municipis al topall de 100 no és casualitat. El xat ja no
  menteix, però un índex que satura la meitat de la comarca al màxim, **informa?**
- **`nota:` vs `caveat:`** (Talaia): unificar-ho al contracte.
- Les **26 fixtures reals** de R1 esperen l'etiquetatge daurat de **Bea**, sense cap `golden` posat per
  cap agent — tal com mana C4.

— Talaia (coordinació · guardiana de main)
