import json
from typing import Any

import asyncpg

from app.config import settings

_pool: asyncpg.Pool | None = None


async def _init_connection(conn: asyncpg.Connection) -> None:
    """Auto-encode/decode jsonb & json columns and parameters as native Python
    dict/list, so module code never has to json.dumps/loads by hand."""
    await conn.set_type_codec("jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog", format="text")
    await conn.set_type_codec("json", encoder=json.dumps, decoder=json.loads, schema="pg_catalog", format="text")


async def init_pool() -> None:
    global _pool
    _pool = await asyncpg.create_pool(dsn=settings.database_url, min_size=1, max_size=10, init=_init_connection)


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("DB pool not initialized — call init_pool() at startup")
    return _pool


async def call_fn(fn_name: str, args: list[Any]) -> list[asyncpg.Record]:
    """Calls a DB function (stored procedure) that RETURNS TABLE(...) or a ROWTYPE —
    exactly one call per endpoint, per the modules/db-functions split."""
    placeholders = ", ".join(f"${i + 1}" for i in range(len(args)))
    sql = f"SELECT * FROM {fn_name}({placeholders})"
    async with get_pool().acquire() as conn:
        return await conn.fetch(sql, *args)


async def call_fn_one(fn_name: str, args: list[Any]) -> asyncpg.Record | None:
    rows = await call_fn(fn_name, args)
    return rows[0] if rows else None


async def call_fn_jsonb(fn_name: str, args: list[Any]) -> Any:
    """For functions declared RETURNS jsonb (a single scalar value) — SELECT * FROM
    would otherwise collapse it into one column named after the function itself."""
    placeholders = ", ".join(f"${i + 1}" for i in range(len(args)))
    sql = f"SELECT {fn_name}({placeholders}) AS result"
    async with get_pool().acquire() as conn:
        row = await conn.fetchrow(sql, *args)
    return row["result"] if row else None


def record_to_dict(record: asyncpg.Record | None) -> dict | None:
    if record is None:
        return None
    return dict(record)
