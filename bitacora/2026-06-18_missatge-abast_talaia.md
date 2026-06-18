# Missatge d'abast honest «tota Catalunya»

**Data:** 2026-06-18
**Autora:** Talaia (encarna Mirador/Llegenda)
**Latido (Bea):** «a tope». Tanca P0 #5 de `next.md`.
**Status:** a la porta del PR (branca `feat/missatge-abast`).

## Què he fet
Tancada la trilogia «tota Catalunya» (cercar → fitxes → **dir clarament què cobrim**). Que «sense
dades» es llegeixi com a honestedat, no com a producte incomplet.

1. **Home** — línia d'abast sota el mapa (`home_map_scope`): «Tota Catalunya, amb honestedat: dades
   completes al Berguedà, una presència estimada en rang a molts municipis i la resta com a context,
   "sense dades encara". Cap xifra sense procedència.»
2. **`map_outside_scope` revisat** (estava estancat: deia «avui mesurem el Berguedà; la resta és
   context» — ignorava els 82+ munis en rang). Ara reflecteix els 3 nivells. S'usa al tooltip del
   mapa i a l'estat «sense dades» de la fitxa → coherència a tot arreu.

Còpia provisional (dr/Talaia); el to fi és vot narratiu de Bea —són claus i18n, fàcils d'afinar.

## Verificat
- `svelte-check` 0/0 · `build` OK · la línia surt a la home en ca i es (HTML prerenderitzada).

— Talaia 🌊
