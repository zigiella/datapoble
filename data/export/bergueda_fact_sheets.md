# Fulls de fets — Berguedà (per a la interpretació, #65)

*El digest EXACTE que llegiria el model d'interpretació. Enganxa'n un al prompt d'escriptor i itera.*
*Tot surt de la dada real; les 3 capes i els gaps són inferència (no cens). `origen` queda fora de la v1.*

---

## Full de fets · COMARCA (Berguedà)

Municipis: 31 · població total 41.523 hab · població mediana 260 hab
DISTRIBUCIÓ DE TIPOLOGIES: indeterminat 16 · capital_serveis 5 · segona_residencia 5 · excursio 2 · buit_administratiu 2 · dormitori_invisible 1
MÉS EXPOSATS (IETR): Castellar de n'Hug 89,4 · Sant Jaume de Frontanyà 85,5 · Gisclareny 82,2
CAPITALS DE SERVEIS: Avià, Bagà, Berga, Gironella, Puig-reig
IETR mitjà comarcal: 38,9
CAVEATS: z-scores i índexs són COMARCALS (no comparables entre comarques). Tot inferència sobre senyals físics.

---

## Fulls de fets · MUNICIPIS

### Castellar de n'Hug  ·  INE 08052  ·  Berguedà
Població (padró): 166 hab

TIPOLOGIA: «excursio» — Turisme d'excursió (de dia): vénen, gasten i marxen; deixen residus i ampolles, no llum de casa.
  Confiança: alta (score 32,8/100)

MODEL DE 3 CAPES — INFERÈNCIA (no cens; es llegeix com a rang):
  · L1 pernocta (qui DORM aquí, via elèctric domèstic): ~218 hab · gap +31% sobre el padró
  · L2 càrrega total (inclou excursionistes de dia, via residus): ~397 hab
  · L3 pressió turística (via vidre; 0–100, RELATIU a la comarca, 50 = mitjana): 83,5
IETR (exposició turística-residencial): 89,4 · #1 de 31 · stock 100 / impact 78,9

SENYALS FÍSICS (mesura):
  · elèctric domèstic 1607,6 kWh/hab · residus 980,4 kg/hab · vidre 107,7 kg/hab
  · restauració 3 locals · comerç+serveis 4 establiments  (OSM = mínim observat, no cens)
TURISME REGLAT: 30 establiments (180,7 per 1000 hab)
HABITATGE: 74,3% no principal · índex d'envelliment 466,7

