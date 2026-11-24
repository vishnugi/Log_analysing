"""SQL Query definitions and report formatting functions."""

import sqlite3

# ==========================================
# SQL QUERY DEFINITIONS
# ==========================================

SQL_SUCCESS_RATE = """
SELECT 
    repo,
    COUNT(*) AS total_jobs,
    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS successful_jobs,
    ROUND(
        (SUM(CASE WHEN status = 'success' THEN 1.0 ELSE 0.0 END) / COUNT(*)) * 100, 
        2
    ) AS success_rate_pct
FROM build_jobs
GROUP BY repo
ORDER BY success_rate_pct ASC;
"""

SQL_SLOWEST_REPOS = """
WITH ordered_jobs AS (
    SELECT 
        repo,
        duration_seconds,
        ROW_NUMBER() OVER (PARTITION BY repo ORDER BY duration_seconds ASC) AS row_num,
        COUNT(*) OVER (PARTITION BY repo) AS total_count
    FROM build_jobs
    WHERE duration_seconds IS NOT NULL
)
SELECT 
    repo,
    ROUND(AVG(duration_seconds), 2) AS avg_duration_sec,
    ROUND(AVG(CASE WHEN row_num IN ((total_count + 1) / 2, (total_count + 2) / 2) THEN duration_seconds END), 2) AS median_duration_sec
FROM ordered_jobs
GROUP BY repo
ORDER BY avg_duration_sec DESC;
"""

SQL_BUSIEST_AUTHORS = """
SELECT 
    COALESCE(author, 'Unknown/System') AS author_name,
    COUNT(*) AS total_jobs
FROM build_jobs
GROUP BY author_name
ORDER BY total_jobs DESC
LIMIT 10;
"""

SQL_DAILY_VOLUME = """
SELECT 
    DATE(started_at) AS build_date,
    COUNT(*) AS daily_jobs
FROM build_jobs
WHERE started_at IS NOT NULL
GROUP BY build_date
ORDER BY build_date ASC;
"""

SQL_CUSTOM_METRIC = """
SELECT 
    trigger,
    COUNT(*) AS total_jobs,
    ROUND(AVG(queue_seconds), 2) AS avg_queue_sec,
    ROUND(
        (SUM(CASE WHEN status = 'failed' THEN 1.0 ELSE 0.0 END) / COUNT(*)) * 100, 
        2
    ) AS failure_rate_pct
FROM build_jobs
GROUP BY trigger
ORDER BY avg_queue_sec DESC;
"""


# ==========================================
# REPORT FORMATTERS
# ==========================================

def query_success_rate(conn: sqlite3.Connection):
    """1. Success rate per repository sorted worst to best."""
    cursor = conn.execute(SQL_SUCCESS_RATE)
    rows = cursor.fetchall()

    print(f"\n{'Repository':<25} | {'Total Jobs':<12} | {'Successful':<12} | {'Success Rate (%)':<16}")
    print("-" * 75)
    for row in rows:
        print(f"{row['repo']:<25} | {row['total_jobs']:<12} | {row['successful_jobs']:<12} | {row['success_rate_pct']:<16.2f}")


def query_slowest_repos(conn: sqlite3.Connection):
    """2. Average and Median build duration per repository."""
    cursor = conn.execute(SQL_SLOWEST_REPOS)
    rows = cursor.fetchall()

    print(f"\n{'Repository':<25} | {'Avg Duration (s)':<18} | {'Median Duration (s)':<18}")
    print("-" * 68)
    for row in rows:
        avg_d = row['avg_duration_sec'] if row['avg_duration_sec'] is not None else 0.0
        med_d = row['median_duration_sec'] if row['median_duration_sec'] is not None else 0.0
        print(f"{row['repo']:<25} | {avg_d:<18.2f} | {med_d:<18.2f}")


def query_busiest_authors(conn: sqlite3.Connection):
    """3. Top 10 authors by number of jobs triggered."""
    cursor = conn.execute(SQL_BUSIEST_AUTHORS)
    rows = cursor.fetchall()

    print(f"\n{'Rank':<6} | {'Author':<25} | {'Jobs Triggered':<15}")
    print("-" * 50)
    for idx, row in enumerate(rows, start=1):
        print(f"{idx:<6} | {row['author_name']:<25} | {row['total_jobs']:<15}")


def query_daily_volume(conn: sqlite3.Connection):
    """4. Number of jobs started per calendar day."""
    cursor = conn.execute(SQL_DAILY_VOLUME)
    rows = cursor.fetchall()

    print(f"\n{'Build Date':<15} | {'Total Jobs':<12}")
    print("-" * 30)
    for row in rows:
        print(f"{str(row['build_date']):<15} | {row['daily_jobs']:<12}")


def query_custom_metric(conn: sqlite3.Connection):
    """5. Custom Metric: Average Queue Wait Time & Failure Rate by Trigger Source."""
    cursor = conn.execute(SQL_CUSTOM_METRIC)
    rows = cursor.fetchall()

    print(f"\n{'Trigger Type':<15} | {'Total Jobs':<12} | {'Avg Queue (s)':<15} | {'Failure Rate (%)':<16}")
    print("-" * 65)
    for row in rows:
        avg_q = row['avg_queue_sec'] if row['avg_queue_sec'] is not None else 0.0
        fail_rate = row['failure_rate_pct'] if row['failure_rate_pct'] is not None else 0.0
        print(f"{row['trigger']:<15} | {row['total_jobs']:<12} | {avg_q:<15.2f} | {fail_rate:<16.2f}")