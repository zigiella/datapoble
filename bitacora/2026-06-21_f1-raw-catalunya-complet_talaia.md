# F1 · Raw de tot Catalunya COMPLET (espina) — baixat i verificat

**Data:** 2026-06-21
**Autora:** Talaia (encarna Sondeig)
**Latido (Bea):** «fem EMEX/origen per trossos? primer Barcelona?» → fet Barcelona i, com que el
mecanisme va net, completades les altres 3 províncies.

## Estat: F1 (ingesta a tot CAT) essencialment FET
Tots els connectors de l'espina baixats a escala Catalunya (sortida a `data/raw`, **gitignored** →
aquesta bitàcola és el registre durable que el raw existeix; és **regenerable** re-corrent els
connectors, ~20 min):

| Font | munis | nota |
|---|---|---|
| residus (ARC) | 949 | inclou 2 codis junk/obsolets; s'imposarà el cens 947 a transform |
| rtc (turisme) | 922 | no tots tenen allotjament (turisme concentrat) — esperat |
| icaen_consum (elèctric) | 947 | cobertura plena |
| electoral | 951 | inclou codis extra; s'imposarà el cens 947 |
| EMEX (Idescat) | 947 | per-muni, 4 trossos de província acumulats |
| origen snapshot | 947 | per-muni |
| origen sèrie estrangera | 947 | per-muni |

Baixada per-muni feta **a trossos de província** (Barcelona 311 · Girona 221 · Lleida 231 ·
Tarragona 184 = 947), acumulant sense esborrar. El pilot Berguedà segueix intacte.

## El que queda fora d'aquesta espina
- **OSM (restauració/serveis)**: diferit a la **segona onada** (OSM infra-mapa el rural → mínim, no
  cens; pla §3.4). Encara acotat al Berguedà.

## Següent: F2 (el cor metodològic)
Instal·lar dbt-duckdb · des-acotar `dbt_project.yml` (comarca, n_municipis) · **unificar el model**
(base Nivell C en lloc de la fixa 1224 —ja provat que millora el Berguedà, PR #161— i z-scores per
`tipus_territorial` en lloc de comarca) · re-materialitzar els marts a **947** · **re-validar el
Berguedà contra l'ETCA** (guardó: no regressar la joia). Llavors els marts (versionats) passen de 31
a 947 i la dada profunda existeix a tot CAT.

— Talaia 🌊
