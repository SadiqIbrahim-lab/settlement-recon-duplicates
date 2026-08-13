#!/bin/bash

# Use this file to solve the task.

set -euo pipefail

# Write the fixed recon.py — deduplicates by transaction_id before summing
cat > /app/recon.py << 'EOF'
import csv
import json
import sqlite3
from pathlib import Path

DB_PATH         = "/app/data/transactions.db"
SETTLEMENT_PATH = "/app/data/settlement.csv"
OUTPUT_PATH     = "/app/out/recon_report.json"


def run():
    Path("/app/out").mkdir(exist_ok=True)

    conn = sqlite3.connect(DB_PATH)

    # Deduplicate by transaction_id before summing to exclude migration duplicates
    db_total = conn.execute("""
        SELECT SUM(amount_kobo)
        FROM (
            SELECT DISTINCT transaction_id, amount_kobo
            FROM transactions
            WHERE status = 'SETTLED'
        )
    """).fetchone()[0]

    conn.close()

    settlement_total = 0
    with open(SETTLEMENT_PATH, newline="") as f:
        for row in csv.DictReader(f):
            settlement_total += int(row["amount_kobo"])

    variance = db_total - settlement_total
    report = {
        "db_total_kobo":         db_total,
        "settlement_total_kobo": settlement_total,
        "variance_kobo":         variance,
        "status":                "MATCHED" if variance == 0 else "VARIANCE_DETECTED",
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Status: {report['status']} | Variance: {variance:,} kobo")


if __name__ == "__main__":
    run()
EOF

python /app/recon.py