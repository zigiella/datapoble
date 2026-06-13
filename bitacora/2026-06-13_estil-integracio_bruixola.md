# Integració de les regles d'estil a l'escriptor i al verificador

**Fecha:** 2026-06-13
**Autora:** Brúixola (IA) — executat per Talaia, input i vot de Bea
**Tema:** Bea aprova la guia d'escriptura i hi suma unes «regles d'estil agnòstiques» (18 regles, font consultoria a OneDrive/CAJON), amb llibertat per reduir-les i decidir on apliquen: al prompt o en una passada de pipeline.
**Status:** fet (codi validat offline) / handoff a Talaia per review

## Decisió: híbrid, sense tercera crida de model
- **Essència generativa → prompt de l'escriptor** (afirmar en positiu, densitat, verbs amb responsabilitat, ancorar abstraccions, nomenar l'autoritat). Configura *què es diu*.
- **Prohibicions mecàniques → verificador** (determinista, barat, auditable per diff, dispara re-intent). Una passada «de model d'estil» afegiria cost, latència i un altre punt de deriva de números. El traductor es queda estret (només tradueix).

## Tres friccions resoltes (estaven en tensió amb regles dures)
1. **«No X sinó Y» vs contra-lectura** — es prohibeix el contrast per inèrcia (guia al prompt), **no** com a porta dura, perquè la contra-lectura és un contrast necessari i no es pot caçar per regex sense fals positiu.
2. **«Redueix la cautela» vs «inferències en rang»** — resolt amb el camp `to`: `mesura` = frase directa (hedge prohibit), `inferencia` = rang obligatori (hedge esperat). El verificador ara és **conscient del `to`**: un hedge dins d'un claim `to:"mesura"` = falla; a `inferencia` no es toca.
3. **Guió llarg (—)** — prohibit al text de la fitxa (els rangs usen «–» o paraules). Els docs interns poden seguir usant-lo.

## Canvis
- `docs/estil-agnostic.md` — nou: 18 regles reduïdes a 10 + checklist + llista d'expressions, adaptades al projecte (es+ca).
- `docs/guia-escriptura.md` + `docs/guia-escritura-es.md` — nova secció **2.1 · Estil**, amb les tres resolucions cuites al text del prompt.
- `tools/gen_fitxa.py` — `BL_ES`/`BL_CA` ampliades (èpica, «genera valor», «canvi de paradigma», «transformació integral», «a nivell de»); detecció de «—»; **`HEDGE_ES`/`HEDGE_CA` + verificador conscient del `to`** (camp nou `hedge_mesura`, imprès al report).
- `tools/eval_writer.py` — `BLACKLIST` sincronitzada (mateix barem per a futures evals).

## Validació (offline, sense API)
`py_compile` OK als dos fitxers. Test unitari de `verify`: claim `mesura` amb «tendeix a» + «—» + «sens dubte» → `blacklist=['sens dubte','—']`, `hedge_mesura=['tendeix a']`; el «potser» d'un claim `inferencia` **no** es marca. Confirma F2 i F1.

## Pendiente
- [ ] **Talaia:** review/merge.
- [ ] **Prova viva** (workflow_dispatch `gen-fitxa.yml`, 3 munis) per veure l'estil en sortida real i confirmar que opus-4.8 + sonnet-4.6 respecten les regles noves sense disparar re-intents en cascada.
- [ ] Integrar `hedge_mesura` (≠ buit) com a condició de re-intent al pipeline EN BUILD, al costat de `blacklist`.

## Enlaces
- `docs/estil-agnostic.md` · `docs/guia-escriptura.md` §2.1 · `docs/guia-escritura-es.md` §2.1
- `tools/gen_fitxa.py` (verify conscient del `to`) · `tools/eval_writer.py`
- previ: `bitacora/2026-06-13_gen-fitxa-pipeline_bruixola.md` (pipeline validat)

— Brúixola
