# Espina territorial + breadcrumb (navegació de tot Catalunya)

**Data:** 2026-06-18
**Autora:** Talaia (encarna Sondeig/dades + Mirador/web)
**Latido (Bea):** «podem seguir» → tria: espina + breadcrumb (§7).
**Status:** a la porta del PR (branca `feat/espina-territorial`). Avança P0 #7 (part espina §7).

## Què he fet
Ara que tot poble és navegable (#146), li dono CONTEXT de situació i navegació entre veïns.

1. **Derivació muni→comarca→vegueria** (`tools/deriva_territori.py`): punt representatiu del municipi
   dins la comarca (EXACTE: les comarques són unions de munis sencers; 947/947, **0 fallback**) +
   `comarca_vegueria.csv`. Artefacte `data/web/municipis-territori.json` (servit pel prebuild).
   Contracte `$lib/contract/territori.ts`.
2. **Breadcrumb** (`Espina.svelte`): Catalunya › vegueria › comarca › municipi, a la fitxa de TOTS
   els munis (Berguedà, coberts i «sense dades»). Catalunya enllaça a la home; vegueria/comarca són
   text (encara no tenen pàgina pròpia).
3. **Veïns de comarca**: secció «A la mateixa comarca: {X}» amb xips-enllaç als altres munis de la
   comarca (límit 30 + nota «se'n mostren N de M» per a comarques grans). Navegació per als 947.
4. **Bug corregit (de #146):** l'eyebrow de la fitxa mostrava `dataset.comarca` (= «Berguedà») per a
   TOTS els munis → fals per als de fora. Ara fa servir la comarca real (territori).

## Verificat (HTML prerenderitzada)
- `svelte-check` 0/0 · `build` OK.
- Salou → Tarragonès · Camp de Tarragona; 21 veïns (tot Tarragonès; Cambrils NO, és Baix Camp ✓).
- Roses → Alt Empordà; 30 xips + «se'n mostren 30 de 67» (límit OK).
- Berga → Berguedà · Comarques Centrals. Abella de la Conca (sense dades) → Pallars Jussà · Alt
  Pirineu (l'espina hi és igualment).
- Sanity de la derivació: Lleida→Segrià, Vielha→Val d'Aran, Tortosa→Baix Ebre, Puigcerdà→Cerdanya.

## Pendent de #7 (spec ric)
Dades obertes §9 · viz noves §4 · 3 profunditats + test CI. (L'espina §7 és aquest PR.)

— Talaia 🌊
