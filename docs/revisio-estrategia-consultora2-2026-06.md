# Revisió de l'estratègia (consultora 2) — gap-analysis · 2026-06-14

*Talaia, per decidir amb Bea. Contrasta l'spec `riusdegent-especificación.md` (v2, 13 seccions) amb
l'estat real del producte. Veredicte: **l'estratègia es manté i l'estem executant**; la deriva és
mínima. Falten DOS nuclis grans (lectures de fitxa §3 i bases Nivell C / Catalunya §2) i un grapat de
peces de l'spec que NO són als teus 7 fronts (cal decidir si entren al llançament o a Fase 2).*

## 0 · Progrés des d'aquesta revisió (2026-06-15/16)

Dos nuclis grans avançats + el mapa multinivell:

- **§3 · Fitxa-IA · lectures — FET i EN VIU** (#125-129). Generades les lectures dels 31 munis
  (escriptor opus-4.8 es → traductor sonnet-4.6 ca, verificador de xifres; 31/31 del model, 0
  reserves després del fix del verificador) i servides a la fitxa: veredicte (P1), lectures per
  perfil (ciutadania/visitant) amb naturalesa+evidència, contra-lectura i preguntes → Pregunta-li.
  El toggle de perfils es va passar a **CSS pur** (el de $state no commutava).
- **§4/§2 · Nivell C — MODEL VALIDAT (carril dades, en silenci)** (#130-136). De «la base única
  del Berguedà no encaixa» a un model robust: `base elèctrica/persona ~ log10(densitat) + renda`
  (INE ADRH 2023), **R²=0,60, 77% dins ±15%, held-out = in-sample (no sobreajust)**. Document
  d'analista viu `docs/analisi-escala-nivellc.md`. **Encara NO publicat** (cal ~≥85% per a xifra
  absoluta; la banda ±15% ja és publicable com a rang). Geometria de vegueries derivada (#134).
- **§10/§5 · Mapa multinivell — FET** (#137). Commutador comarca/vegueria/municipi als dos mapes
  amb **cobertura honesta** (Berguedà completes · Comarques Centrals parcials · resta sense dades);
  home per defecte comarca. *Pendent: confirmació visual de Bea en navegador real.*

## 1 · On som vs l'ordre d'execució de l'spec (§13)

| §13 | Peça | Estat | Evidència |
|---|---|---|---|
| 0 | Accessibilitat AA + alternativa en taula + confiança visual | 🟡 parcial | «veure com a taula» (#97) ✅; **axe-core CI + teclat (mapa/slider/scatter) ⬜** |
| 1 | Prerender/SSR + URLs slug + sitemap + hreflang | ✅ **fet** | slug #98 · /ca+SEO+sitemap+hreflang #120 |
| 2 | Renoms semàntics + taula de còpies §1.4 | ✅ majoritari | Pas 2 #94-95 (IETR→Exposició, capacitat/impacte, «gent que el padró no veu») · **revisió de còpies ⬜ (front teu)** |
| 3 | **Fitxa P1/P2 + lectures pre-generades + xifra citable + emblema doble corrent** | ✅ **lectures fetes** | veredicte+lectures+preguntes en viu #125-129; 5 números (P2) #124. Pendent: **xifra citable ⬜ · doble corrent ⬜** |
| 4 | **Bases per tipus + validació triple + règims (Barcelonès intern)** | 🟡 **Nivell C VALIDAT, no publicat** | Nivell B #103 · ETCA #100-102 · **Nivell C regressió densitat+renda R²0,60, held-out OK #130-136** ✅ (carril en silenci). Pendent: ≥85% (gas/calefacció) → **publicar** · règims com a camp+evals ⬜ |
| 5 | Home nova + espina + breadcrumb | 🟡 **home + mapa multinivell, espina no** | Home «La Llera» #119 · mapa default comarca #137 ✅ (frase-mare ⬜, hallazgos≈troballes 🟡) · **espina/breadcrumb ⬜** |
| 6 | Dorling-fantasma + slider + el riu + beeswarm + pols | ⬜ pendent | (el «wow», va després de la base sana) |
| 7 | Embeds + pàgines de dada + kit de premsa (§9) | ⬜ pendent | dades obertes/descàrrega/cita ⬜ |
| 8 | Catàleg de components + HUD genUI + resposta-com-UI a Pregunta-li | ⬜ pendent | **= el teu «segon pregunta-li (super beta)»** |
| 9 | `oc-aranés` + `en` | ⬜ pendent (ara amb recursos) | SOP + scripts Apertium/AINA rebuts · terreny /ca obert #120 |
| 10 | Tarragonès públic → resta de Catalunya | 🟡 **mapa multinivell + Nivell C validat** | mapa comarca/vegueria/municipi #137 · Nivell C N=91 (Berguedà+Barcelonès+Tarragonès+Baix Llobregat+Maresme) #130-136. Pendent: publicar (go/no-go) |

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
1. ✅ **Caveat Licitacions «només menors»** (#123) · 🟡 alinear troballes amb els 4 *hallazgos* (rècord honest fet; falta contrast/nul honest/contradicció).
2. ✅ **Fitxa-IA · lectures** (§3) — generades i servides per als 31 (#125-129).
3. 🟡 **Bases Nivell C + Catalunya incremental** (§2/§11) — **MODEL VALIDAT** (densitat+renda, R²0,60, held-out; #130-136), carril en silenci. **SEGÜENT:** (a) 1-2 covariables més (gas/calefacció, grandària llar) per creuar el go/no-go (~≥85%) → (b) **publicar** rangs/xifra a la fitxa i al mapa, comarca a comarca; (c) replicar per residus (L2); (d) completar llistes del classificador.
   - En paral·lel: ⬜ **confirmació visual del mapa multinivell** (Bea) · ⬜ frase-mare a la home.
4. **Pàgines de comarca + millorar /resum** (§5) — depèn de 3.
5. **3 profunditats a cada pàgina + test CI** (§1) · **accessibilitat AA / axe-core / teclat** (§13.0).
6. **Espina territorial + breadcrumb** (§7) — al llançament.
7. **Dades obertes + xifra citable + embeds + kit premsa** (§9) — al llançament.
8. **Visualitzacions noves** (§4): Dorling-fantasma, slider, «el riu», beeswarm, emblema doble corrent — al llançament. *(el commutador de granularitat del mapa, #137, ja és un primer pas de viz territorial.)*
9. **Pregunta-li: millorar + segon «super beta»** (genUI/resposta-com-UI, §7.3).
10. **Revisió de còpies** (§1.4) → abans de traduir.
11. **Llengües: aranés (AINA) + anglès** (§1.5/§13.9).
12. **DA externa** (poliment).
13. **Llançament**: treure noindex · og:image.

**Diferit a Fase 2:** Licitacions majors/diputació · **fonts noves §12** (INE-mòbils, VUT plataformes, autocaravanes; tret del mínim per a Nivell C) · genUI HUD complet.

---
*Actualitzat 2026-06-16 (Talaia): vegeu §0 per al progrés recent i `docs/analisi-escala-nivellc.md` per al detall del Nivell C.*

---
*Convicció de l'spec que adopto com a filtre: «si una peça no pot explicar d'on surt, no es publica». El mètode és el producte també a la UI.*
