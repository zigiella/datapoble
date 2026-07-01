"""datapoble-geo-rag — DuckDB geospatial substrate for the 31 Berguedà municipalities.

Phase 0a: build a queryable, spatially-aware substrate from committed data sources.
Isolated experiment — does not depend on or touch packages/ai.
"""

from datapoble_geo_rag.build import build, name_search, neighbors
from datapoble_geo_rag.descriptions import generate_descriptions
from datapoble_geo_rag.search import load_embeddings, semantic_search

# NOTE: embeddings.py is intentionally NOT imported here — it is the only torch module,
# and importing the package must stay torch-free (CI installs no torch).

__all__ = [
    "build",
    "name_search",
    "neighbors",
    "generate_descriptions",
    "load_embeddings",
    "semantic_search",
]
