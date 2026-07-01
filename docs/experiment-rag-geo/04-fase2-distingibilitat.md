# Fase 2 · la regla de distingibilitat — contracte de disseny (abans de codificar)

**De:** Talaia · **Origen:** nota de la Rapaz (30-06-2026, OneDrive/CAJON/13) · **Data:** 2026-07-01
**Ordre:** aquest contracte es fusiona **abans** de codificar la modulació per σ, com el de la Fase 1. «Definit abans de codificar» ha de ser literal a la història del repo.

> La Fase 2 no afegeix una funció nova: **generalitza** la que ja tens. La detecció d'empat de la Fase 1 tracta la **col·lisió exacta** (dos municipis amb el mateix número). El **solapament de bandes** és el mateix fenomen en versió contínua, més comú i ara invisible. La modulació per σ sobre un municipi i l'ordenació entre municipis són **la mateixa pregunta sobre la σ**, i s'han de respondre amb **una sola regla** o es contradiran.

## El principi

Dos municipis només es poden **ordenar** si la distància entre les seves estimacions **supera la incertesa combinada** de les seves bandes. Si no la supera, es reporten com a **no distingibles** — igual que els empats de col·lisió, però per **solapament** en comptes de per **identitat**. La col·lisió exacta de la Fase 1 és el **cas límit** d'aquesta regla, quan la distància és zero.

## La regla de distingibilitat (una, per als dos usos)

Per a dos municipis A i B amb estimacions `est_A`, `est_B` i bandes `[baix, alt]`:

- **Distingibles** si els intervals `[baix_A, alt_A]` i `[baix_B, alt_B]` **no s'encavalquen** (o el solapament és per sota d'un llindar declarat).
- **No distingibles** si els intervals s'encavalquen per sobre del llindar → es reporten com a **no ordenables**, amb el mateix gest que l'empat de col·lisió.
- **Col·lisió exacta** (Fase 1) = `est_A = est_B` i bandes idèntiques = aquesta mateixa regla amb **distància zero**. **No un mecanisme a part** (sense codi duplicat).

**El llindar.** Es comença amb el criteri **net i auditable**: no distingibles si els intervals **p10–p90 se solapen**. És el més defensable perquè fa servir la banda **ja calibrada** (cobertura 78,4%), sense inventar cap paràmetre nou. Si més endavant es vol un llindar més fi (p. ex. exigir que la distància superi la meitat de la suma de semiamplades), es **declara com a paràmetre a metodologia, mai com a veritat** — igual que el |ETCA|≥5% dels 151.

## Els dos usos que surten d'aquesta regla

**1. Modulació per σ sobre un municipi (to graduat).** `S = μ − λ·σ` amb la σ real (la banda). El to i l'amplada del rang de la resposta es modulen per σ: **veu ferma** on és petita, **prudent i rang ample** on és gran. Res de nou respecte al que ja es va votar per al web. *(Recordatori honest: `S = μ − λ·σ` és mean-variance de Markowitz, no una fórmula nostra; el que és nostre és que la σ és una banda de fiabilitat real, no la variància introspectiva del model — vegeu 00-arrencada §veredicte.)*

**2. Ordenació entre municipis (comparació).** Quan la consulta compara («quin té més gent que no consta»), la resposta **no és el número més alt**. És el resultat de la regla: si les bandes no se solapen, s'ordena; si se solapen, es reporta *«els seus intervals s'encavalquen, no els puc ordenar amb confiança»*. **Abstenció d'ordenar**, ara sobre bandes contínues.

## Per què han de compartir regla

Si la modulació per σ i la detecció d'empat decideixen distingibilitat per camins diferents, tard o d'hora **es contradiran**: un dirà que dos pobles són comparables i l'altre que no. **Una sola regla**, aplicada als dos usos, fa que tot el sistema parli amb **una veu** sobre quan es pot ordenar i quan no. La col·lisió exacta i el solapament de bandes són el mateix fenomen a dues resolucions; el sistema honest hi fa el mateix gest.

## El banc de proves de la Fase 2 (des del dia 1)

- Consulta comparativa entre dos munis amb bandes **clarament separades** → s'ordenen.
- Consulta comparativa entre dos munis amb bandes **solapades** → «no distingibles», sense guanyador inventat.
- Consulta sobre un muni de **σ petita** → to ferm.
- Consulta sobre un muni de **σ gran** (soroll) → to prudent, rang ample.
- Verificar que la **col·lisió exacta de la Fase 1** segueix passant per aquesta regla com a cas límit (distància zero), **sense codi duplicat**.

## El que compta com a resposta honesta

La mateixa família que la Fase 1. **Passa** si el sistema ordena només quan la incertesa ho permet i s'absté d'ordenar quan no. **Falla** si presenta un guanyador entre bandes solapades com si fos una comparació informada, o si el to no reflecteix la σ del municipi.

## Ordre respecte a les fases següents

La Fase 2 **defineix** distingibilitat; la Fase 3 (KPI d'abstenció) la **mesura**. La regla ha d'estar fixada abans de la 3, perquè el banc etiquetat de la 3 ha d'incloure casos de **no distingibilitat** i la seva resposta daurada és l'abstenció d'ordenar.
