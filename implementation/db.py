from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

try:
    from .init_db import get_database_path
except ImportError:
    from init_db import get_database_path


class ValidationError(Exception):
    """Raised when a request cannot be safely executed."""


class SQLiteAdapter:
    ALLOWED_OPERATORS = {
        "eq": "=",
        "=": "=",
        "ne": "!=",
        "!=": "!=",
        "gt": ">",
        ">": ">",
        "gte": ">=",
        ">=": ">=",
        "lt": "<",
        "<": "<",
        "lte": "<=",
        "<=": "<=",
        "like": "LIKE",
        "contains": "LIKE",
        "in": "IN",
    }
    ALLOWED_METRICS = {"count", "avg", "sum", "min", "max"}
    MAX_LIMIT = 100

    def __init__(self, db_path: str | Path | None = None):
        self.db_path = Path(db_path).expanduser().resolve() if db_path else get_database_path()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def list_tables(self) -> list[str]:
        sql = """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
        with self.connect() as conn:
            return [row["name"] for row in conn.execute(sql)]

    def get_table_schema(self, table: str) -> dict[str, Any]:
        table = self.validate_table_name(table)
        with self.connect() as conn:
            columns = [
                {
                    "name": row["name"],
                    "type": row["type"],
                    "not_null": bool(row["notnull"]),
                    "default": row["dflt_value"],
                    "primary_key": bool(row["pk"]),
                }
                for row in conn.execute(f"PRAGMA table_info({self.quote_identifier(table)})")
            ]
            foreign_keys = [
                {
                    "from": row["from"],
                    "to_table": row["table"],
                    "to": row["to"],
                    "on_update": row["on_update"],
                    "on_delete": row["on_delete"],
                }
                for row in conn.execute(f"PRAGMA foreign_key_list({self.quote_identifier(table)})")
            ]

        return {"table": table, "columns": columns, "foreign_keys": foreign_keys}

    def get_database_schema(self) -> dict[str, Any]:
        return {"tables": [self.get_table_schema(table) for table in self.list_tables()]}

    def search(
        self,
        table: str,
        columns: list[str] | str | None = None,
        filters: list[dict[str, Any]] | dict[str, Any] | None = None,
        limit: int = 20,
        offset: int = 0,
        order_by: str | None = None,
        descending: bool = False,
    ) -> dict[str, Any]:
        table = self.validate_table_name(table)
        selected_columns = self.normalize_columns(table, columns)
        limit = self.validate_limit(limit)
        offset = self.validate_offset(offset)

        where_sql, params = self.build_where(table, filters)
        select_sql = ", ".join(self.quote_identifier(column) for column in selected_columns)
        sql = f"SELECT {select_sql} FROM {self.quote_identifier(table)}"
        if where_sql:
            sql += f" WHERE {where_sql}"
        if order_by:
            order_by = self.validate_column_name(table, order_by)
            direction = "DESC" if descending else "ASC"
            sql += f" ORDER BY {self.quote_identifier(order_by)} {direction}"
        sql += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self.connect() as conn:
            rows = [dict(row) for row in conn.execute(sql, params)]

        return {
            "table": table,
            "columns": selected_columns,
            "rows": rows,
            "limit": limit,
            "offset": offset,
            "count": len(rows),
        }

    def insert(self, table: str, values: dict[str, Any]) -> dict[str, Any]:
        table = self.validate_table_name(table)
        if not isinstance(values, dict) or not values:
            raise ValidationError("insert values must be a non-empty object")

        normalized_values = {self.validate_column_name(table, column): value for column, value in values.items()}
        columns = list(normalized_values.keys())
        placeholders = ", ".join("?" for _ in columns)
        column_sql = ", ".join(self.quote_identifier(column) for column in columns)
        sql = f"INSERT INTO {self.quote_identifier(table)} ({column_sql}) VALUES ({placeholders})"

        with self.connect() as conn:
            cursor = conn.execute(sql, [normalized_values[column] for column in columns])
            conn.commit()
            inserted_id = cursor.lastrowid

        payload = dict(normalized_values)
        if "id" not in payload:
            payload["id"] = inserted_id

        return {"table": table, "inserted": payload}

    def aggregate(
        self,
        table: str,
        metric: str,
        column: str | None = None,
        filters: list[dict[str, Any]] | dict[str, Any] | None = None,
        group_by: str | list[str] | None = None,
    ) -> dict[str, Any]:
        table = self.validate_table_name(table)
        metric = self.validate_metric(metric)
        group_columns = self.normalize_group_by(table, group_by)

        if metric == "count" and column is None:
            metric_target = "*"
        else:
            if column is None:
                raise ValidationError(f"{metric} requires a column")
            column = self.validate_column_name(table, column)
            metric_target = self.quote_identifier(column)

        select_parts = [self.quote_identifier(column_name) for column_name in group_columns]
        select_parts.append(f"{metric.upper()}({metric_target}) AS value")
        sql = f"SELECT {', '.join(select_parts)} FROM {self.quote_identifier(table)}"

        where_sql, params = self.build_where(table, filters)
        if where_sql:
            sql += f" WHERE {where_sql}"
        if group_columns:
            group_sql = ", ".join(self.quote_identifier(column_name) for column_name in group_columns)
            sql += f" GROUP BY {group_sql}"

        with self.connect() as conn:
            rows = [dict(row) for row in conn.execute(sql, params)]

        return {
            "table": table,
            "metric": metric,
            "column": column,
            "group_by": group_columns,
            "rows": rows,
        }

    def validate_table(self, table: str) -> None:
        self.validate_table_name(table)

    def validate_column(self, table: str, column: str) -> None:
        self.validate_column_name(table, column)

    def normalize_identifier_input(self, value: str, label: str) -> str:
        if not isinstance(value, str):
            raise ValidationError(f"{label} must be a non-empty string")
        normalized = value.strip()
        if not normalized:
            raise ValidationError(f"{label} must be a non-empty string")
        return normalized

    def validate_table_name(self, table: str) -> str:
        normalized_table = self.normalize_identifier_input(table, "table name")
        if normalized_table not in self.list_tables():
            raise ValidationError(f"unknown table: {normalized_table}")
        return normalized_table

    def validate_column_name(self, table: str, column: str) -> str:
        normalized_table = self.validate_table_name(table)
        normalized_column = self.normalize_identifier_input(column, "column name")
        column_names = {item["name"] for item in self.get_table_schema_unchecked(normalized_table)["columns"]}
        if normalized_column not in column_names:
            raise ValidationError(f"unknown column for table {normalized_table}: {normalized_column}")
        return normalized_column

    def validate_metric(self, metric: str) -> str:
        if not isinstance(metric, str):
            raise ValidationError("metric must be a string")
        normalized = metric.strip().lower()
        if normalized not in self.ALLOWED_METRICS:
            allowed = ", ".join(sorted(self.ALLOWED_METRICS))
            raise ValidationError(f"unsupported metric: {metric}. Allowed metrics: {allowed}")
        return normalized

    def normalize_columns(self, table: str, columns: list[str] | str | None) -> list[str]:
        schema_columns = [item["name"] for item in self.get_table_schema_unchecked(table)["columns"]]
        if columns is None:
            return schema_columns
        if isinstance(columns, str):
            columns = [columns]
        if not isinstance(columns, list) or not columns:
            raise ValidationError("columns must be a non-empty list, string, or null")
        normalized_columns = [self.validate_column_name(table, column) for column in columns]
        return normalized_columns

    def normalize_group_by(self, table: str, group_by: str | list[str] | None) -> list[str]:
        if group_by is None:
            return []
        columns = [group_by] if isinstance(group_by, str) else group_by
        if not isinstance(columns, list) or not columns:
            raise ValidationError("group_by must be a string, non-empty list, or null")
        normalized_columns = [self.validate_column_name(table, column) for column in columns]
        return normalized_columns

    def build_where(
        self, table: str, filters: list[dict[str, Any]] | dict[str, Any] | None
    ) -> tuple[str, list[Any]]:
        clauses: list[str] = []
        params: list[Any] = []

        for item in self.normalize_filters(filters):
            column = self.validate_column_name(table, item["column"])
            operator = item["operator"]
            value = item["value"]

            sql_operator = self.ALLOWED_OPERATORS.get(operator)
            if sql_operator is None:
                allowed = ", ".join(sorted(self.ALLOWED_OPERATORS))
                raise ValidationError(f"unsupported filter operator: {operator}. Allowed operators: {allowed}")

            quoted_column = self.quote_identifier(column)
            if operator == "contains":
                clauses.append(f"{quoted_column} LIKE ?")
                params.append(f"%{value}%")
            elif operator == "in":
                if not isinstance(value, list) or not value:
                    raise ValidationError("in operator requires a non-empty list value")
                placeholders = ", ".join("?" for _ in value)
                clauses.append(f"{quoted_column} IN ({placeholders})")
                params.extend(value)
            else:
                clauses.append(f"{quoted_column} {sql_operator} ?")
                params.append(value)

        return " AND ".join(clauses), params

    def normalize_filters(self, filters: list[dict[str, Any]] | dict[str, Any] | None) -> list[dict[str, Any]]:
        if filters is None:
            return []
        if isinstance(filters, dict):
            if {"column", "value"} <= set(filters.keys()):
                return [self.normalize_filter_item(filters)]
            return [
                {"column": column, "operator": "eq", "value": value}
                for column, value in filters.items()
            ]
        if isinstance(filters, list):
            return [self.normalize_filter_item(item) for item in filters]
        raise ValidationError("filters must be an object, list, or null")

    def normalize_filter_item(self, item: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(item, dict):
            raise ValidationError("each filter must be an object")
        if "column" not in item or "value" not in item:
            raise ValidationError("each filter requires column and value")
        operator = item.get("operator", item.get("op", "eq"))
        if not isinstance(operator, str):
            raise ValidationError("filter operator must be a string")
        return {
            "column": self.normalize_identifier_input(item["column"], "column name"),
            "operator": operator.strip().lower(),
            "value": item["value"],
        }

    def validate_limit(self, limit: int) -> int:
        if isinstance(limit, bool):
            raise ValidationError("limit must be a positive integer")
        if not isinstance(limit, int) or limit < 1:
            raise ValidationError("limit must be a positive integer")
        return min(limit, self.MAX_LIMIT)

    def validate_offset(self, offset: int) -> int:
        if isinstance(offset, bool):
            raise ValidationError("offset must be a non-negative integer")
        if not isinstance(offset, int) or offset < 0:
            raise ValidationError("offset must be a non-negative integer")
        return offset

    def get_table_schema_unchecked(self, table: str) -> dict[str, Any]:
        table = self.normalize_identifier_input(table, "table name")
        with self.connect() as conn:
            rows = list(conn.execute(f"PRAGMA table_info({self.quote_identifier(table)})"))
        if not rows:
            raise ValidationError(f"unknown table: {table}")
        return {
            "table": table,
            "columns": [
                {
                    "name": row["name"],
                    "type": row["type"],
                    "not_null": bool(row["notnull"]),
                    "default": row["dflt_value"],
                    "primary_key": bool(row["pk"]),
                }
                for row in rows
            ],
        }

    def quote_identifier(self, identifier: str) -> str:
        return '"' + identifier.replace('"', '""') + '"'
