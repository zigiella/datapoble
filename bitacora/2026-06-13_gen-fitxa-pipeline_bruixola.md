# Pipeline de fitxa (es→ca): resultat de la prova

**Fecha:** 2026-06-13
**Autora:** Brúixola (IA) — executat per Talaia, decisió Bea
**Tema:** prova del pipeline de generació amb la configuració de la Bea: **escriptor opus-4.8 en castellà → traductor sonnet-4.6 al català**, amb re-chequeo de números. 3 munis (Gósol, Berga, Castellar), workflow run 27463988060.
**Status:** fet, VALIDAT / handoff

## Resultat

| Municipi | Escriptor opus-4.8 (es) | Traductor sonnet-4.6 (ca) |
|---|---|---|
| Gósol | json ✓ · 0 falten · contra ✓ · 0 negra · 26s | json ✓ · **números preservats** · 0 negra · 22s |
| Berga | json ✓ · contra ✓ · 0 negra · 22s | json ✓ · **números preservats** · 0 negra · 18s |
| Castellar | json ✓ · contra ✓ · **negra: «porque»** · 24s | json ✓ · **números preservats** · negra: «perquè» · 17s |

**Conclusions:**
- **El pipeline funciona.** JSON vàlid a les dues etapes; **els números es preserven al 100%** en la traducció (3/3) — el re-chequeo determinista ho confirma.
- **El català de sonnet-4.6 és excel·lent**: natural i fluid, esquema i `evidencia` intactes, rangs respectats («entre 198 i 242, punt mig 218», «del 19% al 46%»), contra-lectura completa. L'estratègia de la Bea (model potent escriu en es → model barat tradueix a ca) queda **validada**.
- **Únic defecte:** opus-4.8 va fer servir «porque» (causal) a Castellar; la traducció el va mantenir («perquè»). El verificador ho caça → al pipeline real dispararia un re-intent (regla §3.2). És un toc de prompt, no un problema de fons. *(Nota: el «perquè» d'aquí —«xifra inflada perquè el denominador no recull…»— és explicatiu/metodològic, no una atribució de conducta; potser cal afinar la regla perquè no sigui un fals positiu.)*

## Cost i latència
opus-4.8 (es) ~$0,066/muni, 22–26s · sonnet-4.6 (ca) ~$0,02/muni, 17–22s. Total pipeline ~$0,09/muni → **~$85 per als 947 munis** (es+ca), en build. Assumible.

## Pendiente
- [ ] **Talaia:** review/merge (evidència).
- [ ] **Pipeline EN BUILD** per als 31 del Berguedà: writer→verificador→(re-intent si falla)→traductor→verificador→fallback plantilla; versionar el JSON per municipi (ca+es) al repo i servir-lo a la fitxa.
- [ ] Afinar la regla anti-causal (distingir «perquè» explicatiu-metodològic de «perquè» de conducta) per reduir falsos positius / re-intents.

## Enlaces
- `tools/gen_fitxa.py` · `docs/guia-escritura-es.md` · workflow `gen-fitxa.yml` (run 27463988060)
- eval previ: `bitacora/2026-06-13_eval-writer-resultats_bruixola.md` (opus-4.8 guanyador)

— Brúixola
