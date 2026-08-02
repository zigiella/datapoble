# ADR 0001 · De Cambium Charter a Mycelia Relay v0.5

- **Data:** 2026-08-01
- **Estat:** acceptada i executada
- **Decideix:** la direcció (Bea), preparat per NEOCAM (metodologia). Executat per Talaia.
- **Abast:** mètode de treball de datapoble. **No** toca el producte ni les dades.

## Context

datapoble va estar dos mesos sota **Cambium Charter**, un aparell pensat per a **diverses agents amb
contextos separats**: cua assignada a `bitacora/next.md`, latido, torns, porta de set punts,
jurisdiccions tancades.

La realitat del projecte és una altra: **una coordinadora (Talaia) amb subagents propis** que ella
mateixa despatxa. Aquell aparell cobrava cerimònia que ja no resolia res —la cua me l'escrivia a mi
mateixa, el latido me'l donava jo— mentre deixava sense resoldre el que sí que fa mal:

1. que el meu jo de demà **recuperi el fil**,
2. que la direcció pugui deixar un encàrrec **sense obrir el portàtil**,
3. que estigui escrit **què pot veure un agent al núvol** quan entri.

## Decisió

Adoptar **Mycelia Relay v0.5** (`github.com/zigiella/mycelia-relay`, tag comprovat com a últim
segellat) i retirar Cambium Charter.

**NO s'adopta Mycelia**, el graf de coneixement: la direcció l'ha aturat per replantejar-lo —escriure
coneixement compartit de forma contínua, entre projectes, és un risc de filtració que avui no
compensa. El bloc `knowledge:` queda buit; Relay funciona sencer sense ell des de la v0.4.

## Què mor, què sobreviu, què es muda

**Mor** (aparell de coordinació que una agent sola no necessita):

| | |
|---|---|
| `bitacora/next.md` com a cua | → **GitHub Issues** reclamables (migració d'una vegada: #302–#314) |
| Porta de set punts (`PR-checklist.md`) | → plantilla de PR de Relay |
| Latido, torns i dial | → estats de Relay (`ready`, `working-local`, `paused-local`, `blocked`, `review`, `done`) |
| **Jurisdiccions rígides** (regla 3) | → propietat de sentit comú, reclamada i temporal |

**Sobreviu intacte** — i això és el que importa: **no es perd res dur**. Les regles de producte i
seguretat es promouen a `REGLAS.md` a l'arrel, amb la numeració i el català: la **7** (procedència
de les xifres), la **9** (carril de dades en silenci, amb el go/no-go de ρ≥0,7 i error ≤15%), la
**9b** (pressupost = límit, no silenci), la **10** (secrets mai al repo — que aquí compta el doble
perquè datapoble és públic) i l'**11** (working dir compartit). **Cap s'ha suavitzat ni renumerat.**

Relay demana el **mínim, no el sostre**: quan el contracte genèric i aquestes regles diguin coses
diferents, **manen les regles del projecte**.

**Es muda de casa, no de contingut:** els `docs/equipo/*_role.md` es queden on són (segueixen sent
el planter dels fronts); el seu marc de referència passa a ser `AGENTS.relay.md`.

**No s'esborra res:** `.cambium/` i les bitàcoles queden **marcades com a retirades**, senceres.
Invalidar, no esborrar: el historial és dada.

## La peça que més aporta: `data_map`

A `.relay.yml` es declara **quin material té datapoble, on pot estar** (classe) i **què se'n pot
fer** (drets), amb les rutes de cadascun. Són **dos eixos independents a propòsit**: un material pot
viure legítimament al repo i tot i així no poder-se reproduir.

Hi han quedat **9 materials declarats**. La **regla 9 aterra aquí**: deixa de ser una frase en un
document i passa a ser una entrada que un agent cloud llegeix abans de tocar res.

**Correcció del terreny respecte del document de transició:** suposava que el Nivell C era
`local-only`, i la realitat és que **sí que és al repo** (14 fitxers versionats a
`data/territorial/`). Com que la classe diu *on pot estar* i el dret *què se'n pot fer*, queda
`repository` + `solo-agregado` — que és exactament el que la regla 9 mana.

## Qui integra

**La regla 2 no canvia:** Talaia integra el que és rutinari. **Escala a la direcció:** el que creua
la membrana (publicar dades o web, desplegar, gastar), el **go/no-go de la regla 9**, canviar regles
dures, **tocar les comprovacions o els permisos** (qui controla els checks controla tota la
verificació futura) i el canvi que escombra mig repositori. I per damunt de la llista: **davant del
dubte, pregunta.**

## Conseqüències

- La cua és pública i escrivible des del mòbil; també per a un agent cloud, més endavant.
- Es perd la vigilància automàtica de la jurisdicció; **la qualitat la sosté la verificació**
  (regla 8), que en aquest projecte ja és el que de fet ha atrapat els errors.
- `relay-check` corre al CI però **no és una porta**: avisa, amb `STRICT=0`, i només mira els PR
  amb etiqueta `relevo`. La porta de `main` segueix sent el CI de datapoble.
- Un `data_map` buit **no valida**, a propòsit. Comprovat abans d'omplir-lo.

## Seguiment · el que hem tornat al mètode (2026-08-01)

La direcció ho va demanar així: *«tot allò que t'agradava i era útil, no ho perdis. Ho reintegres
amb lo nou i fas una carta explicant el teu cas.»* Fet a
**[zigiella/mycelia-relay#6](https://github.com/zigiella/mycelia-relay/pull/6)**, amb el cas sencer
a `docs/casos/datapoble-desde-cambium.md` d'aquell repo. Quatre propostes, cadascuna amb el seu
número:

1. **Un camp «l'encàrrec, contrastat» al PR template.** En una sola sessió, tres encàrrecs meus
   portaven una premissa falsa i les tres les va caçar qui les executava; cap va arribar a
   producció. Contradir amunt té un cost social que una casella elimina. **És la que més defensem:
   no era de Cambium, era dels nostres `role.md` — o sigui que no demanem que ens tornin res, sinó
   que ho tinguin ells.**
2. **Un dret nou, `no-publicar`.** Els quatre drets barregen «què puc fer amb el fitxer» i «què pot
   publicar el producte». La nostra capa electoral no encaixa en cap.
3. **La membrana es creua per efecte lateral**, no només per intenció. És el que substitueix, en
   part, el que ens donava la jurisdicció rígida: la valla va aturar coses reals i el que la
   reemplaci no pot ser només la bona voluntat.
4. **L'execució de la pròpia adopció no escala** — i la transcripció de les regles dures sí que
   l'hauria de revisar qui les va escriure. Jo vaig transcriure les de seguretat de la meva
   direcció sense que ningú les mirés.

**El que NO hem perdut i no cal demanar:** les regles dures són senceres a `REGLAS.md`, els
`role.md` es van quedar on eren, i l'obligació de cada front de dir què ha trobat fals al seu
encàrrec segueix escrita a tots cinc.

