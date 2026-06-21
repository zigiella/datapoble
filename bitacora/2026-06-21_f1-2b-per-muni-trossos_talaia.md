# F1.2b · Connectors per-muni a TROSSOS (EMEX/origen) — Barcelona provat en viu

**Data:** 2026-06-21
**Autora:** Talaia (encarna Sondeig)
**Latido (Bea):** «fem EMEX/origen per trossos? primer totes les comarques de Barcelona?».
**Pla:** [docs/pla-catalunya-profund.md](../docs/pla-catalunya-profund.md) §F1.2b.

## Per què a trossos
Els connectors per-muni (EMEX, demografia/origen) fan crida lenta i escrivien amb **sobreescriptura
total** → trossos ingenus s'esborraven entre si. He afegit **acumulació per tros**: carreguen el
parquet existent, en treuen els municipis del tros (els refresquen) i hi concatenen els nous. Així
província rere província s'**acumula** i re-córrer un tros és **idempotent**. De-risca la baixada
llarga (~2.800 crides) i permet verificar a cada pas.

## Què he fet
- `idescat_emex.py` i `demografia_origen.py`: paràmetre `accumulate` (default `False` = sobreescriu,
  pilot Berguedà; `True` = acumula per tros). Procedència informa munis totals + munis del tros + mode.
- `__main__.py`: bandera **`--provincia {08,17,25,43}`** (08=Barcelona…) que subdivideix els per-muni
  en trossos acumulables. Requereix `--scope catalunya`; només aplica als per-muni (els altres, omesos).
  Recompte: Barcelona 311 · Girona 221 · Lleida 231 · Tarragona 184 = 947.

## Provat EN VIU — tros Barcelona (311 munis)
| Font | resultat |
|---|---|
| EMEX | 311 munis (100% província 08), 13 indicadors, 3.776 files |
| origen (snapshot) | 311 munis, 6.531 files |
| origen (sèrie estrangera) | 311 munis, 1.555 files |

Sortida a `data/raw` (gitignored). El pilot Berguedà queda intacte (`accumulate=False` per defecte).

## Següent
Acabar els altres 3 trossos (Girona, Lleida, Tarragona) per completar el raw local dels 947 — al
ritme que Bea vulgui. Després **F2**: unificar el model (base Nivell C + z-scores per tipus) i
re-materialitzar els marts a 947 (instal·lar dbt). L'OSM segueix diferit a la segona onada.

— Talaia 🌊
