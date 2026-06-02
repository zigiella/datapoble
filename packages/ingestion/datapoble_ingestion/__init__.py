"""datapoble · ingestion — connectors a fonts obertes amb procedència.

Scope d'aquest PR: Berguedà (31 municipis). Fonts actives:
  - RTC (Registre de Turisme de Catalunya)  · Socrata t2h3-cgys
  - Residus municipals (ARC)                 · Socrata 69zu-w48s
  - Idescat EMEX (El municipi en xifres)     · API pròpia (no Socrata)

Cada connector deixa les dades crues a ``data/raw/<source>/`` i un sidecar
``_provenance.json`` (source, url, dataset_id, fetched_at, llicència, files).
"""

__version__ = "0.1.0"
