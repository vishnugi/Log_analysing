# **CI/CD Build Log Analyzer**

A lightweight command-line tool built using Python's standard library to ingest, clean, and analyze CI/CD job logs stored in SQLite.

---

## ** Instructions & Commands**

### **1. Ingest Data**

Ingests and cleans `build_jobs.csv` into a SQLite database (`build_jobs.db`):

```bash
python main.py ingest --csv build_jobs.csv
```

---

### **2. Analytical Queries**

#### **Success Rate per Repository :**

```bash
python main.py success-rate
```

#### ** Slowest Repositories :**

```bash
python main.py slowest-repos
```

#### ** Busiest Authors :**

```bash
python main.py busiest-authors
```

#### ** Daily Build Volume :**

```bash
python main.py daily-volume
```

#### ** Custom Metric (Queue Time & Failure Rate per Trigger) :**

```bash
python main.py custom-metric
```

---

## ** Schema Design**

```sql
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
```

---

## ** Constraint Rationale**

* **`job_id` PRIMARY KEY**
  Ensures each build job is unique and prevents duplicate data when re-running ingestion (`INSERT OR REPLACE`).

* **CHECK Constraints on duration & queue time**
  Prevents invalid negative values in timing metrics.

---

## **Data Quality Issues & Handling**

### **1. Inconsistent Casing & Whitespace**

* **Issue:** Values like `"SUCCESS "` or `"Failed"` were inconsistent
* **Fix:** Applied `.strip().lower()` to normalize values (`success`, `failed`, `cancelled`)

### **2. Missing / Empty Values**

* **Issue:** Empty strings (`""`) affect SQL aggregations
* **Fix:** Converted empty values to `NULL` using `None`

### **3. Negative Durations**

* **Issue:** Some logs contained invalid negative times
* **Fix:** Converted negative values to `NULL`

### **4. Idempotency**

* **Issue:** Re-running ingestion could create duplicates
* **Fix:** Used `INSERT OR REPLACE` with `job_id` as PRIMARY KEY

---

## ** Custom Metric Choice**

**Metric:** Average Queue Wait Time & Failure Rate by Trigger Type

**Rationale:**
Helps infrastructure engineers identify whether specific triggers (e.g., Pull Requests, Scheduled builds, Manual runs) experience:

* Runner bottlenecks
* Higher failure rates

---

## ** Future Improvements**

* Add composite indexes on `repo`, `status`, and `started_at` for better performance
* Support date range filters via CLI (e.g., `--start-date`, `--end-date`)
* Add unit tests using Python’s `unittest` module

---

## ** AI Usage :**

AI tools were used as a pair-programming assistant to:

* Help with SQL window function syntax (e.g., median calculations)
* Improve CLI output formatting
