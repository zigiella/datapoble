# Fase nova — inventari d'aparcaments i mancances (auditoria 2026-07-16)

**Mandat de Bea:** fase orientada 100% a dashboard útil + radar; el que no hi serveixi, parat i/o
aparcat. **El model d'estimació de pernocta queda APARCAT** (decisió registrada a la bitàcola).
Auditoria feta per 2 agents (web + operativa) i verificada per Talaia. **Els APARCAR de peces
VISIBLES són proposta: cada retirada de pantalla passa pel vot narratiu de Bea abans d'executar-se.**

## A. Peces del MODEL visibles al web — proposta APARCAR (vot de Bea, peça a peça)

| # | Peça | On | Nota |
|---|---|---|---|
| A1 | Beeswarm/waveform del gap | home + comarca/[slug] | 100% model; era la peça central de la home |
| A2 | Banda pernocta + tres registres + veu del gap | fitxa municipi | on hi ha ETCA, l'ETCA es queda sola |
| A3 | Avís de col·lisió (#237) | fitxa municipi | cau amb la banda (sense banda no té subjecte); `distinguish.ts` es conserva dorment com a candau |
| A4 | Bloc E «les 3 capes» + card «qui hi dorm» | fitxa municipi | el card passa a ETCA oficial o «sense dada oficial» |
| A5 | Confiança del model (score, divergència, validats) | fitxa municipi | les dades oficials porten font+data, no bandera |
| A6 | `gap_pernocta_pct` com a indicador per defecte | /mapa | mínim: defecte → `pct_noprincipal` i treure'l del selector |
| A7 | Tooltip de rang (pernocta) al mapa de la home | home | el mapa es queda (indicador oficial); es poda el tooltip |
| A8 | Família pernocta al glossari | /glossari | ampliar HIDDEN (retoc d'una llista) |
| A9 | Seccions G/H/I del model a /metodologia | /metodologia | moure a annex de recerca o etiquetar «model aparcat» |
| A10 | Stubs morts `/index` (IETR) i `/day-tripper` | routes | orfes de nav; fora |

## B. Peces que es REGENEREN (el mecanisme val, el contingut cita el model)

| # | Peça | Acció |
|---|---|---|
| B1 | Lectures-IA de la fitxa (P1/P2) | regenerar amb `gen_fitxa.py` sobre dades oficials abans d'entrar al mode govern |
| B2 | Pobles mirall (constel·lació) | recalcular el vector sense la component de presència, o aparcar fins llavors |
| B3 | Xips d'exemple de /pregunta-li | citen `gap` i `IETR` → re-basar en KPIs oficials (+ les 8 preguntes curades de C6 §6) |

## C. El que es MANTÉ (esquelet del dashboard, tot oficial)

Home (cercador + portes + mapa amb `pct_noprincipal`) · fitxa: espina, veïns, selector, blocs A–D
oficials (8 dels 12 KPIs ja hi viuen) · /pregunta-li (UI + API viva) · /comarca i /vegueria ·
/glossari (retocat) · deploy Cloudflare + domini.

## D. Estat operatiu real (sorpreses de l'auditoria)

- ✅ **El web és ONLINE** (Cloudflare Pages + `riusdegent.cat`); el comentari «DORMENT» de
  `deploy-web.yml` és ranci.
- ✅ **X2 està FET de facto**: Render viu, `api.*` connectada, CORS resolt, secret posat. La cua de
  Trazo es buida; queden comentaris rancis a `render.yaml` (higiene d'una línia).
- ⚠️ **Render free tier s'adorm** (~15 min) i el cold start és ~1 min: el mode de fall exacte del
  moment «xat en directe». Abans de presentar res: **always-on ~7 $/mes (decisió de Bea)**.
- ⚠️ **Drift** entre `render.yaml` i l'entorn viu del Dashboard de Render: innocu avui, però el repo
  ha de tornar a manar abans de cap demo.
- ⚠️ **noindex actiu ×3**: el site és invisible a cercadors. No bloqueja ensenyar-lo amb URL;
  bloqueja «que ens trobin». Decisió de llançament de Bea, que no s'oblidi.
- ❌ **Cap workflow refresca dades avui**: el mart mensual de l'atur necessita un cron mensual nou
  (el `daily-report` no toca dades). S'afegeix al llistó de D1.
- ❌ **`main` segueix vermell a signals** (desquadre ~7,67 M€) amb el CI acotat — pas 2 de la cua de
  Sondeig, abans que R2/R3/R4 apilin codi sobre `signals`.

## E. El camí crític fins a «online i funcionant» (criteri de Bea)

**Dashboard:** D1 (atur) → D4 (mart_govern + rangs k-de-31) → D5 (vista govern) → aparcaments A1–A10
executats → B1–B3 regenerats. **Radar:** R2 (filtre + `config/`) → R3 (semàfor) → R4 (correu a Bea)
→ banc C4 (**les etiquetes de Bea es poden demanar JA — és la palanca més barata del calendari**) →
1 mes de validació paral·lela. **Xat:** X3 (catàleg govern) darrere de D1/D4.

## F. Dubtes oberts (per a Bea o per als fronts)

1. **«Gobrem»** — ¿Gósol o Gironella? (cap perfil fins a confirmar).
2. **`index_turisme` com a KPI 7 de la gorra**: satura a 100 en 47 municipis (2 dels 6 candidats
   nostres al topall!). ¿El substituïm pel parell cru (RTC/1000 + % no principal, que ja hi són) i
   l'índex compost s'aparca amb els altres? *(Recomanació de Talaia: sí — un índex que satura no
   discrimina, i el tauler ja porta els dos crus.)*
3. **El /mapa tot-Catalunya**: ¿aparador públic (mantenir podat) o fora de la fase (aparcar)?
4. **Les 26 fixtures de R1** esperen l'etiquetatge daurat de Bea (criteri escrit a punt quan vulgui).
