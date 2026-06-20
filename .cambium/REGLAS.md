# REGLAS — datapoble (innegociables)

Les regles que **no es trenquen**, per damunt de qualsevol conveniència. El cos del mètode és a
`.cambium/CHARTER.md` (Cambium Charter, sello a `.cambium/VERSION`); aquí, només el que és dur i
específic de datapoble.

## Direcció i autoritat
1. **Direcció humana = Bea.** Decideix el QUÈ i el PER QUÈ, guarda els secrets i té el **vot narratiu
   final** (marca, còpia, què es publica).
2. **Una sola autoritat de merge = Talaia** (coordinadora) en tot moment. Ningú més fa merge. Mai
   amb la verificació en vermell (CI o la que tingui el projecte). La porta és disciplina
   (`.cambium/plantillas/PR-checklist.md`).
3. **Jurisdicció acotada:** cada front (Sondeig/Cabal/Brúixola/Mirador/Llegenda) mana a la seva zona;
   fora, **handoff**, no edites. (Vegeu `CONTRIBUTING.md` per a les zones.)

## El repo és la veritat
4. **Repo > xat.** Si divergeixen, mana el repo. L'estat durador va a la **bitàcola/PR/memòria**, no
   al xat. La memòria de coordinació és una safata subordinada, mai font de veritat.
5. **Identity-inline:** cada commit diu qui l'ha fet — `Co-authored-by: <Agent> <agent@datapoble.local>`.
   **MAI** el trailer d'IA genèric («Co-Authored-By: Claude», «Generated with Claude Code»): l'autoria
   és de l'agent del front, no de l'eina.
6. **Mai rutes locals** (`C:\…`, `/home/…`) en fitxers versionats; el repo es referencia per URL.
6b. **Fast-path no-codi** (v0.4): els artefactes de coordinació (`bitacora/next.md`, bitàcoles) es
   poden committejar **directe** amb identity-inline + verificació anti-secrets/rutes, encara que no hi
   hagi CI. Tres línies vermelles que SEMPRE van per la porta del PR: **mai codi, mai doctrina
   (`.cambium/`), mai jurisdicció d'altri**.

## Honestedat com a feature
7. **Cap xifra sense procedència.** Estimació ≠ cens: es marca, i si la incertesa mana, es publica
   en **rang**, no com a xifra absoluta. El «no» honest i el fallo sorollós per sobre del poliment fals.
8. **Verificar-o-declarar.** Si no es pot verificar, el PR no és llest; la coordinadora munta el camí
   de verificació. La verificació independent és per **hito / risc / creuada**, **no per-acció**.
9. **Carril dades en silenci:** les dades internes de l'escala (covariables, Nivell C de Catalunya)
   no es publiquen fins que el seu tipus passi el **go/no-go** (ρ≥0,7 i error≤15% per a presència
   absoluta; si no, índexs/rangs relatius).
9b. **Pressupost = límit, no silenci** (Dial, 3a lectura, v0.5): si s'esgota el crèdit assignat d'un
   torn/tasca, s'**escala i es reporta** (bitàcola / a Bea); mai es mor en silenci. *Morir per
   pressupost és fallar en silenci.* (P. ex.: el límit de despesa mensual que va tombar un workflow
   → es reporta i es busca via alternativa, no es calla.)

## Seguretat (repo públic)
10. **Secrets MAI al repo ni a la sortida.** No imprimir, fer eco ni committejar `OPENROUTER_API_KEY`,
    `HF_TOKEN` ni cap credencial; mai dades compromeses al repo públic. Les claus viuen als secrets
    d'Actions, no al codi.
11. **Working dir compartit:** verifica el tip de branca; usa ops ref-only / fast-forward; **mai
    reescriguis ni esborris la branca d'un altre** sense autorització. Committejar només quan es
    demana; mai saltar-se hooks ni la signatura.
