from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

try:
    from .db import SQLiteAdapter, ValidationError
    from .init_db import create_database, get_database_path
except ImportError:
    from db import SQLiteAdapter, ValidationError
    from init_db import create_database, get_database_path


mcp = FastMCP("SQLite Lab MCP Server")


def build_adapter() -> SQLiteAdapter:
    db_path = get_database_path()
    if not Path(db_path).exists():
        create_database(db_path)
    return SQLiteAdapter(db_path)


adapter = build_adapter()


def handle_database_error(error: Exception) -> None:
    if isinstance(error, ValidationError):
        raise ValueError(str(error)) from error
    if isinstance(error, sqlite3.IntegrityError):
        raise ValueError(f"database integrity error: {error}") from error
    raise error


@mcp.tool(name="search")
def search(
    table: str,
    filters: list[dict[str, Any]] | dict[str, Any] | None = None,
    columns: list[str] | str | None = None,
    limit: int = 20,
    offset: int = 0,
    order_by: str | None = None,
    descending: bool = False,
) -> dict[str, Any]:
    """Search rows in a validated table with optional filters, ordering, and pagination."""
    try:
        return adapter.search(
            table=table,
            filters=filters,
            columns=columns,
            limit=limit,
            offset=offset,
            order_by=order_by,
            descending=descending,
        )
    except Exception as error:
        handle_database_error(error)
        raise


@mcp.tool(name="insert")
def insert(table: str, values: dict[str, Any]) -> dict[str, Any]:
    """Insert one row into a validated table and return the inserted payload."""
    try:
        return adapter.insert(table=table, values=values)
    except Exception as error:
        handle_database_error(error)
        raise


@mcp.tool(name="aggregate")
def aggregate(
    table: str,
    metric: str,
    column: str | None = None,
    filters: list[dict[str, Any]] | dict[str, Any] | None = None,
    group_by: str | list[str] | None = None,
) -> dict[str, Any]:
    """Run count, avg, sum, min, or max over a validated table."""
    try:
        return adapter.aggregate(
            table=table,
            metric=metric,
            column=column,
            filters=filters,
            group_by=group_by,
        )
    except Exception as error:
        handle_database_error(error)
        raise


@mcp.resource("schema://database")
def database_schema() -> str:
    """Return the full SQLite schema as JSON text."""
    return json.dumps(adapter.get_database_schema(), indent=2)


@mcp.resource("schema://table/{table_name}")
def table_schema(table_name: str) -> str:
    """Return one table schema as JSON text."""
    try:
        return json.dumps(adapter.get_table_schema(table_name), indent=2)
    except Exception as error:
        handle_database_error(error)
        raise


if __name__ == "__main__":
    mcp.run()
