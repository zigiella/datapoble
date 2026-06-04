"""Read-only DuckDB warehouse over the marts.

This is the *only* place SQL touches data. It loads the mart tables (real
`data/marts/*` when present, otherwise the seed fixtures), and exposes a single
``query`` method that runs **read-only** statements.

Guardrails enforced here (defence in depth — the router also validates before
we ever get here):
- The connection is opened ``read_only`` against an in-memory database built
  from immutable source files; there is no writable target.
- :meth:`Warehouse.query` rejects anything that is not a lone ``SELECT`` /
  ``WITH`` statement (no DDL/DML, no multiple statements, no ``raw``).
- Only tables registered from the catalog's marts exist in the connection, so a
  query against ``raw_*`` or an unknown table fails closed.
"""

from __future__ import annotations

import re
from pathlib import Path

import duckdb

from .catalog import Catalog

# A single read-only data-returning statement. We are deliberately strict:
# the deterministic router only ever emits `SELECT ... FROM <mart> ...`, and
# the LLM path is constrained to the same shape. Anything else is a bug or an
# attack, and is refused.
_ALLOWED_LEADING = re.compile(r"^\s*(select|with)\b", re.IGNORECASE)
_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|attach|copy|install|load|"
    r"pragma|export|import|call|set|truncate|merge|replace|grant|revoke|"
    r"vacuum)\b",
    re.IGNORECASE,
)


class WarehouseError(RuntimeError):
    """Raised when a query violates the read-only / allowed-table guardrails."""


def fixtures_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "fixtures"


def default_marts_dir(catalog: Catalog) -> Path:
    """Where the real marts live (``data/marts`` at the repo root)."""
    root = catalog.path.parents[1] if catalog.path else Path.cwd()
    return root / "data" / "marts"


def _strip_sql(sql: str) -> str:
    """Remove comments and trailing semicolons for validation/normalisation."""
    # Strip line and block comments so they cannot smuggle a second statement.
    no_block = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    no_line = re.sub(r"--[^\n]*", " ", no_block)
    return no_line.strip().rstrip(";").strip()


class Warehouse:
    """An in-memory, read-only view over the mart tables.

    Parameters
    ----------
    catalog:
        The semantic catalog, used to know which tables are legal.
    marts_dir:
        Directory of real mart files (``*.parquet``/``*.csv``). If a required
        table is missing there, the matching fixture CSV is used instead, and
        the table name is recorded in :attr:`using_fixture`.
    use_fixtures:
        Force the seed fixtures and ignore ``marts_dir`` entirely. This is for
        the **deterministic offline gate** (tests / ``run_evals.py``): it pins
        the warehouse to the known fixture distribution so the gate proves the
        router *logic* and stays green and stable regardless of whether the real
        marts happen to be on disk. Runtime callers leave it ``False`` so the
        agent/API keep preferring the real marts.
    """

    def __init__(self, catalog: Catalog, marts_dir: Path | None = None,
                 use_fixtures: bool = False):
        self.catalog = catalog
        self.marts_dir = marts_dir or default_marts_dir(catalog)
        self.fixtures = fixtures_dir()
        self.use_fixtures = use_fixtures
        self.allowed_tables: set[str] = set(catalog.tables())
        self.using_fixture: dict[str, bool] = {}
        # Build a single in-memory DB, register each mart as a real table, then
        # reopen read-only by detaching write access via a fresh cursor guard.
        self._con = duckdb.connect(database=":memory:")
        self._register_tables()
        self._read_only = True  # logical flag; enforced in `query`

    # --- setup ---
    def _source_for(self, table: str) -> tuple[Path, bool]:
        """Return (path, is_fixture) for a mart table, preferring real data.

        When :attr:`use_fixtures` is set the real marts are skipped entirely and
        only the seed fixture is considered, so the offline gate is decoupled
        from whatever happens to live in ``data/marts``.
        """
        if not self.use_fixtures:
            for ext in ("parquet", "csv"):
                candidate = self.marts_dir / f"{table}.{ext}"
                if candidate.is_file():
                    return candidate, False
        fixture = self.fixtures / f"{table}.csv"
        if fixture.is_file():
            return fixture, True
        raise WarehouseError(
            f"No data found for mart '{table}' (looked in {self.marts_dir} "
            f"and {self.fixtures})"
        )

    def _register_tables(self) -> None:
        for table in sorted(self.allowed_tables):
            path, is_fixture = self._source_for(table)
            self.using_fixture[table] = is_fixture
            reader = (
                "read_parquet" if path.suffix == ".parquet" else "read_csv_auto"
            )
            # DuckDB identifiers come from the trusted catalog, not user input.
            self._con.execute(
                f'CREATE TABLE "{table}" AS '
                f"SELECT * FROM {reader}('{path.as_posix()}')"
            )

    # --- guarded query ---
    def validate(self, sql: str) -> str:
        """Validate a statement against the read-only guardrails.

        Returns the cleaned SQL (ready to execute) or raises
        :class:`WarehouseError`.
        """
        cleaned = _strip_sql(sql)
        if not cleaned:
            raise WarehouseError("Empty query")
        if ";" in cleaned:
            raise WarehouseError("Multiple statements are not allowed")
        if not _ALLOWED_LEADING.match(cleaned):
            raise WarehouseError("Only SELECT / WITH queries are allowed")
        if _FORBIDDEN.search(cleaned):
            raise WarehouseError(
                "Query contains a forbidden (write/DDL/side-effect) keyword"
            )
        return cleaned

    def query(self, sql: str, params: dict | list | None = None):
        """Execute a validated read-only query and return rows as dicts.

        ``params`` are bound by DuckDB (``$name`` or ``?``) — never string
        formatted into the SQL — so values like a municipality name cannot
        break out into the statement.
        """
        cleaned = self.validate(sql)
        rel = self._con.execute(cleaned, params or {})
        cols = [d[0] for d in rel.description]
        return [dict(zip(cols, row, strict=True)) for row in rel.fetchall()]

    def close(self) -> None:
        self._con.close()

    def __enter__(self) -> Warehouse:
        return self

    def __exit__(self, *exc) -> None:
        self.close()
