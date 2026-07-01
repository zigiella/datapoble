"""Fase 2 · la regla de distingibilitat — TORCH-FREE, pura (números → bool).

Una sola regla per als DOS usos (contracte 04-fase2-distingibilitat.md):

  1. Ordenació entre municipis (comparació): dos munis només es poden ORDENAR si la
     distància entre les seves estimacions supera la incertesa combinada de les bandes.
     Si les bandes s'encavalquen → NO distingibles → abstenció d'ordenar.
  2. Modulació per σ sobre un municipi: el mateix σ (la banda) governa el to.

La col·lisió exacta de la Fase 1 (dos munis amb el MATEIX número i banda) és el CAS LÍMIT
d'aquesta regla a distància zero: bandes idèntiques → s'encavalquen del tot → no
distingibles. NO és un mecanisme a part — la Fase 1 i la Fase 2 criden aquesta mateixa
funció. Si decidissin distingibilitat per camins diferents, tard o d'hora es
contradirien.

Aquest mòdul és PUR (números entra, bool surt) precisament perquè tots dos usos i els
tests cridin la MATEIXA funció.
"""

from __future__ import annotations

# El llindar per defecte. min_gap=0.0 vol dir: QUALSEVOL solapament de la banda p10–p90
# (la banda JA calibrada, cobertura 78,4%) implica NO distingibles. És el criteri net i
# auditable del contracte, sense inventar cap paràmetre nou.
#
# Un min_gap>0 (p. ex. exigir que la distància superi la meitat de la suma de semiamplades)
# és un PARÀMETRE DE METODOLOGIA DECLARAT, mai la veritat — igual que el |ETCA|≥5% dels 151.
DEFAULT_MIN_GAP = 0.0


def overlaps(a_low: float, a_high: float, b_low: float, b_high: float) -> bool:
    """True si els intervals [a_low, a_high] i [b_low, b_high] s'encavalquen.

    Encavalquen sii max(a_low, b_low) <= min(a_high, b_high). Bandes idèntiques
    s'encavalquen (el cas límit de la col·lisió exacta a distància zero).
    """
    return max(a_low, b_low) <= min(a_high, b_high)


def distinguishable(
    a_low: float,
    a_high: float,
    b_low: float,
    b_high: float,
    min_gap: float = DEFAULT_MIN_GAP,
) -> bool:
    """True sii els intervals són disjunts per sobre de min_gap.

    Amb min_gap=0.0 (per defecte): QUALSEVOL solapament p10–p90 → NO distingibles.
    És la regla neta i auditable del contracte, sobre la banda ja calibrada.

    La separació (gap) entre dos intervals disjunts és la distància entre l'extrem alt del
    de sota i l'extrem baix del de dalt:  gap = max(a_low, b_low) - min(a_high, b_high).
    Són distingibles sii aquesta separació > min_gap. Bandes idèntiques → gap = negatiu →
    no distingibles (el cas límit de la Fase 1).

    Un min_gap>0 és un llindar de metodologia declarat, mai la veritat.
    """
    gap = max(a_low, b_low) - min(a_high, b_high)
    return gap > min_gap
