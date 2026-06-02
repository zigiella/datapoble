"""Client mínim per a l'API SODA/Socrata (Dades Obertes de Catalunya).

No cal autenticació per a aquests datasets. Paginem amb ``$limit``/``$offset``.
Aquest mòdul és el *fallback* explícit a ``requests``; els connectors RTC i
residus el fan servir via ``dlt`` per a la càrrega, però la lògica de fetch viu
aquí perquè sigui testejable i reutilitzable sense dlt.
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

    Es fixa un ``$order`` per garantir paginació determinista (Socrata el
    requereix per a offsets consistents); per defecte ``:id``.
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
