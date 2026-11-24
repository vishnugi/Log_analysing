"""CLI entry point for CI/CD Build Log Analyzer."""

import argparse
import sqlite3
import sys
from pathlib import Path

from ingestion import run_ingestion
import queries

DB_FILE = "build_jobs.db"
CSV_FILE = "build_jobs.csv"


def get_db_connection() -> sqlite3.Connection:
    """Returns a connection to the SQLite database."""
    if not Path(DB_FILE).exists():
        print(f"Error: Database file '{DB_FILE}' not found. Run 'python main.py ingest' first.")
        sys.exit(1)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn


def setup_cli() -> argparse.ArgumentParser:
    """Sets up CLI flags and commands."""
    parser = argparse.ArgumentParser(description="CI/CD Build Log Analyzer CLI Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Ingestion command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest and clean build_jobs.csv into SQLite")
    ingest_parser.add_argument("--csv", default=CSV_FILE, help="Path to raw CSV file")

    # Query commands
    subparsers.add_parser("success-rate", help="Calculate success rate per repository")
    subparsers.add_parser("slowest-repos", help="Calculate average & median job duration per repository")
    subparsers.add_parser("busiest-authors", help="Top 10 authors by total triggered builds")
    subparsers.add_parser("daily-volume", help="Daily build volume across all repositories")
    subparsers.add_parser("custom-metric", help="Queue time and failure rate per trigger type")

    return parser


def main():
    parser = setup_cli()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "ingest":
        run_ingestion(csv_path=args.csv, db_path=DB_FILE)
    else:
        # Route query requests
        conn = get_db_connection()
        try:
            if args.command == "success-rate":
                queries.query_success_rate(conn)
            elif args.command == "slowest-repos":
                queries.query_slowest_repos(conn)
            elif args.command == "busiest-authors":
                queries.query_busiest_authors(conn)
            elif args.command == "daily-volume":
                queries.query_daily_volume(conn)
            elif args.command == "custom-metric":
                queries.query_custom_metric(conn)
        finally:
            conn.close()


if __name__ == "__main__":
    main()