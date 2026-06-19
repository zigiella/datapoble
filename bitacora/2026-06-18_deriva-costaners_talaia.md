# Derivació geomètrica dels municipis costaners (cross-check per al Nivell C)

**Data:** 2026-06-18
**Autora:** Talaia (encarna Sondeig/dades)
**Latido (Bea):** «deriva tu, però en paral·lel vaig a investigar la llista costanera».
**Status:** derivació feta (tool + CSV). Prerequisit de P0 #1 (estendre Nivell C), que segueix
**en pausa** («en parlem»): la classificació costanera definitiva es decidirà encreuant aquesta
derivació amb la llista OFICIAL que investiga la Bea.

## Què he fet
`tools/deriva_costaners.py`: deriva la llista de municipis costaners intersecant la geometria
municipal (INE/IGN) amb el polígon de mar de **Natural Earth 1:10m** (domini públic, citable). NO
inventa res; mètode = distància al mar amb llindar (les dues fonts no casen perfectament → distància,
no intersecció estricta). Sortida `data/territorial/municipis_costaners.csv` (ine5, nom, costaner,
dist_m). El cache de l'oceà va a `data/eval/` (gitignored).

## Troballes
- **83 candidats** a ≤1.500 m. El **nucli (~70, a 0–500 m)** és correcte (Barcelona, Roses, Palamós,
  Cambrils, Salou, Deltebre, l'Escala…).
- La **cua (500–1.500 m)** cola la **segona fila** per la generalització de la costa de NE 10m:
  Premià de Dalt, Vilassar de Dalt, Teià, Alella, Argentona, Vinyols i els Arcs, Sant Boi de
  Llobregat, la Riera de Gaià, Santa Cristina d'Aro… → **falsos positius** que la llista oficial
  resoldrà net.
- **NE 10m és aproximat a escala municipal** (costa generalitzada ~centenars de m): no hi ha un tall
  net. Per això la derivació és un CROSS-CHECK, no l'autoritat.
- **Pesca de qualitat:** la llista a mà de `nivellc_analisi.py` marcava **Vespella de Gaià** com a
  costaner i NO ho és (municipi d'interior, Gaià). La derivació no el flagueja → cal corregir-ho
  quan es reprengui #1.

## Pendent (a parlar amb Bea)
Encreuar amb la llista oficial → fixar la classificació costanera definitiva; després reprendre #1
(estendre el model, re-validar held-out per comarca/tipus). La derivació aïlla els ~10–13 casos
dubtosos que cal resoldre.

— Talaia 🌊
