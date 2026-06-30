# Vot de direcció · els tres registres (el nus «verificat-primer vs costura», resolt)

**Data:** 2026-06-29 · **De:** Bea (direcció) amb el rumb de Rapaz (consultoria) · **Síntesi al repo:** Talaia.
**Estat:** decisió presa, executable. *(El document verbatim de la Bea és input no versionat; aquest n'és l'artefacte versionat — el repo és la veritat.)*

> El nus estava mal plantejat. **No es vota una arquitectura: es mira el número i es deixa que tracti la
> línia.** El número —**99 dels 441 municipis <1.000 hab passen el llindar de senyal** (l'interval de
> pernocta exclou el padró)— dibuixa una **tercera arquitectura**, més honesta que el «verificat-primer»
> i que la «costura» original. Recalculable: [`tools/senyal_sub1000.py`](../../tools/senyal_sub1000.py)
> → `data/territorial/senyal_sub1000.csv` (66 «hi dorm més» + 33 «menys» + 342 soroll).

## La decisió, en una frase

Ni publicar tot el <1.000, ni amagar-lo tot. **Publicar el que el nostre propi sistema distingeix del
seu soroll**, amb veu graduada per magnitud, i replegar la resta a base oficial. **La frontera no és la
població del municipi; és si la nostra estimació es distingeix del nostre error.**

## Els tres registres

1. **Verificat oficial · sense reserva.** Els 947 amb padró, habitatge, renda, residus + ETCA als 486 de
   ≥1.000. Terra ferma. Es publica sempre, a tot arreu.
2. **Costura amb veu graduada · els ~99.** Els <1.000 on l'interval de pernocta exclou el padró (l'única
   porta auditable sense ETCA). Es publiquen per municipi, en rang, amb el criteri escrit al darrere. La
   **magnitud no decideix si entren**: modula com hi parlen (veu més ferma com més l'exclou; rang i to
   més prudents com més just sigui el marge).
3. **Base oficial i prou · els 342 + 20.** Soroll (l'interval inclou el padró) i sense estimació (els 20
   micromunis). No es pinta el gap (no es distingeix del marge); es replega amb el motiu visible:
   «estimació no distingible del marge, vegeu metodologia».

## Dues precisions que no es poden saltar

- **La «segona porta» dels 151 no existeix aquí.** Als 8, la segona porta era |ETCA|≥5% (corroboració
  oficial independent). Aquest univers, per definició, **no té ETCA**. Exigir més magnitud no és
  corroboració externa: és el mateix model parlant més fort, i un model pot estar molt segur i
  sistemàticament equivocat (el règim dens). **Per tant la magnitud va al to, no al llindar.**
- **El que els 99 són i el que no són.** Han passat un llistó **intern**, no una validació externa («el
  model n'està segur», no «està comprovat»). A favor seu: la banda ja va eixamplada ×1,5 i tot i així el
  padró en queda fora (robust); i s'agrupen a `interior_rural` (calibra al 79,6%) i en territori de
  segona residència real (Cerdanya, Empordà, Pirineu). Que el model apunti on el sentit comú també
  apuntaria **no el valida** — és la prova que podia suspendre i no ha suspès, no la que el corona.

## Què executa la Talaia

- [x] **Eina auditable** `tools/senyal_sub1000.py` amb `--check` i sortida CSV (com els 151) + a CI.
- [ ] **Magnitud com a graduació** (no segona porta): els 99 entren tots; `marge_rel_pct` fixa rang i to.
- [ ] **Costura a la fitxa** amb els tres registres (desbloqueja el pas pendent de Fase 1).
- [ ] **Cobertura per tipus a /metodologia sempre amb la n** (a n=7-9 el % és gairebé soroll).

## La reclassificació que se'n deriva

El **test multianual** (2013–2024 a la raw d'ICAEN, ara un sol tall en ús) deixa de ser «oportunitat
futura»: passa a ser **la via de validació dels 99** —un gap que persisteix any rere any puja de «el
model n'està segur» a «ho hem comprovat en el temps»—. És l'única porta oficial que aquest univers sense
ETCA podrà tenir mai. No s'executa ara, però canvia d'estatut al full de ruta.

— Bea, amb Rapaz · *síntesi i execució: Talaia 🌊*
