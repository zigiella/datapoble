# Adopció del Cambium Charter v0.3.1

**Data:** 2026-06-16
**Autora:** Talaia (coordinadora)
**Latido (Bea):** «actualitzar a Cambium Charter v0.3.1 des de zigiella/cambium-charter@v0.3.1».
**Status:** adoptat (ritual §IX) / a la porta del PR.

## Què he fet (ritual §IX — adopció de versió)
Primera adopció FORMAL del mètode a datapoble (abans era informal: `docs/team-method.md` «v1»,
sense `.cambium/` ni adaptador a l'arrel).

1. **Vendoritzat `.cambium/`** des del kit `github.com/zigiella/cambium-charter` al tag **v0.3.1**
   (clonat, copiat, esborrat el clon): `CHARTER.md`, `CHANGELOG.md`, `VERSION` (segell + `upstream:`),
   `LICENSE`, `EJEMPLOS.md`, `adapters/` (4), `plantillas/` (12). (Ometo el README/CONTRIBUTING del
   kit: són del projecte upstream, no del mètode vendoritzat.)
2. **Segell** `.cambium/VERSION` = «Cambium Charter v0.3.1 · upstream: github.com/zigiella/cambium-charter»
   (ja venia segellat amb la procedència; v0.3.1 grava `upstream:` perquè futures actualitzacions
   resolguin la font soles).
3. **Adaptador a l'arrel** `CLAUDE.md` (cos del kit, omplert: projecte=datapoble, coordinadora=talaia;
   apunta a `.cambium/CHARTER.md` + `.cambium/REGLAS.md` + `docs/equipo/talaia_role.md`).
4. **Innegociables** `.cambium/REGLAS.md` (específics de datapoble: direcció Bea, una autoritat de
   merge=Talaia, repo>xat, identity-inline SENSE trailer d'IA, cap xifra sense procedència,
   verificar-o-declarar, carril dades en silenci + go/no-go, secrets mai al repo, no reescriure
   branques d'altri).
5. **Rol** `docs/equipo/talaia_role.md`; punters al Charter des de `CONTRIBUTING.md` i
   `docs/team-method.md` (que queda com a registre històric; la doctrina no es duplica).

## Topologia
datapoble = configuració **(a) pròpia** (§III): una coordinadora que encarna els fronts com a
**persones**, no com a agents separats en execució. Per això les parts del §IX sobre encolar
l'auto-actualització al `next.md` de cada agent i despertar-los són **N/A** aquí: l'adopció la faig
jo, ara, en aquest torn. No introdueixo `next.md` per-agent (seria over-engineering per a aquesta
topologia; el CHANGELOG v0.3 ja avisa contra el cargo-cult).

## Novetats de v0.3 → v0.3.1 que adopto com a pràctica
- **Verificació independent NO per-acció** (antipatró): cadència per hito / risc / creuada. Ja ho
  aplicàvem de facto; ara és explícit a REGLAS.
- **Verificar-o-declarar** + PR no-llest si no es pot verificar (clau amb el preview headless dels
  mapes: verifico per HTML prerenderitzada i declaro el que no he pogut comprovar visualment).
- **Una sola autoritat de merge** en tot moment; la coordinadora codifica el mínim.
- **`upstream:` al VERSION** → la propera actualització es resol amb un latido mínim.
- **Memòria de coordinació opcional** a `.cambium/memoria/`: de moment NO la versiono (la meva
  memòria viu fora del repo); es pot afegir més endavant, sanejada i sense secrets.

## Pendents menors
- Brossa untracked al working dir (`%TEMP%where.txt`, `docs/cambium-charter-segun-anti.md` —narració
  d'un agent Gemini desada per error—): pendent que la Bea autoritzi esborrar-les (no esborro el que
  no he creat sense permís).

— Talaia 🌊
