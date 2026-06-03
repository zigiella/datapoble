"""Client mínim per a l'API SODA/Socrata (Dades Obertes de Catalunya).

Mateix patró que ``packages/ingestion/socrata.py`` (Sondeig): no cal
autenticació, paginem amb ``$limit``/``$offset`` i fixem un ``$order`` per
garantir paginació determinista.
"""
from __future__ import annotations

from typing import Iterator

import requests

DEFAULT_PAGE = 50_000
TIMEOUT = 120


def fetch_all(
    url: str,
    *,
    where: str | None = None,
    select: str | None = None,
    order: str | None = None,
    page_size: int = DEFAULT_PAGE,
    session: requests.Session | None = None,
) -> Iterator[dict]:
    """Itera totes les files d'un recurs Socrata amb paginació estable.

    Socrata requereix un ``$order`` per a offsets consistents; per defecte
    ``:id`` (l'identificador intern de fila).
    """
    sess = session or requests.Session()
    offset = 0
    order = order or ":id"
    while True:
        params = {"$limit": page_size, "$offset": offset, "$order": order}
        if where:
            params["$where"] = where
        if select:
            params["$select"] = select
        resp = sess.get(url, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        yield from batch
        if len(batch) < page_size:
            break
        offset += page_size
