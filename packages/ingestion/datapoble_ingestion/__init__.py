"""datapoble · ingestion — connectors a fonts obertes amb procedència.

Scope d'aquest PR: Berguedà (31 municipis). Fonts actives:
  - RTC (Registre de Turisme de Catalunya)  · Socrata t2h3-cgys
  - Residus municipals (ARC)                 · Socrata 69zu-w48s
  - Idescat EMEX (El municipi en xifres)     · API pròpia (no Socrata)
  - Electoral (Processos electorals - Vots)  · Socrata ntc4-rnwr
  - icaen_consum (consum elèctric municipal) · Socrata 8idm-becu
    proxy de presència per a "població real vs padró"; sector USOS
    DOMÈSTICS (vegeu docs/poblacio-real-fonts.md). Cablejat a `all`.
  - restauracio_osm (establiments de restauració)  · OpenStreetMap/Overpass
    2n proxy d'hostaleria (capa L3), complement del vidre. POIs amenity
    (restaurant/cafe/bar/…) assignats per punt-en-polígon a la geometria
    real dels 31 munis. OSM infra-mapeja el rural → compte = MÍNIM, no cens.
    Llicència ODbL. Cablejat a `all`.
  - serveis_osm (comerç i serveis essencials)       · OpenStreetMap/Overpass
    Senyal de CENTRALITAT funcional (centre de serveis real) per a la
    tipologia capital_serveis. POIs shop (supermarket/convenience/bakery/…)
    + amenity (bank/pharmacy/post_office/townhall/…) assignats per
    punt-en-polígon. El senyal és el COMPTE ABSOLUT (no la densitat). OSM
    infra-mapeja el rural → MÍNIM, no cens. Llicència ODbL. Cablejat a `all`.
  - demografia_origen (composició i arrelament)    · Idescat (EMEX + Pob. estrangera)
    TRANSFORMACIÓ DEMOGRÀFICA (origen), MAI «extranjería». Població per
    NACIONALITAT i per LLOC DE NAIXEMENT (foto darrer any, EMEX) + SÈRIE
    municipal 2021→ de població estrangera (deltes). Lectura ECOLÒGICA;
    secret estadístic dels micromunicipis respectat (NULL). Cablejat a `all`.
  - atur_sepe (atur registrat mensual, D1)          · SEPE, CSV anual (des de 2006)
    Primera família MENSUAL. Filtre pel CATÀLEG de Catalunya sencer (947
    ine5), MAI per província (Gósol=25100 Lleida, Gombrèn=17080 Girona).
    Doctrina del «<5» (C1 §1.1): interval [1,4], mai zero ni NaN silenciós.
    Zero-pad de codis INE obligatori. Cablejat a `all`.

Cada connector deixa les dades crues a ``data/raw/<source>/`` i un sidecar
``_provenance.json`` (source, url, dataset_id, fetched_at, llicència, files).
"""

__version__ = "0.1.0"
