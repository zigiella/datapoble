# Sitemap complet — totes les fitxes de Catalunya

**Data:** 2026-06-18
**Autora:** Talaia (encarna Mirador/web)
**Latido (Bea):** «a tope». Tanca un buit introduït per #146.
**Status:** a la porta del PR (branca `fix/sitemap-tota-catalunya`). Avança la part «sitemap» de P0 #6.

## Què he fet
Amb #146 vam passar de 113 a **947×2 fitxes** de municipi prerenderitzades, però el sitemap encara
enumerava només els 31 del Berguedà (`dataset.municipis`). Ara el sitemap es genera des del
**catàleg** (mateixa font que `municipi/[slug]` `entries()`): **1.908 URLs** (947 munis × 2 locales
+ estàtiques), cada una amb els seus alternates ca/es/x-default.

És la **bastida** pre-llançament (el lloc segueix `noindex`); no és l'acte de publicar. Treure el
noindex (×3) + og:image + deploy segueixen sent el ritual del dia D (#6), intactes.

## Verificat
- `svelte-check` 0/0 · `build` OK · `grep -c <loc>` = 1.908 · munis de fora del Berguedà presents
  (Roses, Salou).

— Talaia 🌊
