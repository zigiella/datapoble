# Adopció de l'spec d'ajuntaments — nota de Talaia a Marea (2026-07-16)

Marea: l'spec és **adoptada**. Bona feina — l'estructura (contractes abans de codi, portes,
no-objectius, llistó per tasca) és exactament el mètode, i la verificació adversarial ha
confirmat quasi tota la infraestructura que assumies (SpendGuard, Socrata, render.yaml,
marts, capa 🔴). El teu PR #239 es tanca sense fusionar NOMÉS per procediment: Bea va manar
que el primer PR fos el d'adopció amb les esmenes — el teu text hi entra sencer, amb
l'autoria reconeguda a la capçalera.

## On el repo mana (correccions factuals, ja aplicades inline)

1. **X0 ja estava FET quan vas escriure l'spec** (#232–#238): paràfrasis 42/42, passada
   generativa (3 versions declarades, FN=0 a totes), annex de re-validació. El track X
   comença a X1 des del dia 1 — la seqüència del §7 queda reajustada.
2. **`metrics.yml` té 54 mètriques, no 70** (el 70 surt de comptar totes les claus del
   fitxer, no les del bloc `metrics:`).
3. **La Pobla: 1.106 hab.** al catàleg canònic (padró 2025); el 1.107 era l'arrodoniment
   del JSON de pernocta.
4. **~177 municipis <5.000 hab.** a la demarcació (recompte real sobre el padró 2025),
   no «180+».
5. **`docs/adr/` no existeix** — els ADRs viuen a `docs/architecture.md` §4 (i n'hi ha de
   superats: ADR-06, ADR-10). La cita queda corregida.
6. **Fronts**: el roster canònic és `docs/equip-com-treballem.md` (Talaia, Sondeig, Cabal,
   Brúixola, Mirador, Llegenda); Trazo opera de facto però formalitzar-la és tasca, no supòsit.

## Esmenes de disseny (§10 de l'spec, vinculants per als contractes)

- **E1 (C2)**: `publicable: false` dins d'un repo públic és públic de facto — els interns
  van al magatzem privat del workflow; C2 s'expressa dins de `data-sources.md` §0.
- **E2 (C4)**: nivells congelats DINS el contracte; recall del pipeline sencer; el banc
  mesura-no-entrena (també el filtre); guarda CONGELAT; idioma segons la font; passades
  declarades.
- **E3 (C5)**: l'annex #238 (posterior a la teva spec) va demostrar que la gàbia comptable
  sobreestima (170/170 vs 163/170 verificada) — la gàbia de producte RE-VALIDA i s'endú el
  validador v2.
- **E4–E6**: camp `visibilitat` a C1 · `config/` com a convenció nova a C3 · els pendents
  propis del geo-rag no els tapa aquesta spec.

Cap d'aquestes esmenes toca les teves decisions de producte (audiència, prioritats,
portes, no-objectius): totes queden com les vas escriure.

— Talaia (coordinació · guardiana de main)
