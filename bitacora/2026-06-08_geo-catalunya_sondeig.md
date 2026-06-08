# Geometria de tot Catalunya per al mapa (municipis + comarques) — Sondeig

**Fecha:** 2026-06-08
**Autora:** Sondeig (dades)
**Para:** Talaia (review/merge) · Mirador (consumidor a `packages/web`, FYI)
**Tema:** anticipant l'escala país, genero les dues capes oficials de Catalunya en GeoJSON WGS84, simplificades per al web, amb `ine5` per fer join amb `mart_municipi`. Fins ara només teníem el Berguedà (31 munis).
**Status:** fet, verificat / handoff

## Contexto
El mapa coroplètic només tenia `bergueda-municipis.geojson` (31 munis, pilot). Per saltar a
Catalunya cal la geometria de **tots** els municipis (~947) i de les **comarques** (~42), amb el
mateix format/contracte que el Berguedà: `FeatureCollection`, clau de join **`ine5`** (5 dígits),
projecció **EPSG:4326 (lon/lat)** com vol MapLibre, i prou lleuger per servir-se estàtic.

## Qué hicimos / decidimos

### Font: ICGC (no Opendatasoft)
- **ICGC — Divisions administratives v2r2, 2026-01-20, llicència CC-BY 4.0.** Descàrrega directa
  de GeoJSON ja en **EPSG:4326** des de
  `https://datacloud.icgc.cat/datacloud/divisions-administratives/json_unzip/`.
- Fitxers d'origen (carpeta `json_unzip/`, una variant per escala de generalització):
  - Municipis: `divisions-administratives-v2r2-municipis-250000-20260120.json` (font 1:250.000).
  - Comarques: `divisions-administratives-v2r2-comarques-1000000-20260120.json` (font 1:1.000.000).
- **Per què ICGC i no Opendatasoft `georef-spain-municipio`** (la font del Berguedà):
  - ICGC dóna **exactament 947 municipis** (compte oficial); Opendatasoft en donava **948** per a
    Catalunya (un de més, sense duplicat de codi → no fiable per al compte exacte).
  - ICGC porta el **codi de comarca a cada municipi** (`CODICOMAR`/`NOMCOMAR`) i, sobretot,
    **té capa de comarques pròpia** — Opendatasoft `georef-spain` NO té comarques (només
    municipi/província/CA; la comarca és una divisió catalana que no hi és).
  - És la **font preferent** del brief (institut oficial) i els noms ja vénen en **català**
    (coincideixen amb el Berguedà).
  - Trade-off: ICGC i Opendatasoft no són byte-idèntiques, així que la geometria dels 31 munis del
    Berguedà a la capa Catalunya **no és la mateixa** que `bergueda-municipis.geojson` (font i
    simplificació diferents). El que importa —els **codis `ine5`**— sí que casa 31/31 (verificat).

### El codi: `CODIMUNI` (6 dígits) → `ine5` (5)
Trampa important: ICGC identifica el municipi amb **`CODIMUNI` de 6 dígits** = INE5 + **dígit de
control**. Ex.: Abrera `080018`→`08001`, Avià `080116`→`08011`. El nostre `ine5` és els **5 primers
dígits** de `CODIMUNI` (verificat: 947/947 donen un INE5 vàlid i únic, i els 31 del Berguedà casen).
- Municipis: `ine5 = CODIMUNI.substr(0,5)`, `nom = NOMMUNI`. Es **descarten** la resta de camps.
- Comarques: `id = CODICOMAR` (2 dígits), `nom = NOMCOMAR`, `cap = CAPCOMAR` (capital, extra útil).

### Simplificació (mapshaper, Visvalingam ponderat)
L'oficial és pesat → `npx mapshaper` amb `-simplify <pct>% weighted keep-shapes` (preserva la
topologia i evita esborrar illes/munis petits) i `-o precision=0.00001` (5 decimals ≈ 1,1 m, igual
que el Berguedà). Comandes exactes (reproduïbles):

```
# Municipis (font 1:250.000) → ~1,0 MB
npx mapshaper divisions-administratives-v2r2-municipis-250000-20260120.json \
  -each 'ine5=String(CODIMUNI).substr(0,5), nom=NOMMUNI' \
  -filter-fields ine5,nom \
  -simplify 15% weighted keep-shapes \
  -o precision=0.00001 format=geojson catalunya-municipis.geojson

# Comarques (font 1:1.000.000) → ~224 KB
npx mapshaper divisions-administratives-v2r2-comarques-1000000-20260120.json \
  -each 'id=CODICOMAR, nom=NOMCOMAR, cap=CAPCOMAR' \
  -filter-fields id,nom,cap \
  -simplify 15% weighted keep-shapes \
  -o precision=0.00001 format=geojson catalunya-comarques.geojson
```
(Després, un pas de post-procés afegeix el bloc `meta` i ordena les features per codi, per a diffs
estables. El `meta` de cada fitxer documenta font, URL, CRS i tolerància.)

