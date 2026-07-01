"""datapoble-geo-rag — DuckDB geospatial substrate for the 31 Berguedà municipalities.

Phase 0a: build a queryable, spatially-aware substrate from committed data sources.
Isolated experiment — does not depend on or touch packages/ai.
"""

from datapoble_geo_rag.build import build, name_search, neighbors

__all__ = ["build", "name_search", "neighbors"]
