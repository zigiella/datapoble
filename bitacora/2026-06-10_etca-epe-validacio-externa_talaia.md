# Verificació ETCA / EPE (Idescat) com a àncora externa

**Fecha:** 2026-06-10
**Autora:** Talaia (coordinació / recerca)
**Tema:** quick win del repàs del pla — comprovar si les estimacions de població estacional d'Idescat (ETCA) baixen a municipi i poden validar externament el nostre `carrega_funcional_est` / «població real». Verificació, no integració.
**Status:** aprenentatge

## Què és
**EPE — Estimacions de Població Estacional** (Idescat). Unitat: **ETCA** = població equivalent a temps complet anual (1 dia-persona = 1/365 ETCA). Estima la **càrrega de població** que suporta un municipi —residents + treballadors + estudiants + visitants temporals— amb desglossament **trimestral** (estacionalitat). Des de la base **2022** hi afegeix una estimació de **pernoctacions en allotjament turístic** i de turistes.

→ **És, conceptualment, gairebé exactament el nostre `carrega_funcional_est`** (el «denominador per governar»), però **oficial**. Per tant, l'àncora externa **discriminant** (no circular) que ens faltava: avui l'única «validació» és Spearman(IETR, residus), gairebé circular (L2 *són* residus).

## El límit: granularitat
Es publica a **Catalunya · comarques · municipis ≥ 1.000 habitants** (des de 2021; abans del 2020, >5.000 + capitals de comarca). Verificat sobre el nostre parquet:
- **Cobreix 8 dels 31 munis del Berguedà** (≥1.000 hab): Berga, Gironella, Puig-reig, Avià, Bagà, Casserres, Cercs, Olvan.
- **NO cobreix 23 munis** (<1.000) — i entre ells, **precisament els turístics extrems** (Castellar de n'Hug #1 IETR, Gósol, Saldes, Capolat…), que són els casos que més voldríem validar.
- **Comarca (Berguedà):** sí disponible → sostre agregat / forma de corba.

## Recomanació (alimenta el pas «bases esperades + escala»)
1. **Usar l'ETCA com a àncora externa a dos nivells:** (a) **municipal** per als 8 munis ≥1.000 → comparació DIRECTA `carrega_funcional_est` vs ETCA (validació discriminant real); (b) **comarcal** com a sostre agregat per **calibrar les bases** (la crítica de circularitat de la consultora).
2. **Per als 23 petits** (els turístics): no hi ha àncora municipal → mantenir el caveat honest i recolzar-se en l'enfocament **comarcal/tipològic** (és el pla de bases jeràrquiques).
3. **ull a l'estacional i a les pernoctacions (2022):** dos senyals externs addicionals per a L1/turisme.

## Pendiente (futur, Sondeig — no aquesta tasca)
- [ ] Ingerir EPE municipal (`idescat id=epe`, `by=mun`) Berguedà ≥1.000 + comarcal i comparar amb `carrega_funcional_est`.
- [ ] Afegir una fila ETCA/EPE a `docs/poblacio-real-fonts.md` (inventari de fonts).

## Enlaces
- https://www.idescat.cat/pub/?id=epe · https://www.idescat.cat/pub/?id=epe&n=9522&by=mun
- `docs/poblacio-real-fonts.md` · `docs/feedback-consultora-i-roadmap.md` (§7 referents externs)

— Talaia 🌊
