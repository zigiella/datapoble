# Cua — reconducció (rumbo decidit 2026-06-27)

*Mètode: **Cambium Charter v0.5**. Es treballa de dalt a baix; cada tasca = un PR. Cada **fase** és
publicable per si sola.*

> **🧭 RUMBO DECIDIT (2026-06-27).** Després de l'arc «fer-ho bé» (dada honesta a tot CAT) i del dossier
> de consultoria, la **consultoria externa** ha reconduït el projecte. Decisió a
> `docs/dossier-consultoria-2026-06/01-reconduccio.md`. Concepte: **«l'observatori que sap el que no
> sap»** (Berguedà = nucli validat · Catalunya = context honest i curat, amb la **costura visible**
> entre Idescat ≥1.000 hab i la nostra estimació <1.000). **El gap és el ganxo; l'epistemologia és el
> producte.** Es treballa per **fases (0→5)**. **No s'executa cap fase fins que Bea en doni el tret de
> sortida.** Criteri de parada: si només dues, **Fase 1 + Fase 2**.

> **Vot de Bea pendent** (no el tanca Talaia): enquadrament del *gap* com a hipòtesi (còpia) ·
> postura política explícita + nota de mètode · portar (o no) el doc verbatim de la consultoria al
> repo · per quina fase comencem (recomanat: **Fase 0**). Detall a §7 de la reconducció.

---

## Fase 0 · congelar abast i matar el que trenca · *demostra criteri*
- [ ] Treure del **mapa públic CAT**: tipologia, pressió turística, IETR, contradiccions, restauració.
- [ ] Reubicar cada una a **Berguedà** o a **context de fitxa** (segons el contracte d'abast, §4).
- [ ] Treure **política** de **totes** les pàgines + **nota de mètode** amb postura deliberada.
- [ ] Escriure el **contracte d'abast** en una pàgina (què es mostra on).
- [ ] Decidir l'**enquadrament del *gap*** (registre d'**hipòtesi**, no de veredicte) — *vot de Bea*.

## Fase 1 · el nucli epistèmic · *el 70% del valor*
- [ ] Produir **intervals predictius reals** i comprovar-ne la **calibració**.
- [ ] **Reliability diagram** + taula de **cobertura empírica del p10–p90** en held-out.
- [ ] **Refer la banda** si la cobertura no coincideix amb el que promet.
- [ ] **Cosir la capa CAT**: ETCA oficial (Idescat) a ≥1.000 hab · estimació pròpia només a <1.000
      (marcada experimental) · **costura visible** + **doble etiqueta** (font + significat: ETCA = net
      anual ETC ≠ la nostra pernocta).
- [ ] Verificar que **Barcelona i les ciutats denses les parla Idescat** (desapareix el negatiu absurd).
- [ ] Documentar el **supòsit causal i els confusors** del residu (R²=0,41) a la metodologia.

## Fase 2 · la vitrina Berguedà · *rigor de punta a punta*
- [ ] 31 munis, dades completes, model validat i ben narrat.
- [ ] Pàgina de **metodologia auditable** amb gràfics de validació.
- [ ] Error per **tipus territorial** i límits declarats (inclòs que **ETCA també és estimació**).

## Fase 3 · la capa Catalunya honesta · *saber quan NO ensenyar*
- [ ] Mapa públic amb **% habitatge no principal** + el **present-vs-padró cosit**.
- [ ] **Escala log** on la densitat ho demani.
- [ ] Llegenda que **matisa, no que es disculpa**.

## Fase 4 · la fitxa i la home · *producte per a consum humà*
- [ ] Fitxa amb **jerarquia dura**: el *gap* i la seva incertesa, protagonista; la resta col·lapsada.
- [ ] Treure de la vista per defecte la «**maquinària**» crua.
- [ ] Home: **mapa comarcal agregat + cercador**, amb el **waveform del *gap*** com a peça-firma.
- [ ] Etiquetar «**el bessó del teu poble**» com a experimental o validar la mètrica de distància.
- *(Absorbeix el brief de fitxa §5 i la nav/UI §6 del dossier: canvas vertical, zoom CAT, treure menú
  sobrant, Resum→Comarca.)*

## Fase 5 · la capa d'IA honesta · *opcional, el «no» com a funcionalitat* · **(IA)**
- [ ] «Pregunta-li» com a **text-to-SQL acotat al Berguedà**, amb traça (font + consulta SQL).
- [ ] Que **es negui** quan la pregunta surt del catàleg.
- [ ] Corregir el cas trencat («té més població Lleida que Girona?» → respon «Barcelona»).

---

## Transversal / llançament (quan el nucli aguanti)
- **Ops de llançament** (Talaia+Mirador): treure noindex ×3 (`app.html`, `robots.txt`, `_headers`);
  `og:image`; deploy verd al domini; comprovació final. *(El sitemap ja hi és, #150.)*
- **a11y AA** (Llegenda+Mirador): teclat al mapa, contrast, `axe-core` a CI.
- **Llengües** aranès + anglès (Brúixola+Talaia) **(IA)**: repàs còpia ca/es → Apertium/AINA (oc) + en.
- **Viz pendents** (Mirador): Dorling, slider, embedding 2D de secció (PCA/MDS), dades obertes (/dades,
  xifra citable, embeds, kit premsa). *Subordinades al nucli; entren si sumen.*

---

## Històric — arc «fer-ho bé» (F1–F5) + llançament P0/P1 · **FET** (a `main`)
*Detall a la bitàcola i als PR; aquí només el resum perquè la cua viva sigui la reconducció.*
- **P0/P1 llançament** (juny 2026): Nivell C a tot CAT (#152) · cercador 947 (#146) · prerender 947
  (#146) · licitacions «en construcció» (#147) · missatge d'abast (#148) · sitemap (#150) · espina +
  comarca/vegueria (#151,#158) · beeswarm/constel·lació del gap (#155,#157).
- **Arc «fer-ho bé» (F1–F5)** (`docs/pla-catalunya-profund.md`): dataset profund estès als 947 amb
  model unificat i honest; els **11 indicadors es pintaven a tot CAT**; fitxes uniformes; **guardó ETCA
  Berguedà 8,2%/ρ=0,967** preservat. PRs #161–#179. Dossier de consultoria #181.
- **⚠️ La reconducció REENQUADRA tot això:** dels 11 indicadors, el mapa públic CAT en conserva
  ~**3** (gap reenquadrat + %no-principal + residus); la resta baixa a Berguedà o fitxa (§4). No és
  feina perduda: és la matèria primera que ara es **cura**.

## Diferit a Fase 2 (del projecte, no del pla)
Licitacions de veritat (menors → majors/diputació) · fonts noves.
