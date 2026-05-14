from __future__ import annotations

import pytest

from implementation.db import SQLiteAdapter, ValidationError
from implementation.init_db import create_database


@pytest.fixture()
def adapter(tmp_path):
    db_path = tmp_path / "lab.db"
    create_database(db_path)
    return SQLiteAdapter(db_path)


def test_search_supports_filters_ordering_and_pagination(adapter):
    result = adapter.search(
        table="students",
        filters={"cohort": "A1"},
        columns=["name", "cohort"],
        order_by="name",
        limit=1,
    )

    assert result["count"] == 1
    assert result["rows"][0] == {"name": "An Nguyen", "cohort": "A1"}


def test_insert_returns_inserted_payload(adapter):
    result = adapter.insert(
        "students",
        {"name": "Minh Do", "email": "minh.do@example.edu", "cohort": "C3"},
    )

    assert result["inserted"]["id"] > 0
    assert result["inserted"]["email"] == "minh.do@example.edu"


def test_aggregate_supports_average_and_grouping(adapter):
    avg_result = adapter.aggregate("enrollments", "avg", column="score")
    grouped_result = adapter.aggregate("students", "count", group_by="cohort")

    assert round(avg_result["rows"][0]["value"], 2) == 83.81
    assert {"cohort": "A1", "value": 2} in grouped_result["rows"]


def test_invalid_table_column_operator_and_empty_insert_are_rejected(adapter):
    with pytest.raises(ValidationError, match="unknown table"):
        adapter.search("missing")

    with pytest.raises(ValidationError, match="unknown column"):
        adapter.search("students", columns=["password"])

    with pytest.raises(ValidationError, match="unsupported filter operator"):
        adapter.search("students", filters=[{"column": "cohort", "operator": "regex", "value": "A.*"}])

    with pytest.raises(ValidationError, match="non-empty object"):
        adapter.insert("students", {})


def test_search_accepts_trimmed_identifier_input(adapter):
    result = adapter.search(
        table=" students \n",
        filters={"cohort": "A1"},
        order_by=" name ",
        limit=5,
    )

    assert result["table"] == "students"
    assert result["rows"][0]["name"] == "An Nguyen"
