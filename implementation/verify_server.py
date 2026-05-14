from __future__ import annotations

import json

from db import SQLiteAdapter, ValidationError
from init_db import create_database
from mcp_server import aggregate, database_schema, insert, search, table_schema


def print_json(title: str, payload) -> None:
    print(f"\n## {title}")
    print(json.dumps(payload, indent=2) if not isinstance(payload, str) else payload)


def main() -> None:
    db_path = create_database()
    adapter = SQLiteAdapter(db_path)

    print(f"Database reset at: {db_path}")
    print_json("Tables", adapter.list_tables())

    print_json(
        "search students in cohort A1",
        search(table="students", filters={"cohort": "A1"}, order_by="name"),
    )

    print_json(
        "insert a new student",
        insert(
            table="students",
            values={
                "name": "Linh Ho",
                "email": "linh.ho@example.edu",
                "cohort": "A1",
            },
        ),
    )

    print_json(
        "average enrollment score",
        aggregate(table="enrollments", metric="avg", column="score"),
    )

    print_json(
        "count students by cohort",
        aggregate(table="students", metric="count", group_by="cohort"),
    )

    print_json("schema://database", database_schema())
    print_json("schema://table/students", table_schema("students"))

    print("\n## invalid request example")
    try:
        search(table="missing_table")
    except (ValueError, ValidationError) as error:
        print(f"Clear error returned: {error}")


if __name__ == "__main__":
    main()
