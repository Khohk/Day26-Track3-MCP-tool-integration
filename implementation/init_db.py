from __future__ import annotations

import os
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "sqlite_lab.db"


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS enrollments;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS students;

CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    cohort TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    credits INTEGER NOT NULL CHECK (credits > 0)
);

CREATE TABLE enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    score REAL NOT NULL CHECK (score >= 0 AND score <= 100),
    status TEXT NOT NULL CHECK (status IN ('active', 'completed', 'dropped')),
    enrolled_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (course_id) REFERENCES courses(id)
);
"""


SEED_SQL = """
INSERT INTO students (name, email, cohort) VALUES
    ('An Nguyen', 'an.nguyen@example.edu', 'A1'),
    ('Binh Tran', 'binh.tran@example.edu', 'A1'),
    ('Chi Le', 'chi.le@example.edu', 'B2'),
    ('Duc Pham', 'duc.pham@example.edu', 'B2'),
    ('Ema Vo', 'ema.vo@example.edu', 'C3');

INSERT INTO courses (code, title, credits) VALUES
    ('PY101', 'Python Foundations', 3),
    ('DB201', 'Database Systems', 4),
    ('AI301', 'Applied AI', 3);

INSERT INTO enrollments (student_id, course_id, score, status) VALUES
    (1, 1, 88.5, 'completed'),
    (1, 2, 91.0, 'active'),
    (2, 1, 77.0, 'completed'),
    (2, 3, 84.0, 'active'),
    (3, 2, 92.5, 'completed'),
    (4, 1, 69.0, 'completed'),
    (4, 3, 73.5, 'active'),
    (5, 3, 95.0, 'completed');
"""


def get_database_path() -> Path:
    configured = os.getenv("SQLITE_LAB_DB_PATH")
    return Path(configured).expanduser().resolve() if configured else DEFAULT_DB_PATH


def create_database(db_path: str | Path | None = None) -> Path:
    path = Path(db_path).expanduser().resolve() if db_path else get_database_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA_SQL)
        conn.executescript(SEED_SQL)
        conn.commit()

    return path


if __name__ == "__main__":
    created_path = create_database()
    print(f"SQLite lab database created at: {created_path}")