CONTEXT COMARCAL: població mediana 260 hab · IETR mitjà 38,9 · el Berguedà és rural i envellit, amb un extrem turístic (Gósol, Castellar, Saldes) i una capital de serveis (Berga).
CAVEATS: les 3 capes i els gaps són INFERÈNCIA. Inferència sobre senyals físics, no cens.
[Composició d'origen/arrelament: capa SENSIBLE, FORA de la interpretació v1 (vegeu el CSV/SQLite si la vols consultar a banda).]

### Sant Jaume de Frontanyà  ·  INE 08216  ·  Berguedà
Població (padró): 25 hab

TIPOLOGIA: «segona_residencia» — Turisme de pernocta: molts llits (2a residència) que s'omplen caps de setmana i ponts.
  Confiança: baixa (score 38,8/100)

MODEL DE 3 CAPES — INFERÈNCIA (no cens; es llegeix com a rang):
  · L1 pernocta (qui DORM aquí, via elèctric domèstic): ~47 hab · gap +88% sobre el padró
  · L2 càrrega total (inclou excursionistes de dia, via residus): ~69 hab
  · L3 pressió turística (via vidre; 0–100, RELATIU a la comarca, 50 = mitjana): 35,1
IETR (exposició turística-residencial): 85,5 · #2 de 31 · stock 86,4 / impact 84,5

SENYALS FÍSICS (mesura):
  · elèctric domèstic 2285,6 kWh/hab · residus 1132,5 kg/hab · vidre 39,6 kg/hab
  · restauració 0 locals · comerç+serveis 1 establiments  (OSM = mínim observat, no cens)
TURISME REGLAT: 5 establiments (200 per 1000 hab)
HABITATGE: 56,4% no principal · índex d'envelliment 350

CONTEXT COMARCAL: població mediana 260 hab · IETR mitjà 38,9 · el Berguedà és rural i envellit, amb un extrem turístic (Gósol, Castellar, Saldes) i una capital de serveis (Berga).
CAVEATS: les 3 capes i els gaps són INFERÈNCIA. Confiança baixa: senyals que divergeixen o padró petit → llegeix-ho amb prudència.
[Composició d'origen/arrelament: capa SENSIBLE, FORA de la interpretació v1 (vegeu el CSV/SQLite si la vols consultar a banda).]

### Gisclareny  ·  INE 08093  ·  Berguedà
Població (padró): 28 hab

TIPOLOGIA: «segona_residencia» — Turisme de pernocta: molts llits (2a residència) que s'omplen caps de setmana i ponts.
  Confiança: baixa (score 42,8/100)

MODEL DE 3 CAPES — INFERÈNCIA (no cens; es llegeix com a rang):
  · L1 pernocta (qui DORM aquí, via elèctric domèstic): ~55 hab · gap +96% sobre el padró
  · L2 càrrega total (inclou excursionistes de dia, via residus): ~71 hab
  · L3 pressió turística (via vidre; 0–100, RELATIU a la comarca, 50 = mitjana): 100
IETR (exposició turística-residencial): 82,2 · #3 de 31 · stock 96,1 / impact 68,3

SENYALS FÍSICS (mesura):
  · elèctric domèstic 2395,1 kWh/hab · residus 1038,9 kg/hab · vidre 144 kg/hab
  · restauració 1 locals · comerç+serveis 1 establiments  (OSM = mínim observat, no cens)
TURISME REGLAT: 4 establiments (142,9 per 1000 hab)
HABITATGE: 65,1% no principal · índex d'envelliment 650

CONTEXT COMARCAL: població mediana 260 hab · IETR mitjà 38,9 · el Berguedà és rural i envellit, amb un extrem turístic (Gósol, Castellar, Saldes) i una capital de serveis (Berga).
CAVEATS: les 3 capes i els gaps són INFERÈNCIA. Confiança baixa: senyals que divergeixen o padró petit → llegeix-ho amb prudència.
[Composició d'origen/arrelament: capa SENSIBLE, FORA de la interpretació v1 (vegeu el CSV/SQLite si la vols consultar a banda).]

### Gósol  ·  INE 25100  ·  Berguedà
Població (padró): 207 hab

TIPOLOGIA: «segona_residencia» — Turisme de pernocta: molts llits (2a residència) que s'omplen caps de setmana i ponts.
  Confiança: alta (score 61,8/100)

MODEL DE 3 CAPES — INFERÈNCIA (no cens; es llegeix com a rang):
  · L1 pernocta (qui DORM aquí, via elèctric domèstic): ~386 hab · gap +86% sobre el padró
  · L2 càrrega total (inclou excursionistes de dia, via residus): ~535 hab
  · L3 pressió turística (via vidre; 0–100, RELATIU a la comarca, 50 = mitjana): 100
IETR (exposició turística-residencial): 72,1 · #4 de 31 · stock 100 / impact 44,2

SENYALS FÍSICS (mesura):
  · elèctric domèstic 2283,4 kWh/hab · residus 1059,7 kg/hab · vidre 149,4 kg/hab
  · restauració 6 locals · comerç+serveis 4 establiments  (OSM = mínim observat, no cens)
TURISME REGLAT: 20 establiments (96,6 per 1000 hab)
HABITATGE: 67,9% no principal · índex d'envelliment 310,5

CONTEXT COMARCAL: població mediana 260 hab · IETR mitjà 38,9 · el Berguedà és rural i envellit, amb un extrem turístic (Gósol, Castellar, Saldes) i una capital de serveis (Berga).
CAVEATS: les 3 capes i els gaps són INFERÈNCIA. Inferència sobre senyals físics, no cens.
[Composició d'origen/arrelament: capa SENSIBLE, FORA de la interpretació v1 (vegeu el CSV/SQLite si la vols consultar a banda).]

### Capolat  ·  INE 08045  ·  Berguedà
Població (padró): 93 hab

TIPOLOGIA: «indeterminat» — Senyals ambigus o mixtos: el model NO força una etiqueta (territori mixt).
  Confiança: alta (score 42,7/100)

MODEL DE 3 CAPES — INFERÈNCIA (no cens; es llegeix com a rang):
  · L1 pernocta (qui DORM aquí, via elèctric domèstic): ~131 hab · gap +41% sobre el padró
  · L2 càrrega total (inclou excursionistes de dia, via residus): ~206 hab
  · L3 pressió turística (via vidre; 0–100, RELATIU a la comarca, 50 = mitjana): 61,9
IETR (exposició turística-residencial): 60,5 · #5 de 31 · stock 28,1 / impact 93,0

SENYALS FÍSICS (mesura):
  · elèctric domèstic 1723,2 kWh/hab · residus 906,5 kg/hab · vidre 77,2 kg/hab
  · restauració 1 locals · comerç+serveis 1 establiments  (OSM = mínim observat, no cens)
TURISME REGLAT: 13 establiments (139,8 per 1000 hab)
HABITATGE: 43,3% no principal · índex d'envelliment 106,3

CONTEXT COMARCAL: població mediana 260 hab · IETR mitjà 38,9 · el Berguedà és rural i envellit, amb un extrem turístic (Gósol, Castellar, Saldes) i una capital de serveis (Berga).
CAVEATS: les 3 capes i els gaps són INFERÈNCIA. Inferència sobre senyals físics, no cens.
[Composició d'origen/arrelament: capa SENSIBLE, FORA de la interpretació v1 (vegeu el CSV/SQLite si la vols consultar a banda).]

### Saldes  ·  INE 08190  ·  Berguedà
Població (padró): 301 hab

TIPOLOGIA: «segona_residencia» — Turisme de pernocta: molts llits (2a residència) que s'omplen caps de setmana i ponts.
  Confiança: alta (score 76,5/100)

MODEL DE 3 CAPES — INFERÈNCIA (no cens; es llegeix com a rang):
  · L1 pernocta (qui DORM aquí, via elèctric domèstic): ~560 hab · gap +86% sobre el padró
  · L2 càrrega total (inclou excursionistes de dia, via residus): ~681 hab
  · L3 pressió turística (via vidre; 0–100, RELATIU a la comarca, 50 = mitjana): 71
IETR (exposició turística-residencial): 57,8 · #6 de 31 · stock 77,1 / impact 38,6

SENYALS FÍSICS (mesura):
  · elèctric domèstic 2277,4 kWh/hab · residus 927,3 kg/hab · vidre 90,1 kg/hab
  · restauració 5 locals · comerç+serveis 8 establiments  (OSM = mínim observat, no cens)
TURISME REGLAT: 23 establiments (76,4 per 1000 hab)
HABITATGE: 61,6% no principal · índex d'envelliment 359,3

CONTEXT COMARCAL: població mediana 260 hab · IETR mitjà 38,9 · el Berguedà és rural i envellit, amb un extrem turístic (Gósol, Castellar, Saldes) i una capital de serveis (Berga).
CAVEATS: les 3 capes i els gaps són INFERÈNCIA. Inferència sobre senyals físics, no cens.
[Composició d'origen/arrelament: capa SENSIBLE, FORA de la interpretació v1 (vegeu el CSV/SQLite si la vols consultar a banda).]

### Sagàs  ·  INE 08188  ·  Berguedà
Població (padró): 153 hab

TIPOLOGIA: «segona_residencia» — Turisme de pernocta: molts llits (2a residència) que s'omplen caps de setmana i ponts.
  Confiança: alta (score 34/100)

MODEL DE 3 CAPES — INFERÈNCIA (no cens; es llegeix com a rang):
  · L1 pernocta (qui DORM aquí, via elèctric domèstic): ~394 hab · gap +158% sobre el padró
  · L2 càrrega total (inclou excursionistes de dia, via residus): ~285 hab
  · L3 pressió turística (via vidre; 0–100, RELATIU a la comarca, 50 = mitjana): 100
IETR (exposició turística-residencial): 56,1 · #7 de 31 · stock 22,2 / impact 90,1

SENYALS FÍSICS (mesura):
  · elèctric domèstic 3.153 kWh/hab · residus 764,5 kg/hab · vidre 132,5 kg/hab
  · restauració 1 locals · comerç+serveis 1 establiments  (OSM = mínim observat, no cens)
TURISME REGLAT: 20 establiments (130,7 per 1000 hab)
HABITATGE: 43,6% no principal · índex d'envelliment 163,2

CONTEXT COMARCAL: població mediana 260 hab · IETR mitjà 38,9 · el Berguedà és rural i envellit, amb un extrem turístic (Gósol, Castellar, Saldes) i una capital de serveis (Berga).
CAVEATS: les 3 capes i els gaps són INFERÈNCIA. Inferència sobre senyals físics, no cens.
[Composició d'origen/arrelament: capa SENSIBLE, FORA de la interpretació v1 (vegeu el CSV/SQLite si la vols consultar a banda).]

### Castellar del Riu  ·  INE 08050  ·  Berguedà
Població (padró): 151 hab

TIPOLOGIA: «indeterminat» — Senyals ambigus o mixtos: el model NO força una etiqueta (territori mixt).
  Confiança: baixa (score 44,2/100)

MODEL DE 3 CAPES — INFERÈNCIA (no cens; es llegeix com a rang):
  · L1 pernocta (qui DORM aquí, via elèctric domèstic): ~188 hab · gap +24% sobre el padró
  · L2 càrrega total (inclou excursionistes de dia, via residus): ~379 hab
  · L3 pressió turística (via vidre; 0–100, RELATIU a la comarca, 50 = mitjana): 62,7
IETR (exposició turística-residencial): 55,1 · #8 de 31 · stock 35,8 / impact 74,5

SENYALS FÍSICS (mesura):
  · elèctric domèstic 1523,3 kWh/hab · residus 1028,0 kg/hab · vidre 78,4 kg/hab
  · restauració 1 locals · comerç+serveis 1 establiments  (OSM = mínim observat, no cens)
TURISME REGLAT: 17 establiments (112,6 per 1000 hab)
HABITATGE: 45,2% no principal · índex d'envelliment 117,4

CONTEXT COMARCAL: població mediana 260 hab · IETR mitjà 38,9 · el Berguedà és rural i envellit, amb un extrem turístic (Gósol, Castellar, Saldes) i una capital de serveis (Berga).
CAVEATS: les 3 capes i els gaps són INFERÈNCIA. Confiança baixa: senyals que divergeixen o padró petit → llegeix-ho amb prudència.
[Composició d'origen/arrelament: capa SENSIBLE, FORA de la interpretació v1 (vegeu el CSV/SQLite si la vols consultar a banda).]

### Castell de l'Areny  ·  INE 08057  ·  Berguedà
Població (padró): 68 hab

TIPOLOGIA: «indeterminat» — Senyals ambigus o mixtos: el model NO força una etiqueta (territori mixt).
  Confiança: baixa (score 36,4/100)

MODEL DE 3 CAPES — INFERÈNCIA (no cens; es llegeix com a rang):
  · L1 pernocta (qui DORM aquí, via elèctric domèstic): ~92 hab · gap +35% sobre el padró
  · L2 càrrega total (inclou excursionistes de dia, via residus): ~149 hab
  · L3 pressió turística (via vidre; 0–100, RELATIU a la comarca, 50 = mitjana): 49,7
IETR (exposició turística-residencial): 52,8 · #9 de 31 · stock 55,1 / impact 50,4

SENYALS FÍSICS (mesura):
  · elèctric domèstic 1648,8 kWh/hab · residus 898,7 kg/hab · vidre 60,1 kg/hab
  · restauració 0 locals · comerç+serveis 1 establiments  (OSM = mínim observat, no cens)
TURISME REGLAT: 6 establiments (88,2 per 1000 hab)
HABITATGE: 53,0% no principal · índex d'envelliment 450

CONTEXT COMARCAL: població mediana 260 hab · IETR mitjà 38,9 · el Berguedà és rural i envellit, amb un extrem turístic (Gósol, Castellar, Saldes) i una capital de serveis (Berga).
CAVEATS: les 3 capes i els gaps són INFERÈNCIA. Confiança baixa: senyals que divergeixen o padró petit → llegeix-ho amb prudència.
[Composició d'origen/arrelament: capa SENSIBLE, FORA de la interpretació v1 (vegeu el CSV/SQLite si la vols consultar a banda).]

### Montclar  ·  INE 08130  ·  Berguedà
Població (padró): 133 hab

TIPOLOGIA: «buit_administratiu» — Micromunicipi tranquil a tots els eixos: padró estable, sense pressió.
  Confiança: baixa (score 57/100)

MODEL DE 3 CAPES — INFERÈNCIA (no cens; es llegeix com a rang):
  · L1 pernocta (qui DORM aquí, via elèctric domèstic): ~204 hab · gap +53% sobre el padró
  · L2 càrrega total (inclou excursionistes de dia, via residus): ~192 hab
  · L3 pressió turística (via vidre; 0–100, RELATIU a la comarca, 50 = mitjana): 38,4
IETR (exposició turística-residencial): 46,0 · #10 de 31 · stock 33,2 / impact 58,9

SENYALS FÍSICS (mesura):
  · elèctric domèstic 1880,4 kWh/hab · residus 592,7 kg/hab · vidre 44,2 kg/hab
  · restauració 0 locals · comerç+serveis 1 establiments  (OSM = mínim observat, no cens)
TURISME REGLAT: 11 establiments (82,7 per 1000 hab)
HABITATGE: 47,1% no principal · índex d'envelliment 140,9

CONTEXT COMARCAL: població mediana 260 hab · IETR mitjà 38,9 · el Berguedà és rural i envellit, amb un extrem turístic (Gósol, Castellar, Saldes) i una capital de serveis (Berga).
CAVEATS: les 3 capes i els gaps són INFERÈNCIA. Confiança baixa: senyals que divergeixen o padró petit → llegeix-ho amb prudència.
[Composició d'origen/arrelament: capa SENSIBLE, FORA de la interpretació v1 (vegeu el CSV/SQLite si la vols consultar a banda).]

### Quar, la  ·  INE 08177  ·  Berguedà
Població (padró): 44 hab

TIPOLOGIA: «indeterminat» — Senyals ambigus o mixtos: el model NO força una etiqueta (territori mixt).
  Confiança: baixa (score 5/100)

MODEL DE 3 CAPES — INFERÈNCIA (no cens; es llegeix com a rang):
  · L1 pernocta (qui DORM aquí, via elèctric domèstic): ~127 hab · gap +189% sobre el padró
  · L2 càrrega total (inclou excursionistes de dia, via residus): ~86 hab
  · L3 pressió turística (via vidre; 0–100, RELATIU a la comarca, 50 = mitjana): 57,1
IETR (exposició turística-residencial): 45,7 · #11 de 31 · stock 29,1 / impact 62,2

SENYALS FÍSICS (mesura):
  · elèctric domèstic 3539,5 kWh/hab · residus 803,9 kg/hab · vidre 70,5 kg/hab
  · restauració 0 locals · comerç+serveis 1 establiments  (OSM = mínim observat, no cens)
TURISME REGLAT: 4 establiments (90,9 per 1000 hab)
HABITATGE: 41,9% no principal · índex d'envelliment 240

CONTEXT COMARCAL: població mediana 260 hab · IETR mitjà 38,9 · el Berguedà és rural i envellit, amb un extrem turístic (Gósol, Castellar, Saldes) i una capital de serveis (Berga).
CAVEATS: les 3 capes i els gaps són INFERÈNCIA. Confiança baixa: senyals que divergeixen o padró petit → llegeix-ho amb prudència.
[Composició d'origen/arrelament: capa SENSIBLE, FORA de la interpretació v1 (vegeu el CSV/SQLite si la vols consultar a banda).]

### Santa Maria de Merlès  ·  INE 08255  ·  Berguedà
Població (padró): 179 hab

TIPOLOGIA: «indeterminat» — Senyals ambigus o mixtos: el model NO força una etiqueta (territori mixt).
  Confiança: baixa (score 51,6/100)

MODEL DE 3 CAPES — INFERÈNCIA (no cens; es llegeix com a rang):
  · L1 pernocta (qui DORM aquí, via elèctric domèstic): ~398 hab · gap +122% sobre el padró
  · L2 càrrega total (inclou excursionistes de dia, via residus): ~300 hab
  · L3 pressió turística (via vidre; 0–100, RELATIU a la comarca, 50 = mitjana): 63,8
IETR (exposició turística-residencial): 44,3 · #12 de 31 · stock 31,3 / impact 57,3

SENYALS FÍSICS (mesura):
  · elèctric domèstic 2721,8 kWh/hab · residus 687,0 kg/hab · vidre 79,9 kg/hab
  · restauració 2 locals · comerç+serveis 1 establiments  (OSM = mínim observat, no cens)
TURISME REGLAT: 14 establiments (78,2 per 1000 hab)
HABITATGE: 46,9% no principal · índex d'envelliment 87,5

CONTEXT COMARCAL: població mediana 260 hab · IETR mitjà 38,9 · el Berguedà és rural i envellit, amb un extrem turístic (Gósol, Castellar, Saldes) i una capital de serveis (Berga).
CAVEATS: les 3 capes i els gaps són INFERÈNCIA. Confiança baixa: senyals que divergeixen o padró petit → llegeix-ho amb prudència.
[Composició d'origen/arrelament: capa SENSIBLE, FORA de la interpretació v1 (vegeu el CSV/SQLite si la vols consultar a banda).]

### Borredà  ·  INE 08024  ·  Berguedà
Població (padró): 434 hab

TIPOLOGIA: «indeterminat» — Senyals ambigus o mixtos: el model NO força una etiqueta (territori mixt).
  Confiança: alta (score 79,2/100)

MODEL DE 3 CAPES — INFERÈNCIA (no cens; es llegeix com a rang):
  · L1 pernocta (qui DORM aquí, via elèctric domèstic): ~619 hab · gap +43% sobre el padró
  · L2 càrrega total (inclou excursionistes de dia, via residus): ~908 hab
  · L3 pressió turística (via vidre; 0–100, RELATIU a la comarca, 50 = mitjana): 42,4
IETR (exposició turística-residencial): 44,1 · #13 de 31 · stock 53,9 / impact 34,4

SENYALS FÍSICS (mesura):
  · elèctric domèstic 1745,1 kWh/hab · residus 858,2 kg/hab · vidre 49,8 kg/hab
  · restauració 4 locals · comerç+serveis 5 establiments  (OSM = mínim observat, no cens)
TURISME REGLAT: 26 establiments (59,9 per 1000 hab)
HABITATGE: 54,6% no principal · índex d'envelliment 361,8

CONTEXT COMARCAL: població mediana 260 hab · IETR mitjà 38,9 · el Berguedà és rural i envellit, amb un extrem turístic (Gósol, Castellar, Saldes) i una capital de serveis (Berga).
CAVEATS: les 3 capes i els gaps són INFERÈNCIA. Inferència sobre senyals físics, no cens.
[Composició d'origen/arrelament: capa SENSIBLE, FORA de la interpretació v1 (vegeu el CSV/SQLite si la vols consultar a banda).]

### Vallcebre  ·  INE 08293  ·  Berguedà
Població (padró): 260 hab

TIPOLOGIA: «indeterminat» — Senyals ambigus o mixtos: el model NO força una etiqueta (territori mixt).
  Confiança: alta (score 65,5/100)

MODEL DE 3 CAPES — INFERÈNCIA (no cens; es llegeix com a rang):
  · L1 pernocta (qui DORM aquí, via elèctric domèstic): ~326 hab · gap +25% sobre el padró
  · L2 càrrega total (inclou excursionistes de dia, via residus): ~531 hab
  · L3 pressió turística (via vidre; 0–100, RELATIU a la comarca, 50 = mitjana): 46,6
IETR (exposició turística-residencial): 43,8 · #14 de 31 · stock 56,5 / impact 31,2

SENYALS FÍSICS (mesura):
  · elèctric domèstic 1532,5 kWh/hab · residus 837,4 kg/hab · vidre 55,7 kg/hab
  · restauració 2 locals · comerç+serveis 4 establiments  (OSM = mínim observat, no cens)
TURISME REGLAT: 15 establiments (57,7 per 1000 hab)
HABITATGE: 53,1% no principal · índex d'envelliment 537,5

CONTEXT COMARCAL: població mediana 260 hab · IETR mitjà 38,9 · el Berguedà és rural i envellit, amb un extrem turístic (Gósol, Castellar, Saldes) i una capital de serveis (Berga).
CAVEATS: les 3 capes i els gaps són INFERÈNCIA. Inferència sobre senyals físics, no cens.
[Composició d'origen/arrelament: capa SENSIBLE, FORA de la interpretació v1 (vegeu el CSV/SQLite si la vols consultar a banda).]

### Nou de Berguedà, la  ·  INE 08142  ·  Berguedà
Població (padró): 163 hab

TIPOLOGIA: «excursio» — Turisme d'excursió (de dia): vénen, gasten i marxen; deixen residus i ampolles, no llum de casa.
  Confiança: alta (score 59/100)

MODEL DE 3 CAPES — INFERÈNCIA (no cens; es llegeix com a rang):
  · L1 pernocta (qui DORM aquí, via elèctric domèstic): ~259 hab · gap +59% sobre el padró
  · L2 càrrega total (inclou excursionistes de dia, via residus): ~373 hab
  · L3 pressió turística (via vidre; 0–100, RELATIU a la comarca, 50 = mitjana): 71,5
IETR (exposició turística-residencial): 41,1 · #15 de 31 · stock 38,9 / impact 43,4

SENYALS FÍSICS (mesura):
  · elèctric domèstic 1.943 kWh/hab · residus 939,1 kg/hab · vidre 90,8 kg/hab
  · restauració 3 locals · comerç+serveis 2 establiments  (OSM = mínim observat, no cens)
TURISME REGLAT: 11 establiments (67,5 per 1000 hab)
HABITATGE: 48,0% no principal · índex d'envelliment 391,7

CONTEXT COMARCAL: població mediana 260 hab · IETR mitjà 38,9 · el Berguedà és rural i envellit, amb un extrem turístic (Gósol, Castellar, Saldes) i una capital de serveis (Berga).
CAVEATS: les 3 capes i els gaps són INFERÈNCIA. Inferència sobre senyals físics, no cens.
[Composició d'origen/arrelament: capa SENSIBLE, FORA de la interpretació v1 (vegeu el CSV/SQLite si la vols consultar a banda).]

### Viver i Serrateix  ·  INE 08308  ·  Berguedà
Població (padró): 178 hab

TIPOLOGIA: «indeterminat» — Senyals ambigus o mixtos: el model NO força una etiqueta (territori mixt).
  Confiança: mitjana (score 61/100)

MODEL DE 3 CAPES — INFERÈNCIA (no cens; es llegeix com a rang):
  · L1 pernocta (qui DORM aquí, via elèctric domèstic): ~311 hab · gap +75% sobre el padró
  · L2 càrrega total (inclou excursionistes de dia, via residus): ~293 hab
  · L3 pressió turística (via vidre; 0–100, RELATIU a la comarca, 50 = mitjana): 59,9
IETR (exposició turística-residencial): 40,1 · #16 de 31 · stock 21,4 / impact 58,8

SENYALS FÍSICS (mesura):
  · elèctric domèstic 2136,7 kWh/hab · residus 675,0 kg/hab · vidre 74,5 kg/hab
  · restauració 0 locals · comerç+serveis 1 establiments  (OSM = mínim observat, no cens)
TURISME REGLAT: 13 establiments (73,0 per 1000 hab)
HABITATGE: 42,1% no principal · índex d'envelliment 122,9

CONTEXT COMARCAL: població mediana 260 hab · IETR mitjà 38,9 · el Berguedà és rural i envellit, amb un extrem turístic (Gósol, Castellar, Saldes) i una capital de serveis (Berga).
CAVEATS: les 3 capes i els gaps són INFERÈNCIA. Inferència sobre senyals físics, no cens.
[Composició d'origen/arrelament: capa SENSIBLE, FORA de la interpretació v1 (vegeu el CSV/SQLite si la vols consultar a banda).]

### Fígols  ·  INE 08080  ·  Berguedà
Població (padró): 41 hab

TIPOLOGIA: «buit_administratiu» — Micromunicipi tranquil a tots els eixos: padró estable, sense pressió.
  Confiança: baixa (score 29,7/100)

MODEL DE 3 CAPES — INFERÈNCIA (no cens; es llegeix com a rang):
  · L1 pernocta (qui DORM aquí, via elèctric domèstic): ~34 hab · gap -17% sobre el padró
  · L2 càrrega total (inclou excursionistes de dia, via residus): ~76 hab
  · L3 pressió turística (via vidre; 0–100, RELATIU a la comarca, 50 = mitjana): 7,8
IETR (exposició turística-residencial): 35,8 · #17 de 31 · stock 26,6 / impact 44,9

SENYALS FÍSICS (mesura):
  · elèctric domèstic 1016,4 kWh/hab · residus 759,9 kg/hab · vidre 1,2 kg/hab
  · restauració 0 locals · comerç+serveis 1 establiments  (OSM = mínim observat, no cens)
TURISME REGLAT: 3 establiments (73,2 per 1000 hab)
HABITATGE: 35,3% no principal · índex d'envelliment 1.100

CONTEXT COMARCAL: població mediana 260 hab · IETR mitjà 38,9 · el Berguedà és rural i envellit, amb un extrem turístic (Gósol, Castellar, Saldes) i una capital de serveis (Berga).
CAVEATS: les 3 capes i els gaps són INFERÈNCIA. Confiança baixa: senyals que divergeixen o padró petit → llegeix-ho amb prudència.
[Composició d'origen/arrelament: capa SENSIBLE, FORA de la interpretació v1 (vegeu el CSV/SQLite si la vols consultar a banda).]

### Pobla de Lillet, la  ·  INE 08166  ·  Berguedà
Població (padró): 1.106 hab

TIPOLOGIA: «indeterminat» — Senyals ambigus o mixtos: el model NO força una etiqueta (territori mixt).
  Confiança: mitjana (score 72,5/100)

MODEL DE 3 CAPES — INFERÈNCIA (no cens; es llegeix com a rang):
  · L1 pernocta (qui DORM aquí, via elèctric domèstic): ~1.243 hab · gap +12% sobre el padró
  · L2 càrrega total (inclou excursionistes de dia, via residus): ~1.237 hab
  · L3 pressió turística (via vidre; 0–100, RELATIU a la comarca, 50 = mitjana): 41,5
IETR (exposició turística-residencial): 32,3 · #18 de 31 · stock 50,3 / impact 14,2

SENYALS FÍSICS (mesura):
  · elèctric domèstic 1375,1 kWh/hab · residus 458,6 kg/hab · vidre 48,6 kg/hab
  · restauració 7 locals · comerç+serveis 16 establiments  (OSM = mínim observat, no cens)
TURISME REGLAT: 31 establiments (28,0 per 1000 hab)
HABITATGE: 52,1% no principal · índex d'envelliment 407,1

CONTEXT COMARCAL: població mediana 260 hab · IETR mitjà 38,9 · el Berguedà és rural i envellit, amb un extrem turístic (Gósol, Castellar, Saldes) i una capital de serveis (Berga).
CAVEATS: les 3 capes i els gaps són INFERÈNCIA. Inferència sobre senyals físics, no cens.
[Composició d'origen/arrelament: capa SENSIBLE, FORA de la interpretació v1 (vegeu el CSV/SQLite si la vols consultar a banda).]

### Cercs  ·  INE 08268  ·  Berguedà
Població (padró): 1.236 hab

TIPOLOGIA: «indeterminat» — Senyals ambigus o mixtos: el model NO força una etiqueta (territori mixt).
  Confiança: mitjana (score 73,1/100)

MODEL DE 3 CAPES — INFERÈNCIA (no cens; es llegeix com a rang):
  · L1 pernocta (qui DORM aquí, via elèctric domèstic): ~1.652 hab · gap +34% sobre el padró
  · L2 càrrega total (inclou excursionistes de dia, via residus): ~1.466 hab
  · L3 pressió turística (via vidre; 0–100, RELATIU a la comarca, 50 = mitjana): 32,8
IETR (exposició turística-residencial): 31,1 · #19 de 31 · stock 50,9 / impact 11,3

SENYALS FÍSICS (mesura):
  · elèctric domèstic 1635,7 kWh/hab · residus 486,2 kg/hab · vidre 36,4 kg/hab
  · restauració 11 locals · comerç+serveis 8 establiments  (OSM = mínim observat, no cens)
TURISME REGLAT: 29 establiments (23,5 per 1000 hab)
HABITATGE: 52,8% no principal · índex d'envelliment 270

CONTEXT COMARCAL: població mediana 260 hab · IETR mitjà 38,9 · el Berguedà és rural i envellit, amb un extrem turístic (Gósol, Castellar, Saldes) i una capital de serveis (Berga).
CAVEATS: les 3 capes i els gaps són INFERÈNCIA. Inferència sobre senyals físics, no cens.
[Composició d'origen/arrelament: capa SENSIBLE, FORA de la interpretació v1 (vegeu el CSV/SQLite si la vols consultar a banda).]

### Espunyola, l'  ·  INE 08078  ·  Berguedà
Població (padró): 260 hab

TIPOLOGIA: «indeterminat» — Senyals ambigus o mixtos: el model NO força una etiqueta (territori mixt).
  Confiança: alta (score 58,5/100)

MODEL DE 3 CAPES — INFERÈNCIA (no cens; es llegeix com a rang):
  · L1 pernocta (qui DORM aquí, via elèctric domèstic): ~391 hab · gap +50% sobre el padró
  · L2 càrrega total (inclou excursionistes de dia, via residus): ~530 hab
  · L3 pressió turística (via vidre; 0–100, RELATIU a la comarca, 50 = mitjana): 34,8
IETR (exposició turística-residencial): 30,4 · #20 de 31 · stock 5,6 / impact 55,2

SENYALS FÍSICS (mesura):
  · elèctric domèstic 1839,6 kWh/hab · residus 836,2 kg/hab · vidre 39,2 kg/hab
  · restauració 3 locals · comerç+serveis 2 establiments  (OSM = mínim observat, no cens)
TURISME REGLAT: 17 establiments (65,4 per 1000 hab)
HABITATGE: 30,5% no principal · índex d'envelliment 176,5

CONTEXT COMARCAL: població mediana 260 hab · IETR mitjà 38,9 · el Berguedà és rural i envellit, amb un extrem turístic (Gósol, Castellar, Saldes) i una capital de serveis (Berga).
CAVEATS: les 3 capes i els gaps són INFERÈNCIA. Inferència sobre senyals físics, no cens.
[Composició d'origen/arrelament: capa SENSIBLE, FORA de la interpretació v1 (vegeu el CSV/SQLite si la vols consultar a banda).]

### Guardiola de Berguedà  ·  INE 08099  ·  Berguedà
Població (padró): 962 hab

TIPOLOGIA: «indeterminat» — Senyals ambigus o mixtos: el model NO força una etiqueta (territori mixt).
  Confiança: mitjana (score 83,7/100)

MODEL DE 3 CAPES — INFERÈNCIA (no cens; es llegeix com a rang):
  · L1 pernocta (qui DORM aquí, via elèctric domèstic): ~1.125 hab · gap +17% sobre el padró
  · L2 càrrega total (inclou excursionistes de dia, via residus): ~1.120 hab
  · L3 pressió turística (via vidre; 0–100, RELATIU a la comarca, 50 = mitjana): 44,6
IETR (exposició turística-residencial): 29,3 · #21 de 31 · stock 30,2 / impact 28,4

SENYALS FÍSICS (mesura):
  · elèctric domèstic 1.432 kWh/hab · residus 477,4 kg/hab · vidre 53 kg/hab
  · restauració 4 locals · comerç+serveis 9 establiments  (OSM = mínim observat, no cens)
TURISME REGLAT: 44 establiments (45,7 per 1000 hab)
HABITATGE: 41,2% no principal · índex d'envelliment 286,8

CONTEXT COMARCAL: població mediana 260 hab · IETR mitjà 38,9 · el Berguedà és rural i envellit, amb un extrem turístic (Gósol, Castellar, Saldes) i una capital de serveis (Berga).
CAVEATS: les 3 capes i els gaps són INFERÈNCIA. Inferència sobre senyals físics, no cens.
[Composició d'origen/arrelament: capa SENSIBLE, FORA de la interpretació v1 (vegeu el CSV/SQLite si la vols consultar a banda).]

### Sant Julià de Cerdanyola  ·  INE 08903  ·  Berguedà
Població (padró): 234 hab

TIPOLOGIA: «dormitori_invisible» — Hi dormen sense constar al padró, però amb poca hostaleria.
  Confiança: baixa (score 61,4/100)

MODEL DE 3 CAPES — INFERÈNCIA (no cens; es llegeix com a rang):
  · L1 pernocta (qui DORM aquí, via elèctric domèstic): ~412 hab · gap +76% sobre el padró
  · L2 càrrega total (inclou excursionistes de dia, via residus): ~289 hab
  · L3 pressió turística (via vidre; 0–100, RELATIU a la comarca, 50 = mitjana): 48,3
IETR (exposició turística-residencial): 29,0 · #22 de 31 · stock 51,4 / impact 6,7

SENYALS FÍSICS (mesura):
  · elèctric domèstic 2153,8 kWh/hab · residus 506,5 kg/hab · vidre 58,1 kg/hab
  · restauració 2 locals · comerç+serveis 3 establiments  (OSM = mínim observat, no cens)
TURISME REGLAT: 4 establiments (17,1 per 1000 hab)
HABITATGE: 49,6% no principal · índex d'envelliment 281,8

CONTEXT COMARCAL: població mediana 260 hab · IETR mitjà 38,9 · el Berguedà és rural i envellit, amb un extrem turístic (Gósol, Castellar, Saldes) i una capital de serveis (Berga).
CAVEATS: les 3 capes i els gaps són INFERÈNCIA. Confiança baixa: senyals que divergeixen o padró petit → llegeix-ho amb prudència.
[Composició d'origen/arrelament: capa SENSIBLE, FORA de la interpretació v1 (vegeu el CSV/SQLite si la vols consultar a banda).]

### Montmajor  ·  INE 08132  ·  Berguedà
Població (padró): 471 hab

TIPOLOGIA: «indeterminat» — Senyals ambigus o mixtos: el model NO força una etiqueta (territori mixt).
  Confiança: alta (score 80,4/100)

MODEL DE 3 CAPES — INFERÈNCIA (no cens; es llegeix com a rang):
  · L1 pernocta (qui DORM aquí, via elèctric domèstic): ~766 hab · gap +63% sobre el padró
  · L2 càrrega total (inclou excursionistes de dia, via residus): ~969 hab
  · L3 pressió turística (via vidre; 0–100, RELATIU a la comarca, 50 = mitjana): 40
IETR (exposició turística-residencial): 26 · #23 de 31 · stock 25,7 / impact 26,3

SENYALS FÍSICS (mesura):
  · elèctric domèstic 1989,5 kWh/hab · residus 843,3 kg/hab · vidre 46,5 kg/hab
  · restauració 5 locals · comerç+serveis 6 establiments  (OSM = mínim observat, no cens)
TURISME REGLAT: 18 establiments (38,2 per 1000 hab)
HABITATGE: 42,6% no principal · índex d'envelliment 211,3

CONTEXT COMARCAL: població mediana 260 hab · IETR mitjà 38,9 · el Berguedà és rural i envellit, amb un extrem turístic (Gósol, Castellar, Saldes) i una capital de serveis (Berga).
CAVEATS: les 3 capes i els gaps són INFERÈNCIA. Inferència sobre senyals físics, no cens.
[Composició d'origen/arrelament: capa SENSIBLE, FORA de la interpretació v1 (vegeu el CSV/SQLite si la vols consultar a banda).]

### Bagà  ·  INE 08016  ·  Berguedà
Població (padró): 2.167 hab

TIPOLOGIA: «capital_serveis» — Centre de serveis real: té el comerç i els serveis essencials que serveixen també els pobles veïns.
  Confiança: mitjana (score 77,3/100)

MODEL DE 3 CAPES — INFERÈNCIA (no cens; es llegeix com a rang):
  · L1 pernocta (qui DORM aquí, via elèctric domèstic): ~2.780 hab · gap +28% sobre el padró
  · L2 càrrega total (inclou excursionistes de dia, via residus): ~2.351 hab
  · L3 pressió turística (via vidre; 0–100, RELATIU a la comarca, 50 = mitjana): 31,5
IETR (exposició turística-residencial): 24,5 · #24 de 31 · stock 38,2 / impact 10,8

SENYALS FÍSICS (mesura):
  · elèctric domèstic 1570,2 kWh/hab · residus 444,7 kg/hab · vidre 34,5 kg/hab
  · restauració 9 locals · comerç+serveis 16 establiments  (OSM = mínim observat, no cens)
TURISME REGLAT: 46 establiments (21,2 per 1000 hab)
HABITATGE: 46,4% no principal · índex d'envelliment 295,7

CONTEXT COMARCAL: població mediana 260 hab · IETR mitjà 38,9 · el Berguedà és rural i envellit, amb un extrem turístic (Gósol, Castellar, Saldes) i una capital de serveis (Berga).
CAVEATS: les 3 capes i els gaps són INFERÈNCIA. Inferència sobre senyals físics, no cens.
[Composició d'origen/arrelament: capa SENSIBLE, FORA de la interpretació v1 (vegeu el CSV/SQLite si la vols consultar a banda).]

### Vilada  ·  INE 08299  ·  Berguedà
Població (padró): 430 hab

TIPOLOGIA: «indeterminat» — Senyals ambigus o mixtos: el model NO força una etiqueta (territori mixt).
  Confiança: mitjana (score 75,4/100)

MODEL DE 3 CAPES — INFERÈNCIA (no cens; es llegeix com a rang):
  · L1 pernocta (qui DORM aquí, via elèctric domèstic): ~554 hab · gap +29% sobre el padró
  · L2 càrrega total (inclou excursionistes de dia, via residus): ~380 hab
  · L3 pressió turística (via vidre; 0–100, RELATIU a la comarca, 50 = mitjana): 32,3
IETR (exposició turística-residencial): 21,0 · #25 de 31 · stock 34,4 / impact 7,6

SENYALS FÍSICS (mesura):
  · elèctric domèstic 1575,7 kWh/hab · residus 362,1 kg/hab · vidre 35,6 kg/hab
  · restauració 4 locals · comerç+serveis 6 establiments  (OSM = mínim observat, no cens)
TURISME REGLAT: 7 establiments (16,3 per 1000 hab)
HABITATGE: 44,3% no principal · índex d'envelliment 325

CONTEXT COMARCAL: població mediana 260 hab · IETR mitjà 38,9 · el Berguedà és rural i envellit, amb un extrem turístic (Gósol, Castellar, Saldes) i una capital de serveis (Berga).
CAVEATS: les 3 capes i els gaps són INFERÈNCIA. Inferència sobre senyals físics, no cens.
[Composició d'origen/arrelament: capa SENSIBLE, FORA de la interpretació v1 (vegeu el CSV/SQLite si la vols consultar a banda).]

### Casserres  ·  INE 08049  ·  Berguedà
Població (padró): 1.665 hab

TIPOLOGIA: «indeterminat» — Senyals ambigus o mixtos: el model NO força una etiqueta (territori mixt).
  Confiança: mitjana (score 80,3/100)

MODEL DE 3 CAPES — INFERÈNCIA (no cens; es llegeix com a rang):
  · L1 pernocta (qui DORM aquí, via elèctric domèstic): ~2.225 hab · gap +34% sobre el padró
  · L2 càrrega total (inclou excursionistes de dia, via residus): ~1.615 hab
  · L3 pressió turística (via vidre; 0–100, RELATIU a la comarca, 50 = mitjana): 34,5
IETR (exposició turística-residencial): 13,2 · #26 de 31 · stock 15,8 / impact 10,7

SENYALS FÍSICS (mesura):
  · elèctric domèstic 1635,9 kWh/hab · residus 397,8 kg/hab · vidre 38,7 kg/hab
  · restauració 5 locals · comerç+serveis 9 establiments  (OSM = mínim observat, no cens)
TURISME REGLAT: 30 establiments (18,0 per 1000 hab)
HABITATGE: 35,1% no principal · índex d'envelliment 202,6

CONTEXT COMARCAL: població mediana 260 hab · IETR mitjà 38,9 · el Berguedà és rural i envellit, amb un extrem turístic (Gósol, Castellar, Saldes) i una capital de serveis (Berga).
CAVEATS: les 3 capes i els gaps són INFERÈNCIA. Inferència sobre senyals físics, no cens.
[Composició d'origen/arrelament: capa SENSIBLE, FORA de la interpretació v1 (vegeu el CSV/SQLite si la vols consultar a banda).]

### Olvan  ·  INE 08144  ·  Berguedà
Població (padró): 926 hab

TIPOLOGIA: «indeterminat» — Senyals ambigus o mixtos: el model NO força una etiqueta (territori mixt).
  Confiança: mitjana (score 83,8/100)

MODEL DE 3 CAPES — INFERÈNCIA (no cens; es llegeix com a rang):
  · L1 pernocta (qui DORM aquí, via elèctric domèstic): ~1.118 hab · gap +21% sobre el padró
  · L2 càrrega total (inclou excursionistes de dia, via residus): ~903 hab
  · L3 pressió turística (via vidre; 0–100, RELATIU a la comarca, 50 = mitjana): 32,6
IETR (exposició turística-residencial): 11,9 · #27 de 31 · stock 10,8 / impact 13,1

SENYALS FÍSICS (mesura):
  · elèctric domèstic 1477,9 kWh/hab · residus 400,0 kg/hab · vidre 36,1 kg/hab
  · restauració 3 locals · comerç+serveis 6 establiments  (OSM = mínim observat, no cens)
TURISME REGLAT: 19 establiments (20,5 per 1000 hab)
HABITATGE: 32,1% no principal · índex d'envelliment 221,2

CONTEXT COMARCAL: població mediana 260 hab · IETR mitjà 38,9 · el Berguedà és rural i envellit, amb un extrem turístic (Gósol, Castellar, Saldes) i una capital de serveis (Berga).
CAVEATS: les 3 capes i els gaps són INFERÈNCIA. Inferència sobre senyals físics, no cens.
[Composició d'origen/arrelament: capa SENSIBLE, FORA de la interpretació v1 (vegeu el CSV/SQLite si la vols consultar a banda).]

### Avià  ·  INE 08011  ·  Berguedà
Població (padró): 2.263 hab

TIPOLOGIA: «capital_serveis» — Centre de serveis real: té el comerç i els serveis essencials que serveixen també els pobles veïns.
  Confiança: mitjana (score 79,3/100)

MODEL DE 3 CAPES — INFERÈNCIA (no cens; es llegeix com a rang):
  · L1 pernocta (qui DORM aquí, via elèctric domèstic): ~2.684 hab · gap +19% sobre el padró
  · L2 càrrega total (inclou excursionistes de dia, via residus): ~2.076 hab
  · L3 pressió turística (via vidre; 0–100, RELATIU a la comarca, 50 = mitjana): 26,7
IETR (exposició turística-residencial): 4,1 · #28 de 31 · stock 0 / impact 8,3

SENYALS FÍSICS (mesura):
  · elèctric domèstic 1451,5 kWh/hab · residus 376,2 kg/hab · vidre 27,8 kg/hab
  · restauració 6 locals · comerç+serveis 13 establiments  (OSM = mínim observat, no cens)
TURISME REGLAT: 30 establiments (13,3 per 1000 hab)
HABITATGE: 25,6% no principal · índex d'envelliment 168,4

CONTEXT COMARCAL: població mediana 260 hab · IETR mitjà 38,9 · el Berguedà és rural i envellit, amb un extrem turístic (Gósol, Castellar, Saldes) i una capital de serveis (Berga).
CAVEATS: les 3 capes i els gaps són INFERÈNCIA. Inferència sobre senyals físics, no cens.
[Composició d'origen/arrelament: capa SENSIBLE, FORA de la interpretació v1 (vegeu el CSV/SQLite si la vols consultar a banda).]

### Puig-reig  ·  INE 08175  ·  Berguedà
Població (padró): 4.558 hab

TIPOLOGIA: «capital_serveis» — Centre de serveis real: té el comerç i els serveis essencials que serveixen també els pobles veïns.
  Confiança: mitjana (score 86,4/100)

MODEL DE 3 CAPES — INFERÈNCIA (no cens; es llegeix com a rang):
  · L1 pernocta (qui DORM aquí, via elèctric domèstic): ~4.343 hab · gap -5% sobre el padró
  · L2 càrrega total (inclou excursionistes de dia, via residus): ~3.713 hab
  · L3 pressió turística (via vidre; 0–100, RELATIU a la comarca, 50 = mitjana): 27,1
IETR (exposició turística-residencial): 0,9 · #29 de 31 · stock 1,8 / impact 0,1

SENYALS FÍSICS (mesura):
  · elèctric domèstic 1166,3 kWh/hab · residus 334,0 kg/hab · vidre 28,3 kg/hab
  · restauració 5 locals · comerç+serveis 10 establiments  (OSM = mínim observat, no cens)
TURISME REGLAT: 20 establiments (4,4 per 1000 hab)
HABITATGE: 26,7% no principal · índex d'envelliment 218,7

CONTEXT COMARCAL: població mediana 260 hab · IETR mitjà 38,9 · el Berguedà és rural i envellit, amb un extrem turístic (Gósol, Castellar, Saldes) i una capital de serveis (Berga).
CAVEATS: les 3 capes i els gaps són INFERÈNCIA. Inferència sobre senyals físics, no cens.
[Composició d'origen/arrelament: capa SENSIBLE, FORA de la interpretació v1 (vegeu el CSV/SQLite si la vols consultar a banda).]

### Gironella  ·  INE 08092  ·  Berguedà
Població (padró): 5.082 hab

TIPOLOGIA: «capital_serveis» — Centre de serveis real: té el comerç i els serveis essencials que serveixen també els pobles veïns.
  Confiança: mitjana (score 84,1/100)

MODEL DE 3 CAPES — INFERÈNCIA (no cens; es llegeix com a rang):
  · L1 pernocta (qui DORM aquí, via elèctric domèstic): ~5.245 hab · gap +3% sobre el padró
  · L2 càrrega total (inclou excursionistes de dia, via residus): ~4.010 hab
  · L3 pressió turística (via vidre; 0–100, RELATIU a la comarca, 50 = mitjana): 21,6
IETR (exposició turística-residencial): 0,6 · #30 de 31 · stock 1,2 / impact 0

SENYALS FÍSICS (mesura):
  · elèctric domèstic 1263,2 kWh/hab · residus 323,5 kg/hab · vidre 20,6 kg/hab
  · restauració 23 locals · comerç+serveis 25 establiments  (OSM = mínim observat, no cens)
TURISME REGLAT: 21 establiments (4,1 per 1000 hab)
HABITATGE: 26,4% no principal · índex d'envelliment 185,6

CONTEXT COMARCAL: població mediana 260 hab · IETR mitjà 38,9 · el Berguedà és rural i envellit, amb un extrem turístic (Gósol, Castellar, Saldes) i una capital de serveis (Berga).
CAVEATS: les 3 capes i els gaps són INFERÈNCIA. Inferència sobre senyals físics, no cens.
[Composició d'origen/arrelament: capa SENSIBLE, FORA de la interpretació v1 (vegeu el CSV/SQLite si la vols consultar a banda).]

### Berga  ·  INE 08022  ·  Berguedà
Població (padró): 17.539 hab

TIPOLOGIA: «capital_serveis» — Centre de serveis real: té el comerç i els serveis essencials que serveixen també els pobles veïns.
  Confiança: mitjana (score 80,9/100)

MODEL DE 3 CAPES — INFERÈNCIA (no cens; es llegeix com a rang):
  · L1 pernocta (qui DORM aquí, via elèctric domèstic): ~17.174 hab · gap -2% sobre el padró
  · L2 càrrega total (inclou excursionistes de dia, via residus): ~19.626 hab
  · L3 pressió turística (via vidre; 0–100, RELATIU a la comarca, 50 = mitjana): 26,6
IETR (exposició turística-residencial): 0,3 · #31 de 31 · stock 0,6 / impact 0

SENYALS FÍSICS (mesura):
  · elèctric domèstic 1198,5 kWh/hab · residus 458,8 kg/hab · vidre 27,6 kg/hab
  · restauració 28 locals · comerç+serveis 53 establiments  (OSM = mínim observat, no cens)
TURISME REGLAT: 45 establiments (2,6 per 1000 hab)
HABITATGE: 24,2% no principal · índex d'envelliment 182

CONTEXT COMARCAL: població mediana 260 hab · IETR mitjà 38,9 · el Berguedà és rural i envellit, amb un extrem turístic (Gósol, Castellar, Saldes) i una capital de serveis (Berga).
CAVEATS: les 3 capes i els gaps són INFERÈNCIA. Inferència sobre senyals físics, no cens.
[Composició d'origen/arrelament: capa SENSIBLE, FORA de la interpretació v1 (vegeu el CSV/SQLite si la vols consultar a banda).]
