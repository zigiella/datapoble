# Contracte d'abast — datapoble

**Què es mostra, i on.** Document canònic d'una pàgina (Fase 0 de la [reconducció](dossier-consultoria-2026-06/01-reconduccio.md)).
Quan dubtem on va un indicador, mana aquesta taula. *Saber tallar és el senyal de criteri.*

## La regla

> Al **mapa públic de Catalunya** només entra el que aguanta **sense llegenda defensiva**. La llegenda
> matisa, mai es disculpa. Si un indicador necessita un paràgraf demanant perdó per no enganyar, **no
> entra**: baixa a la vitrina Berguedà o a context de fitxa.

Quatre destinacions:
- **Mapa públic CAT** — el cop d'ull a tot el país. Pocs indicadors, tots blindats.
- **Vitrina Berguedà** — el nucli validat (vegeu «Validació», la frase canònica): hi cap el detall que no generalitza.
- **Fitxa de municipi** — context per poble (es llegeix amb el municipi al davant, no en abstracte).
- **Fora** — el que no s'entén com a mapa; pot reconvertir-se en senyal intern.

## La taula

| Indicador | On viu | Per què | Estat |
|---|---|---|---|
| **Gent que el padró no veu** (gap) | Mapa públic CAT · reenquadrat com a hipòtesi | L'estrella. ≥1.000 hab = ETCA oficial (Idescat); <1.000 = estimació experimental nostra, amb la **costura visible** | Mapa ✅ · costura ⏳ (Fase 1) |
| **% habitatge no principal** | Mapa públic CAT | Oficial, llegible d'un cop d'ull, directe | ✅ |
| **Residus** (kg/hab/any) | Mapa públic CAT · amb caveat | Mesura directa (ARC); segon pilar | ✅ |
| **Densitat de població** | Fitxa (tornarà al mapa amb **escala log**) | Barcelona domina l'escala lineal | Fora del mapa ✅ · log ⏳ |
| **Renda neta per persona** | Fitxa | Aporta poc al conjunt del mapa; distreu | Fora del mapa ✅ |
| **IETR** (exposició) | Berguedà / fitxa | No s'entén a escala Catalunya | Fora del mapa ✅ |
| **Tipologia d'habitança** | Només Berguedà | Els llindars no generalitzen (Barcelona=excursió) | Fora del mapa CAT ✅ |
| **Pressió turística** | Berguedà / fora | El proxy no capta la gran ciutat | Fora del mapa ✅ |
| **Càrrega per residus** | Fitxa interna / fora | Es confon amb el gap; difícil d'explicar | Fora del mapa ✅ |
| **Densitat de restauració** (OSM) | Fitxa · amb caveat | OSM infra-mapa el rural: mínim observat, no cens | Fora del mapa ✅ |
| **Contradiccions de senyals** | Fora → bandera interna de confiança | No s'entén com a mapa públic | Fora del mapa ✅ |
| **Política** | Fora de tot el web | Decisió de direcció (vegeu nota) | ⏳ (PRs en curs) |

## Resultat per superfície

- **Mapa públic CAT (3):** gap (reenquadrat) · % habitatge no principal · residus.
- **Vitrina Berguedà:** el detall (tipologia, IETR, pressió…), narrat; validat contra ETCA als 9 munis grans (vegeu «Validació»).
- **Fitxa:** context (densitat, renda, restauració, IETR…), cadascun amb procedència i caveat.
- **Fora:** contradiccions (→ senyal intern de confiança) · política.

## La costura del gap (pendent de Fase 1)

El gap del mapa públic **cosirà dues capes amb nom propi**, no una de sola:
- **≥1.000 hab → ETCA oficial d'Idescat** (vinculació, net anual en equivalent-a-temps-complet).
- **<1.000 hab → la nostra estimació experimental de pernocta** (residu elèctric, en rang).

Són **magnituds diferents** (font *i* significat): la costura s'**etiqueta**, no es fon. Fer-la visible
és la declaració de portafolio («l'observatori que sap el que no sap»), no un pegat. Vegeu
[reconducció §1–§2](dossier-consultoria-2026-06/01-reconduccio.md).

## Nota sobre la política

Treure la pestanya **no despolititza** per si sol: el padró mou finançament, pes electoral i
dimensionament de serveis, i una eina que diu «aquí dorm un X% més de gent de la que consta» és
munició. La postura ha de ser **deliberada**, amb una **nota de mètode** sobre usos i límits del gap
(decisió de direcció, pendent). El que sí és ferm: cap contingut polític es mostra al web.

---
## Validació (frase canònica)

*Frase ÚNICA de validació. Tota referència a «validat» (web, dossier, metodologia, cua) hi apunta;
no es repeteix a mà —una font, no dotze còpies que es contradiran.*

> La pernocta està validada contra l'ETCA d'Idescat als **9 municipis del Berguedà de ≥1.000 hab**
> (ρ=0,967; error medià 8,2%, **dins de mostra**). Als **22 municipis petits no hi ha ETCA**:
> l'estimació no té validació oficial, i és on l'error creix. La **generalització** del model és la
> cobertura de la banda **fora de mostra** (interval nominal del 80% → 78,4% empíric), no el 8,2%.

Curta (peus i tooltips): «Validat contra l'ETCA als 9 munis grans del Berguedà; als 22 petits,
estimació sense validació oficial. Generalització: banda 80%→78,4% fora de mostra.»

Al web, la font és el missatge i18n **`met_valid_canon`** / **`met_valid_canon_curt`** (ca+es). El que
NO canvia: cap número ni cap càlcul; la banda ×1,5 dels micromunicipis sense validar es manté, ara ben
etiquetada com el que és —estimació sense validació oficial.

---

*Deriva de la reconducció (rumbo 2026-06-27). Si canvia, s'actualitza aquí primer.*
