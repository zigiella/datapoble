# Tauler v2 — esmenes de Bea (2026-07-19) · vinculants

Revisió del mode govern un cop vist en viu. **Manen sobre C6 i sobre la gorra §3** allà on
discrepin. Estat del terreny verificat per Talaia abans d'especificar (què tenim de veritat).

---

## 1. Les 12 esmenes

| # | Esmena de Bea | Front | Estat de la dada |
|---|---|---|---|
| E1 | **Una sola vista, «Tauler de dades»** — fora el commutador Veïnal/Govern | Mirador | — (copy/estructura) |
| E2 | **Indicadors de «vida» junts**: residus kg/hab + **elèctric domèstic kWh/hab** + **vidre kg/hab** | Mirador | ✅ les tres mètriques existeixen |
| E3 | «Establiments / 1.000 hab» → **«Establiments turístics / 1.000 hab»** | Mirador | ✅ la mètrica és `rtc_per_1000hab` (Registre de Turisme): l'etiqueta actual és **imprecisa**, la nova és la correcta |
| E4 | **Cal posar l'atur** al tauler | Sondeig + Mirador | ✅ dada al mart (`mart_pols_mensual`, 224k files); falta l'**export web** |
| E5 | **Cada quan s'actualitza cada dada** + **processos d'actualització** | Sondeig | ⚠️ cadència NO és al contracte; només existeix `refresh-atur.yml` |
| E6 | **Indicadors de tendència** (puja/baixa vs període anterior; quins períodes?) | Sondeig + Mirador | ⚠️ **PARCIAL** — vegeu §2 |
| E7 | **Repassar P1/P2**; que no citin mètriques antigues (aparcades) | gen_fitxa | ⚠️ pendent (era B1) |
| E8 | **«Confiança mitjana»** a P1: un usuari normal no sap què vol dir | gen_fitxa/Mirador | — (copy) |
| E9 | **Rang comarcal al % nacionalitat estrangera** | Mirador | ✅ el rang existeix; estava retingut esperant el vot — **ara s'hi posa** |
| E10 | **Fora la frase** «Renovació demogràfica: l'entrada de gent nova…» | Mirador | — (copy) |
| E11 | «Qui hi ha (i qui hi haurà)»: **evolució de població, de nascuts fora de Catalunya i de nascuts a l'estranger** | Sondeig + Mirador | 🟡 origen ✅ (finestra 2021→2025); població: **verificar sèrie a EMEX** |
| E12 | **Franges d'edat** (quanta gent a cada franja) **i la seva evolució** | Sondeig + Mirador | ✅ **ja ingerides** (`pob_0_14`, `pob_65_84`, `pob_85_mes`) — el mart les usa i les llença |

## 2. La veritat sobre la TENDÈNCIA (E6) — regla d'honestedat

**Només es mostra tendència on hi ha sèrie real.** Inventar un «puja/baixa» sense període anterior
seria exactament el pecat que aquest projecte no comet.

| Família | Sèrie disponible | Tendència v2 |
|---|---|---|
| **Atur** | mensual 2006→2026 (SEPE) | ✅ Δ mes anterior + Δ mateix mes any anterior (estacionalitat!) |
| **Origen** (estrangera) | finestra 2021→2025 (Cens anual, `mart_demografia`) | ✅ Δ de la finestra (ja calculat: +5,61 pts, +64 persones a la Pobla) |
| **Població / franges d'edat** | EMEX porta `year` a la ingesta crua → **Sondeig verifica si es pot demanar sèrie** | 🟡 si hi és, Δ; si no, «sense sèrie» |
| **Renda · habitatge · residus · energia · RTC** | una sola foto | ❌ **«sense sèrie encara»** — explícit a la targeta, i la ingestió de sèrie s'encua |

**Cap targeta amb fletxa sense període.** Tota tendència diu **contra quin període** compara
(«vs juny 2025», «2021→2025»). Sense això, no es mostra.

## 3. La frescor (E5) — dues coses, no una

1. **Declarar la cadència al contracte**: camp nou per font/mètrica (`actualitzacio: mensual |
   anual | puntual | irregular`) + la **data de la dada** (ja hi és) + **data de la darrera
   càrrega**. El tauler ho mostra a cada xifra («mensual · darrera: 2026-06»).
2. **Tenir els processos**: avui només `refresh-atur.yml`. Cal inventariar per font quin procés
   la refresca (cron, manual documentat, o cap) i **dir la veritat quan no n'hi ha** — una dada
   anual sense procés és honesta si es diu; una que sembla viva i no ho és, no.

## 4. El que NO canvia

La regla de ferro (C6 §8.1): **cada xifra amb la seva font o fórmula**. Les esmenes hi sumen
(cadència i tendència), no la substitueixen. I la política editorial del §7: cap indicador es
retira ni es suavitza perquè incomodi.
