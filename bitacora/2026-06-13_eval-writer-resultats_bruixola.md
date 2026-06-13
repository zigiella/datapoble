# Eval del motor d'escriptura (§3): resultats i tria de model

**Fecha:** 2026-06-13
**Autora:** Brúixola (IA) — executat per Talaia, vot final de Bea
**Tema:** «petites proves amb diferents models» (Bea) per a l'escriptor de fitxes. 3 municipis (Gósol, Berga, Castellar de n'Hug) × 6 models, via OpenRouter a GitHub Actions (secret real). Verificador determinista + lectura humana del relat.
**Status:** fet (workflow run 27462993861) / decisió de model proposada, pendent vot Bea

## Resultats (3 munis × 6 models, 18 crides)

| Model | JSON vàlid | Xifres no verif.* | Llista negra | Cost/muni | Latència |
|---|---|---|---|---|---|
| **anthropic/claude-opus-4.8** | **3/3 ✓** | baix (0/4/2) | **0** | $0,066 | 27–30 s |
| anthropic/claude-opus-4.7 | 3/3 ✓ | baix (1/3/1) | **«perquè» ×2** | $0,065 | 28–30 s |
| anthropic/claude-sonnet-4.6 | 3/3 ✓ | mitjà (3/10/3) | 0 | $0,040 | 36–44 s |
| openai/gpt-5.5-pro | **0/3 ✗** | — | — | **$0,83** | 64–91 s |
| minimax/minimax-m3 | 0/3 ✗ | — | 1 | $0,006 | 95–119 s |
| deepseek/deepseek-v4-pro | 0/3 ✗ | — | — | $0,005 | 62–72 s |

*Xifres no verificades = senyal de confabulació (amb residual de falsos positius: '1000' del llindar micromunicipi, '100' d'un índex, '5' d'una paràfrasi). El relat es va llegir a mà per confirmar.

## Lectura

- **Els 3 models de raonament (gpt-5.5-pro, minimax-m3, deepseek-v4-pro) NO superen la porta de JSON** amb aquest harness simple: tornen `content` buit (raonament que es menja els tokens) o abocaments de raonament de 12–15 KB, no el JSON net. **Caveat honest:** part d'això pot ser del meu harness (no uso `response_format: json_object` ni gestiono la sortida de raonament); una prova justa caldria afegir-ho. Però gpt-5.5-pro a més és **el més car amb diferència** ($0,83/muni = ~$2,5 la prova; ~$2.300 per a 947 munis × 2 idiomes) per a un resultat fallit aquí.
- **Els 3 Claude van nets** amb el prompt simple. **`opus-4.8` és el millor:** JSON vàlid sempre, **0 hits de llista negra**, confabulació baixa, i un relat excel·lent — respecta els rangs («entre 198 i 242», «del 19% al 46%, punt mig 31%, no xifra tancada»), inclou la **contra-lectura** obligatòria de la divergència (93/100, confiança 33/100), i «treu suc» (el denominador per governar, la història de la divergència). `opus-4.7` és equivalent en qualitat però va fer servir «perquè» (causal, prohibit per la guia). `sonnet-4.6` és vàlid i més barat però confabula més (Berga: 10 xifres no verificades).

## Recomanació (Talaia)

**Escriptor = `anthropic/claude-opus-4.8`.** És el model potent que la Bea volia, i a més respecta les regles dures (un model més desfermat no ho faria). Cost a escala: ~$0,066/muni → **~$125 per a una regeneració completa de Catalunya** (947 × 2 idiomes), assumible perquè és en build, no en viu. **Fallback barat** si el cost importa: `sonnet-4.6` ($0,040) amb verificació més estricta. **NO gpt-5.5-pro** (car + poc fiable aquí).

Si la Bea vol donar una oportunitat justa als models de raonament: afegir `response_format` + gestió de la sortida de raonament i re-córrer. Però opus-4.8 ja ho clava net i barat.

## Pendiente
- [ ] **Vot de la Bea** sobre el model escriptor.
- [ ] Afinar el prompt/guia per matar el residual («perquè» a 4.7; falsos positius del verificador). 
- [ ] Construir el pipeline de generació EN BUILD (writer opus-4.8 → verificador determinista → fallback plantilla) per als 31 del Berguedà; després ca→es amb model barat.

## Enlaces
- `tools/eval_writer.py` · workflow `.github/workflows/eval-writer.yml` (run 27462993861) · guia `docs/guia-escriptura.md`
- sortides crues: artifact `eval-writer-outputs` (locals, no committejades)

— Brúixola
