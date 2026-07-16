# D6 · La proposta a l'Ajuntament de la Pobla de Lillet — què és, exactament

**Especificat per Talaia (2026-07-16) a petició de Bea.** Estat: **esborrany per al vot de Bea** — ella decideix si el porta tal qual, el reescriu o el fa de viva veu.
Contracte vinculant: `docs/ajuntaments/C2-dades-internes.md` (llegir abans de prometre res).

---

## 1. Què és (i per què importa)

**És:** demanar a l'Ajuntament **2 o 3 indicadors que ja tinguin en un full de càlcul** i que **cap font pública té**, per ensenyar-los al seu costat de les dades públiques (padró, atur, presència estimada) al seu propi tauler.

**Per què importa:** és l'única part del producte que **no podem construir sols**. El dashboard amb dades públiques el fem nosaltres; el que fa que un alcalde digui «això és meu» és veure **el seu número** (el que fins ara vivia en un Excel del despatx) amb el context comarcal al costat. A la demo és el moment 2.

**Per què és lead time i no feina:** la resposta d'un ajuntament petit pot trigar setmanes. Per això arrenca **ara**, no a la setmana 5.

## 2. Què demanem, exactament

**2–3 indicadors mensuals que ja recullin.** Res de feina nova: si no existeix en un full avui, no el demanem. Exemples del que sol existir en un ajuntament petit *(orientatius — mana el que ells tinguin)*:

- usuaris del casal de gent gran / de la llar d'infants
- assistents a activitats culturals o de l'espai jove
- consum d'aigua municipal, o incidències de via pública
- llicències d'obres tramitades, o ocupació d'equipaments

**El format (tan simple com es pot):** un CSV per indicador, dues columnes.

```csv
data,valor
2026-01,42
2026-02,38
2026-03,45
```

- `data` en `AAAA-MM` · `valor` un número · opcionalment una tercera columna `nota` per a l'excepció puntual («març: obres, tancat 2 setmanes»).
- Si el tenen en Excel, ens el poden passar en Excel i nosaltres el convertim. **La feina de format és nostra, no seva.**

**Per a cada indicador, dues decisions que són SEVES:**
1. **Es pot publicar?** (`publicable: true|false`) — si diuen que no, el número **no surt mai al web**: només al seu tauler intern i al correu. Es pot canviar d'opinió quan vulguin.
2. **Vols avís?** — un llindar opcional («si els usuaris del casal baixen de 20, avisa'm»). L'avís és **un correu**, mai una publicació automàtica.

## 3. El que els prometem (i que el contracte C2 ens obliga a complir)

- **Mai persones ni adreces.** Només **agregats del municipi** (quants, no qui). Si un fitxer porta dades personals, el retornem sense processar.
- **El que no és publicable, no és públic.** El nostre codi és obert, i per això els indicadors no publicables **no entren mai al repositori**: viatgen per canal privat i viuen fora del codi.
- **Validació abans de res:** si un valor és anòmal (un salt de x3, una data que no encaixa), **no el publiquem: preguntem**.
- **Cap número sense el seu origen:** el seu indicador sortirà sempre citat com a «font: Ajuntament de la Pobla de Lillet», amb la data.
- **Poden sortir quan vulguin.** Deixem de fer-ho servir i s'esborra.

## 4. El que hi guanyen (l'honest, no el venut)

- El seu número **amb context**: no «42 usuaris», sinó «42 usuaris, i com es compara amb el que és esperable per a un municipi de la seva mida».
- El **tauler de govern**: atur del mes, presència estimada amb la seva banda, licitacions, i els seus indicadors, tot en una pàgina.
- El **radar de subvencions** (quan surti de proves): un correu al matí si la BDNS publica alguna cosa que encaixa amb el poble.
- **Zero cost i zero manteniment** per a ells: ho fem nosaltres; ells envien un CSV al mes (o quan puguin).

**El que NO els prometem:** que això sigui un servei amb suport garantit. És un projecte en construcció, i se'ls diu així.

## 5. El «no» també és una resposta

Si diuen que no, o si no contesten: la demo va amb **dades sintètiques marcades «demo»** (pla B del moment 2), i es diu que són sintètiques. **No inventem un ajuntament col·laborador que no existeix.** Un «no» d'ells és informació útil: ens diu què fa por (privacitat? feina? exposició?) i això entra al disseny.

## 6. Com es porta (les tres opcions per a Bea)

1. **De viva veu** (recomanat si hi ha confiança prèvia): la conversa curta, i aquest doc després com a resum escrit.
2. **Correu amb aquest doc adjunt**, resumit a 10 línies al cos.
3. **Talaia prepara un correu formal** en castellà/català per a secretaria, i Bea el signa.

**Decisió de Bea:** quina de les tres, i si els exemples d'indicadors del §2 encaixen amb el que sap de la Pobla (ella coneix el poble; jo no).
