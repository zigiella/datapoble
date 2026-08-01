# REGLAS — datapoble (innegociables)

Les regles que **no es trenquen**, per damunt de qualsevol conveniència.

El marc de treball és **Mycelia Relay** (`AGENTS.relay.md` + `.relay.yml`, segell `v0.5`). Relay
demana el **mínim, no el sostre**: **aquestes regles l'endureixen i manen** quan diguin coses
diferents. Els fronts i les seves zones són a `docs/equipo/*_role.md`.

*Promogudes des de `.cambium/REGLAS.md` el 2026-08-01 en passar de Cambium Charter a Relay. La
numeració i la llengua es conserven: cap regla s'ha suavitzat ni renumerat. L'única que canvia de
contingut és la 3, i el perquè hi va escrit.*

## Direcció i autoritat
1. **Direcció humana = Bea.** Decideix el QUÈ i el PER QUÈ, guarda els secrets i té el **vot narratiu
   final** (marca, còpia, què es publica).
2. **Talaia integra el que és rutinari.** Mai amb la verificació en vermell. **Escala a Bea:** el que
   creua la membrana (**publicar dades o web, desplegar, enviar, gastar**), el **go/no-go de la
   regla 9**, **canviar regles dures**, **tocar les comprovacions o els permisos** (CI, validadors,
   protecció de branques, secrets — qui controla els checks controla tota la verificació futura) i
   el **canvi que escombra mig repositori**. I per damunt de la llista: **davant del dubte, pregunta.**
   Preguntar és gratis; integrar amb dubtes el paga qui ve després.
3. **Propietat reclamada, no alambrada** *(reescrita 2026-08-01; abans deia «jurisdicció acotada»)*.
   Cada front té la seva zona i normalment hi mana, però la propietat és **de sentit comú, reclamada
   i temporal**: es pot editar la zona d'un altre si millora la feina, dient-ho. **El que cuida la
   qualitat és la verificació, no la tanca** (regla 8). El que no canvia: una sola tasca, un sol
   escriptor, i el traspàs es diu per escrit.

## El repo és la veritat
4. **Repo > xat.** Si divergeixen, mana el repo. L'estat durador va als **Issues, al PR i a la
   bitàcola**, no al xat. La memòria de coordinació és una safata subordinada, mai font de veritat.
5. **Identity-inline:** cada commit diu qui l'ha fet — `<Agent> <agent@datapoble.local>`. **MAI** el
   trailer d'IA genèric («Co-Authored-By: Claude», «Generated with Claude Code»): l'autoria és de
   l'agent del front, no de l'eina.
6. **Mai rutes locals** (`C:\…`, `/home/…`) en fitxers versionats; el repo es referencia per URL.
6b. **Fast-path no-codi:** els artefactes de coordinació (bitàcoles, notes) es poden committejar
   **directe** amb identity-inline + verificació anti-secrets/rutes. Tres línies vermelles que SEMPRE
   van per la porta del PR: **mai codi, mai doctrina, mai una regla dura**.

## Honestedat com a feature
7. **Cap xifra sense procedència.** Estimació ≠ cens: es marca, i si la incertesa mana, es publica
   en **rang**, no com a xifra absoluta. El «no» honest i el fallo sorollós per sobre del poliment fals.
8. **Verificar-o-declarar.** Si no es pot verificar, el PR no és llest; qui integra munta el camí de
   verificació. La verificació independent és per **fita / risc / creuada**, **no per-acció**.
9. **Carril dades en silenci:** les dades internes de l'escala (covariables, Nivell C de Catalunya)
   no es publiquen fins que el seu tipus passi el **go/no-go** (ρ≥0,7 i error≤15% per a presència
   absoluta; si no, índexs/rangs relatius). **El go/no-go és de la direcció, no de qui integra.**
   Aquest material està declarat a `.relay.yml` → `data_map` amb les seves rutes, perquè un agent
   cloud ho pugui llegir abans de tocar res.
9b. **Pressupost = límit, no silenci:** si s'esgota el crèdit assignat d'un torn/tasca, s'**escala i
   es reporta**; mai es mor en silenci. *Morir per pressupost és fallar en silenci.*

## Seguretat (repo públic)
10. **Secrets MAI al repo ni a la sortida.** No imprimir, fer eco ni committejar `OPENROUTER_API_KEY`,
    `HF_TOKEN` ni cap credencial; mai dades compromeses al repo públic. Les claus viuen als secrets
    d'Actions, no al codi. Els destinataris del radar són **claus simbòliques, mai correus** (una
    «@» és un error de càrrega, fail-fast).
11. **Working dir compartit:** verifica el tip de branca; usa ops ref-only / fast-forward; **mai
    reescriguis ni esborris la branca d'un altre** sense autorització. Committejar només quan es
    demana; mai saltar-se hooks ni la signatura. Al worktree, **mai `pip install -e`**: el venv és
    compartit i reapuntar-lo trenca les sondes de la resta (ha passat tres vegades).
