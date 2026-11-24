"""CSV parsing, data cleaning, and SQLite ingestion logic."""

import csv
import sqlite3
import sys
from pathlib import Path

CREATE_SCHEMA = """
CREATE TABLE IF NOT EXISTS build_jobs (
    job_id TEXT PRIMARY KEY,
    repo TEXT NOT NULL,
    branch TEXT,
    trigger TEXT NOT NULL,
    status TEXT NOT NULL,
    author TEXT,
    runner TEXT,
    started_at TEXT NOT NULL,
    duration_seconds REAL CHECK (duration_seconds IS NULL OR duration_seconds >= 0),
    queue_seconds REAL CHECK (queue_seconds IS NULL OR queue_seconds >= 0)
);
"""

INSERT_JOB = """
INSERT OR REPLACE INTO build_jobs (
    job_id, repo, branch, trigger, status, author, runner,
    started_at, duration_seconds, queue_seconds
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
"""


def init_db(conn: sqlite3.Connection):
    """Creates the build_jobs table with explicit data constraints."""
    with conn:
        conn.execute(CREATE_SCHEMA)


def clean_row(row: dict):
    """Cleans and normalizes a single raw CSV row dict."""
    job_id = row.get("job_id", "").strip()
    if not job_id:
        return None  # Skip rows without a primary identifier

    repo = row.get("repo", "").strip()
    branch = row.get("branch", "").strip() or None
    trigger = row.get("trigger", "").strip().lower() or "unknown"
    status = row.get("status", "").strip().lower() or "unknown"
    author = row.get("author", "").strip() or None
    runner = row.get("runner", "").strip() or None

    # Standardize ISO timestamps
    raw_started = row.get("started_at", "").strip()
    started_at = raw_started.replace(" ", "T") if raw_started else None

    # Parse duration_seconds safely
    raw_duration = row.get("duration_seconds", "").strip()
    try:
        duration_seconds = float(raw_duration) if raw_duration else None
        if duration_seconds is not None and duration_seconds < 0:
            duration_seconds = None  # Flag negative duration as NULL
    except ValueError:
        duration_seconds = None

    # Parse queue_seconds safely
    raw_queue = row.get("queue_seconds", "").strip()
    try:
        queue_seconds = float(raw_queue) if raw_queue else None
        if queue_seconds is not None and queue_seconds < 0:
            queue_seconds = None  # Flag negative queue times as NULL
    except ValueError:
        queue_seconds = None

    return (
        job_id,
        repo,
        branch,
        trigger,
        status,
        author,
        runner,
        started_at,
        duration_seconds,
        queue_seconds,
    )


def run_ingestion(csv_path: str, db_path: str):
    """Reads CSV, cleans data, and inserts into SQLite idempotently."""
    csv_file = Path(csv_path)
    if not csv_file.exists():
        print(f"Error: CSV file '{csv_path}' not found.")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    init_db(conn)

    rows_to_insert = []
    skipped_count = 0

    with open(csv_file, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cleaned = clean_row(row)
            if cleaned:
                rows_to_insert.append(cleaned)
            else:
                skipped_count += 1

    with conn:
        conn.executemany(INSERT_JOB, rows_to_insert)

    print(
        f"Ingestion complete: Processed {len(rows_to_insert)} records successfully "
        f"(Skipped: {skipped_count}). Database stored in '{db_path}'."
    )