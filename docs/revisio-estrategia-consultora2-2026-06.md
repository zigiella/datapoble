# Revisió de l'estratègia (consultora 2) — gap-analysis · 2026-06-14

*Talaia, per decidir amb Bea. Contrasta l'spec `riusdegent-especificación.md` (v2, 13 seccions) amb
l'estat real del producte. Veredicte: **l'estratègia es manté i l'estem executant**; la deriva és
mínima. Falten DOS nuclis grans (lectures de fitxa §3 i bases Nivell C / Catalunya §2) i un grapat de
peces de l'spec que NO són als teus 7 fronts (cal decidir si entren al llançament o a Fase 2).*

## 1 · On som vs l'ordre d'execució de l'spec (§13)

| §13 | Peça | Estat | Evidència |
|---|---|---|---|
| 0 | Accessibilitat AA + alternativa en taula + confiança visual | 🟡 parcial | «veure com a taula» (#97) ✅; **axe-core CI + teclat (mapa/slider/scatter) ⬜** |
| 1 | Prerender/SSR + URLs slug + sitemap + hreflang | ✅ **fet** | slug #98 · /ca+SEO+sitemap+hreflang #120 |
| 2 | Renoms semàntics + taula de còpies §1.4 | ✅ majoritari | Pas 2 #94-95 (IETR→Exposició, capacitat/impacte, «gent que el padró no veu») · **revisió de còpies ⬜ (front teu)** |
| 3 | **Fitxa P1/P2 + lectures pre-generades + xifra citable + emblema doble corrent** | 🟡 **motor llest, no servit** | pipeline validat #108-114; la fitxa avui és NOMÉS P3 (blocs de dada). Lectures/veredicte/5 números/preguntes ⬜ · xifra citable ⬜ · doble corrent ⬜ |
| 4 | **Bases per tipus + validació triple + règims (Barcelonès intern)** | 🟡 **Nivell B fet, C no** | Nivell B `tipus_territorial` #103 ✅ · ETCA validació Berguedà #100-102 ✅ · **Nivell C (esperats per regressió + calibratge coef) ⬜** · règims a la guia ✅, com a camp+evals ⬜ |
| 5 | Home nova + espina + breadcrumb | 🟡 **home feta, espina no** | Home «La Llera» #119 ✅ (frase-mare ⬜, hallazgos≈troballes 🟡) · **espina/breadcrumb territorial ⬜** |
| 6 | Dorling-fantasma + slider + el riu + beeswarm + pols | ⬜ pendent | (el «wow», va després de la base sana) |
| 7 | Embeds + pàgines de dada + kit de premsa (§9) | ⬜ pendent | dades obertes/descàrrega/cita ⬜ |
| 8 | Catàleg de components + HUD genUI + resposta-com-UI a Pregunta-li | ⬜ pendent | **= el teu «segon pregunta-li (super beta)»** |
| 9 | `oc-aranés` + `en` | ⬜ pendent (ara amb recursos) | SOP + scripts Apertium/AINA rebuts · terreny /ca obert #120 |
| 10 | Tarragonès públic → resta de Catalunya | 🟡 stress-test fet #107 | càrrega incremental (Barcelonès+Salou) decidida |

**Licitacions** (els dos pilars): Fase 1 viva #118; majors/diputació → Fase 2 (decidit).

## 2 · Lectura: la deriva és mínima

- **§13.1 i §13.2 ja són fets** (slug, /ca, SEO, renoms). Anàvem ben encaminats.
- **El nucli que falta són §13.3 (lectures de fitxa) i §13.4 (Nivell C / Catalunya)** — exactament els teus «Fitxa-IA» i «tota Catalunya». No és deriva: és el gruix de valor encara per construir.
- **La Home (#119) es va fer abans que les lectures (§13 la posa al pas 5, després del 3).** No és problema —la home funciona— però enllaça a fitxes que encara no tenen lectures: per això **les lectures són el següent nucli natural**.

## 3 · Divergències i decisions (què ha canviat o cal triar)

1. **Home: cercador-primer vs frase-mare.** L'spec §6 vol la **frase-mare** («El padró diu qui consta…») d'heroi amb el cercador a sota; tu vas triar «La Llera» (cercador d'heroi, H1 = «Quin poble vols entendre?»). Compatible: es pot **afegir la frase-mare** sobre/sota el cercador sense perdre el cercador-primer. *Decisió menor.*
2. **Troballes ≠ els 4 hallazgos de l'spec.** Tinc gap/ietr/div/lic; l'spec vol **rècord honest · contrast (el duel) · nul honest · contradicció**. Val la pena alinear-ho (sobretot «nul honest», que és identitat de marca). *Refinament.*
3. **Accessibilitat (§13.0) la posa l'spec PRIMER** («barata d'inici, caríssima a posteriori»): **axe-core a CI + teclat al mapa/scatter**. Avui no hi és. Recomano colar-la aviat. *Decisió.*
4. **Test CI de les 3 profunditats** (§1.1: script que falla si surt jerga «above the fold») — operativitza el teu front «3 nivells a cada pàgina». *Adoptar.*
5. **Peces de l'spec que NO eren als 7 fronts → DECISIÓ (Bea, 2026-06-14):**
   - ✅ **AL LLANÇAMENT — Dades obertes de veritat (§9):** /dades, descàrrega CSV/JSON/Parquet/SQLite, **xifra citable** (cada número una URL), embeds, kit de premsa.
   - ✅ **AL LLANÇAMENT — Visualitzacions noves (§4):** Dorling-fantasma, slider de denominador, «el riu», beeswarm, **emblema doble corrent**, glif balança.
   - ✅ **AL LLANÇAMENT — Espina territorial + breadcrumb (§7).**
   - ⏭️ **A FASE 2 — Fonts noves (§12):** INE-mòbils, VUT plataformes, Càtedra TIM (tret del que calgui mínimament per a Nivell C).

## 4 · Ordre reconciliat (CONFIRMAT amb Bea, 2026-06-14)

0. **Aquesta revisió** ✅.
1. **Caveat Licitacions «només menors»** (quick) · alinear troballes amb els 4 *hallazgos* (rècord honest · contrast · nul honest · contradicció).
2. **Fitxa-IA · lectures** (§3): generar+servir veredicte + 5 números + 4 lectures + preguntes per als 31. **← SEGÜENT NUCLI (decidit).**
3. **Bases Nivell C + Catalunya incremental** (§2/§11): Barcelonès intern + Salou/Tarragonès, go/no-go, càrrega «poc a poc verificant». **Pal de paller.**
4. **Pàgines de comarca + millorar /resum** (§5) — depèn de 3.
5. **3 profunditats a cada pàgina + test CI** (§1) · **accessibilitat AA / axe-core / teclat** (§13.0, l'spec la vol aviat).
6. **Espina territorial + breadcrumb** (§7) — al llançament.
7. **Dades obertes + xifra citable + embeds + kit premsa** (§9) — al llançament.
8. **Visualitzacions noves** (§4): Dorling-fantasma, slider, «el riu», beeswarm, emblema doble corrent — al llançament.
9. **Pregunta-li: millorar + segon «super beta»** (genUI/resposta-com-UI, §7.3).
10. **Revisió de còpies** (§1.4) → abans de traduir.
11. **Llengües: aranés (Apertium/AINA) + anglès** (§1.5/§13.9).
12. **DA externa** (poliment).
13. **Llançament**: treure noindex · og:image.

**Diferit a Fase 2:** Licitacions majors/diputació · **fonts noves §12** (INE-mòbils, VUT plataformes, autocaravanes; tret del mínim per a Nivell C) · genUI HUD complet.

---
*Convicció de l'spec que adopto com a filtre: «si una peça no pot explicar d'on surt, no es publica». El mètode és el producte també a la UI.*
