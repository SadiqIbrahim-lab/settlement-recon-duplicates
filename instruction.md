The nightly reconciliation has been reporting a higher total than the 
payment processor's settlement file since last week's database migration. 
Finance flagged it on day one and it has not resolved itself.
sss
Run the reconciliation script:

    python /app/recon.py

The script reads from `/app/data/transactions.db` and `/app/data/settlement.csv`,
then writes a report to `/app/out/recon_report.json`.

Fix the pipeline so the report shows:

    {
      "db_total_kobo": <n>,
      "settlement_total_kobo": <n>,
      "variance_kobo": 0,
      "status": "MATCHED"
    }

`db_total_kobo` and `settlement_total_kobo` must be equal and must reflect
the actual transaction data. ++