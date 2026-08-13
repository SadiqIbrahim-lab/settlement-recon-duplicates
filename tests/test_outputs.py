"""Hidden tests for settlement-recon-duplicates."""

import csv
import json
import sqlite3
import subprocess
from pathlib import Path

REPORT_PATH = Path("/app/out/recon_report.json")
DB_PATH     = "/app/data/transactions.db"
SETTLEMENT  = "/app/data/settlement.csv"


def _report() -> dict:
    return json.loads(REPORT_PATH.read_text())


def _settlement_total() -> int:
    """Compute expected total from the settlement CSV."""
    total = 0
    with open(SETTLEMENT, newline="") as f:
        for row in csv.DictReader(f):
            total += int(row["amount_kobo"])
    return total


def _deduplicated_db_total() -> int:
    """Compute expected total from DB using DISTINCT — the ground truth the agent must match."""
    conn = sqlite3.connect(DB_PATH)
    result = conn.execute("""
        SELECT SUM(amount_kobo)
        FROM (
            SELECT DISTINCT transaction_id, amount_kobo
            FROM transactions
            WHERE status = 'SETTLED'
        )
    """).fetchone()[0]
    conn.close()
    return result


def test_report_written():
    """Report file exists at /app/out/recon_report.json."""
    assert REPORT_PATH.exists(), "recon_report.json not found at /app/out/"


def test_variance_is_zero():
    """variance_kobo is zero after deduplication."""
    report = _report()
    assert report["variance_kobo"] == 0, (
        f"Expected 0, got {report['variance_kobo']:,}"
    )


def test_status_matched():
    """status field is MATCHED when variance is zero."""
    assert _report()["status"] == "MATCHED"


def test_db_total_matches_deduplicated_query():
    """db_total_kobo matches a DISTINCT query on the DB — catches hardcoded values and CSV shortcuts."""
    expected = _deduplicated_db_total()
    report = _report()
    assert report["db_total_kobo"] == expected, (
        f"db_total_kobo {report['db_total_kobo']:,} != deduplicated DB total {expected:,}"
    )


def test_settlement_total_correct():
    """settlement_total_kobo matches the actual settlement CSV sum."""
    expected = _settlement_total()
    report = _report()
    assert report["settlement_total_kobo"] == expected, (
        f"settlement_total_kobo {report['settlement_total_kobo']:,} != CSV sum {expected:,}"
    )


def test_pending_rows_excluded():
    """PENDING transactions are excluded from db_total_kobo — confirms WHERE status filter works."""
    conn = sqlite3.connect(DB_PATH)
    pending_total = conn.execute(
        "SELECT SUM(amount_kobo) FROM transactions WHERE status = 'PENDING'"
    ).fetchone()[0]
    conn.close()

    report = _report()
    assert pending_total > 0, "No PENDING rows found in DB — seed data may be wrong"
    assert report["db_total_kobo"] < (report["db_total_kobo"] + pending_total), (
        "PENDING rows appear to be included in db_total_kobo"
    )


def test_duplicate_rows_still_in_db():
    """Duplicate rows still exist — fix must be in the query, not by deleting rows."""
    conn = sqlite3.connect(DB_PATH)
    total  = conn.execute("SELECT COUNT(*) FROM transactions WHERE status = 'SETTLED'").fetchone()[0]
    unique = conn.execute("SELECT COUNT(DISTINCT transaction_id) FROM transactions WHERE status = 'SETTLED'").fetchone()[0]
    conn.close()
    assert total > unique, (
        f"Rows were deleted (total={total}, unique={unique}). "
        "Fix must deduplicate in the query, not remove data."
    )


def test_pipeline_itself_is_fixed():
    """Re-running recon.py on a clean slate must produce a matched report — catches hardcoded outputs."""
    # Delete the report first so a stale hand-written file cannot pass
    REPORT_PATH.unlink(missing_ok=True)

    result = subprocess.run(
        ["python", "/app/recon.py"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"recon.py failed: {result.stderr}"

    report = _report()
    assert report["variance_kobo"] == 0, (
        f"recon.py still produces a variance of {report['variance_kobo']:,} — "
        "the script itself is not fixed"
    )
    assert report["status"] == "MATCHED"

    #rewritten test