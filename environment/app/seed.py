# generates the DB and settlement CSV at build time

import csv
import random
import sqlite3
from pathlib import Path

random.seed(42)  # deterministic — same data every build

Path("/app/data").mkdir(parents=True, exist_ok=True)
Path("/app/out").mkdir(parents=True, exist_ok=True)

# 5,000 unique transactions — this is the ground truth
transactions = [
    (f"TXN-{i+1:06d}", random.randint(100_000, 50_000_000))
    for i in range(5_000)
]

# Settlement CSV — the payment processor's export (correct, no duplicates)
with open("/app/data/settlement.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["transaction_id", "amount_kobo", "status"])
    for txn_id, amount in transactions:
        writer.writerow([txn_id, amount, "SETTLED"])

# Transaction DB — 500 rows double-loaded from the migration
conn = sqlite3.connect("/app/data/transactions.db")
conn.execute("""
    CREATE TABLE transactions (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id TEXT    NOT NULL,
        amount_kobo    INTEGER NOT NULL,
        status         TEXT    NOT NULL DEFAULT 'SETTLED',
        created_at     TEXT    NOT NULL DEFAULT (datetime('now'))
    )
""")

for txn_id, amount in transactions:
    conn.execute(
        "INSERT INTO transactions (transaction_id, amount_kobo) VALUES (?, ?)",
        (txn_id, amount),
    )

# Simulate the double-load: 500 random transactions inserted a second time
for txn_id, amount in random.sample(transactions, 500):
    conn.execute(
        "INSERT INTO transactions (transaction_id, amount_kobo) VALUES (?, ?)",
        (txn_id, amount),
    )
# Add 200 PENDING transactions not in the settlement file
# These must be excluded from the recon sum — makes the WHERE status filter testable
pending_transactions = [
    (f"TXN-PENDING-{i+1:04d}", random.randint(100_000, 50_000_000))
    for i in range(200)
]
for txn_id, amount in pending_transactions:
    conn.execute(
        "INSERT INTO transactions (transaction_id, amount_kobo, status) VALUES (?, ?, 'PENDING')",
        (txn_id, amount),
    )
conn.commit()

total = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
unique = conn.execute("SELECT COUNT(DISTINCT transaction_id) FROM transactions").fetchone()[0]
print(f"Seeded: {total} rows, {unique} unique transaction_ids ({total - unique} duplicates)")
conn.close()

#completed