- **Tolerància triada:** municipis **15%** des de la font 1:250.000 (vèrtexs retinguts) → **1.046.764 B
  (~1,02 MB)**, objectiu < 1,5 MB ✔. Comarques **15%** des de 1:1.000.000 → **229.427 B (~224 KB)**,
  objectiu < 300 KB ✔. (Per a munis vaig provar 8–18%: 8%→672 KB, 18%→1,21 MB; 15% és el punt dolç
  amb marge.)

## Por qué
- **EPSG:4326** perquè MapLibre vol lon/lat; el Berguedà ja hi és.
- **`keep-shapes`** perquè sense això la simplificació forta es menja municipis diminuts (Gisclareny,
  Sant Jaume de Frontanyà…) i perdríem features → el join amb el mart quedaria coix.
- **Dues capes independents** (munis de 250k, comarques de 1M): el brief les demana com a capes
  separades amb pressupostos de mida propis. **Conseqüència honesta:** com que se simplifiquen per
  separat i de fonts d'escala diferent, el contorn d'una comarca **no coincideix píxel a píxel** amb
  la unió dels seus municipis. Per a un coroplètic on les capes es pinten per separat (o la comarca
  com a vora gruixuda a sobre) és l'esperat i acceptable. Si algun dia es vol perfecte encaix,
  caldria dissoldre les comarques DES dels municipis (mapshaper `-dissolve CODICOMAR`) sobre la
  mateixa font — anotat com a millora futura, no necessari ara.

## Verificación
- **Comptes:** municipis **947** features / **947** `ine5` únics ; comarques **43** features / **43**
  `id` únics.
  - Nota comarques: **43 = 41 comarques + Val d'Aran + Lluçanès**. L'Aran és entitat territorial
    singular i el Lluçanès és la comarca creada el 2023; ICGC v2r2 (2026) les inclou. El brief deia
    «~42»; 43 és el compte oficial actual.
- **`ine5`:** 0 malformats (tots casen `^[0-9]{5}$`); derivats de `CODIMUNI` oficial.
- **Berguedà:** els **31/31** `ine5` de `bergueda-municipis.geojson` hi són i casen; **0**
  discrepàncies de nom (insensible a article/majúscules). Inclou els casos delicats: Gósol `25100`
  (província 25/Lleida però comarca 14/Berguedà), Sant Julià de Cerdanyola `08903`.
- **GeoJSON vàlid:** parsejat amb dos camins independents (node propi + `mapshaper -info`):
  `FeatureCollection` correcte, **0 geometries nul·les/buides**, tots els anells tancats (≥4 punts),
  totes les coordenades dins la bbox de Catalunya (lon 0,1–3,5 / lat 40,4–42,95), precisió ≤ 5
  decimals.

## Pendiente / handoffs
- [ ] **Talaia:** review/merge. Toco NOMÉS els dos GeoJSON nous a `packages/web/static/geo/` + aquesta
      bitàcola (cap codi del web, cap mart, cap contracte).
- [ ] **Mirador (FYI):** les dues capes ja són a `static/geo/`. Mateix contracte que el Berguedà
      (`properties.ine5` + `nom` als munis; `id`+`nom`+`cap` a les comarques). Per a l'escala
      Catalunya pots substituir/afegir la font del mapa quan toqui. La geometria del Berguedà dins
      `catalunya-municipis` NO és byte-idèntica a `bergueda-municipis.geojson` (font ICGC vs
      Opendatasoft); el join per `ine5` és el mateix.
- [ ] **Sondeig (jo, futur):** quan el mart passi de 31 a 947 munis, aquesta geometria ja hi és a punt.
      Millora opcional: comarques dissoltes des dels municipis per a encaix perfecte de vores.

## Enlaces
- `packages/web/static/geo/catalunya-municipis.geojson` (947 munis, ~1,02 MB, `ine5`+`nom`)
- `packages/web/static/geo/catalunya-comarques.geojson` (43 comarques, ~224 KB, `id`+`nom`+`cap`)
- Font: ICGC Divisions administratives v2r2 (2026-01-20), CC-BY 4.0 —
  https://datacloud.icgc.cat/datacloud/divisions-administratives/json_unzip/
- Format de referència: `packages/web/static/geo/bergueda-municipis.geojson`
