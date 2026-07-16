# La demo a la Diba — què és, exactament

**Especificat per Talaia (2026-07-16) a petició de Bea.** Estat: **proposta — el guió és vot de Bea.**
**DATA: no n'hi ha (decisió de Bea, 2026-07-16).** Es valorarà presentar-la **quan el producte sigui online
i funcionant** — no es treballa contra un calendari extern. El §4 (la lògica de la data) queda com a
referència per al dia que es decideixi: segueix valent que el número del radar necessita el seu mes.
Referència: `docs/spec-ajuntaments-v1.md` §7 (guió original de Marea) — aquest doc el concreta i n'explicita els prerequisits.

---

## 1. Què és (i què no)

**És:** una reunió de ~30 minuts amb **Magda Lorente** (Diba — Oficina de Serveis Digitals i Orientació a la Dada / SeTDIBA), on **Bea** ensenya datapoble funcionant per a un ajuntament real (la Pobla de Lillet) i n'obté un **següent pas concret**. Dels 30', ~15 són demo en viu i la resta conversa.

**No és:** una venda de producte, ni una prova de concepte teòrica, ni una petició de finançament. És ensenyar una cosa **que ja funciona** en un municipi real i preguntar on encaixa (SeTDIBA? Catàleg de serveis? pilot amb més municipis?).

**Qui:** presenta Bea (veu humana, direcció). Talaia prepara el material i verifica cada número abans que surti. Cap agent «apareix» a la demo — el que es veu és el producte.

**Format:** *(a decidir per Bea — condiciona els assajos)* presencial a la Diba · videotrucada · o híbrid. Si és presencial, cal preveure connexió i que el correu del radar arribi aquell matí.

## 2. El guió (5 moments, cadascun amb el seu prerequisit)

| # | Moment (què veu la Magda) | Prerequisit dur | Si no hi és |
|---|---|---|---|
| 1 | **Mode govern de la Pobla**: atur del mes, KPIs amb percentil comarcal, sèries | D5 desplegat + D1 (atur real) + D4 (percentils al mart) | no hi ha demo — és el cor |
| 2 | ~~Dades internes reals~~ → **FASE 2** (decisió de Bea): la v1 va només amb dades públiques. El moment 2 passa a ser **la lectura de govern**: els 12 KPIs amb rang comarcal (`gorra-alcalde-pobla.md`) — incloent-hi **l'avís honest** que el nostre model de presència falla a la Pobla | D5 + D4 | — |
| 3 | **Xat en directe**: una resposta traçada (font+fórmula) i **una abstenció amb motiu** | X2 (API viva) + catàleg carregat | mode offline honest (pantalla dissenyada) o es narra sense clicar |
| 4 | **El correu del radar** d'aquell matí, amb convocatòries reals | R4 corrent + perfil de la Pobla actiu | s'ensenya un correu arxivat d'un matí anterior (dir-ho) |
| 5 | **Canvi a Castellar amb un clic** (multi-poble = 1 YAML) → tancament: *els ~177 municipis <5.000 hab. de la demarcació són el mateix pipeline* | C3 (perfils) + D5 multi-muni | es narra amb el YAML a la pantalla |

**El moment que decideix la reunió és el 4 + el número que l'acompanya.** La resta ensenya que el producte existeix; el radar ensenya que **vigila sol**, i el número diu **si te'n pots fiar**.

## 3. El one-pager (el que queda a la seva taula)

Una cara. Conté, en aquest ordre:
1. **Què és** riusdegent en dues línies + què hi guanya un ajuntament petit.
2. **Els números, amb el seu asterisc** (verificats per Talaia, mai un titular pelat):
   - Radar: **recall del mes de validació, tal com surti** (el número que importa aquí).
   - Xat: **abstenció honesta** — 21/21 al banc determinista de la Fase 3 (amb el mirall declarat) · 42/42 sota paràfrasis adversarials · capa generativa **FN=0 a les tres passades declarades** (mai «170/170» com a titular; la gàbia verificada és ~163/170).
3. **Què NO fa** (els no-objectius): no envia res a cap administració, no amaga indicadors incòmodes, no toca dades personals.
4. **El següent pas que proposem** (§5).

## 4. La data no és lliure — la determina el número del radar

La finestra de l'spec és **setmana 6–8**. El que la fixa:

- El radar ha d'estar **viu a final de la setmana 3** (R1→R2→R3→banc C4→R4).
- La **validació paral·lela és d'un mes** (C4 §5) i és el que produeix el número del moment 4.
- Per tant: **setmana 8 = mes complet** → el número és el que hem contractat.
  **Setmana 6 = ~2-3 setmanes** → el número existeix però és més fluix, i s'ha de presentar com el que és («tres setmanes, no un mes»).

**Recomanació de Talaia: setmana 8.** Motiu: anem a ensenyar honestedat mesurada; presentar-hi un número escapçat contradiu el missatge. Les úniques raons per anar a la 6 serien externes (l'agenda de la Magda, o que la finestra es tanqui) — i llavors es diu el que és, sense maquillar.

**Riscos, dits clars:** (D6 ja no és risc: és fase 2 per decisió de Bea.) R4 depèn que el banc C4 passi la porta; si el banc surt DECEBEDOR o pitjor, **no hi ha correu a la demo** (porta innegociable) i el moment 4 cau: la demo es reenfoca al dashboard + xat, i el radar es presenta com a recerca en curs amb el seu número tal com va sortir.

## 5. Què li demanem (el següent pas)

No demanem diners ni compromís. Demanem **una d'aquestes tres**, i marxem amb una:
1. **Encaix**: on viu això a la Diba (SeTDIBA? Catàleg de serveis digitals? un altre programa?).
2. **Pilot**: 2-3 ajuntaments més de la demarcació que hi tinguin interès (escalar = activar un YAML, no construir).
3. **Contrast**: què li falta perquè sigui útil de debò per als seus municipis — el «no» també és resposta útil.

## 6. Definició de fet (preparació)

- [ ] Assaig complet amb Bea, cronometrat, amb la web real (no diapositives).
- [ ] Cada número del one-pager **re-verificat per Talaia** contra les actes del repo el dia abans.
- [ ] Pla B de cada moment provat (no narrat: provat).
- [ ] El correu del radar d'aquell matí, comprovat abans de la reunió.
- [ ] One-pager imprès i en PDF.
