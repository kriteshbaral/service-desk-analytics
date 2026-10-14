"""
Load tickets.csv into SQLite, run every query in sql/analysis.sql,
and save the results:

  analysis/output/<query_name>.csv  - one file per query (open in Excel / Power BI)
  analysis/output/metrics.json      - all results together (used by the dashboard)
  dashboard/data.js                 - the same JSON, wrapped so index.html can load it offline

Uses only the Python standard library.
"""

import csv
import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "tickets.csv"
SCHEMA = ROOT / "sql" / "schema.sql"
QUERIES = ROOT / "sql" / "analysis.sql"
OUT_DIR = ROOT / "analysis" / "output"
DASHBOARD_DATA = ROOT / "dashboard" / "data.js"


def load_tickets(conn):
    conn.executescript(SCHEMA.read_text())
    with CSV_PATH.open() as f:
        rows = list(csv.DictReader(f))
    cols = list(rows[0])
    for r in rows:  # empty strings -> NULL
        for c in ("resolved_at", "csat_score"):
            if r[c] == "":
                r[c] = None
    conn.executemany(
        f"INSERT INTO tickets ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
        [tuple(r[c] for c in cols) for r in rows],
    )
    conn.commit()
    return len(rows)


def parse_queries(text):
    """Split analysis.sql into {name: sql} using the '-- name:' markers."""
    parts = re.split(r"^-- name:\s*(\w+)\s*$", text, flags=re.M)
    return {parts[i]: parts[i + 1].strip() for i in range(1, len(parts), 2)}


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    n = load_tickets(conn)
    print(f"Loaded {n:,} tickets")

    results = {}
    for name, sql in parse_queries(QUERIES.read_text()).items():
        rows = [dict(r) for r in conn.execute(sql).fetchall()]
        results[name] = rows
        with (OUT_DIR / f"{name}.csv").open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        print(f"  {name:<26} {len(rows):>3} rows")

    results["_meta"] = {
        "organisation": "Harbourline Regional Services (fictional)",
        "period": "October 2025 - September 2026",
        "generated_from": "data/tickets.csv",
    }
    (OUT_DIR / "metrics.json").write_text(json.dumps(results, indent=2))
    DASHBOARD_DATA.write_text("window.METRICS = " + json.dumps(results) + ";\n")
    print(f"Saved results to {OUT_DIR} and {DASHBOARD_DATA}")


if __name__ == "__main__":
    main()
