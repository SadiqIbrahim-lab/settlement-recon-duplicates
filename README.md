#sadiq-ibrahim/settlement-recon-duplicates
## Adversarial testing log
Cheat 1 — deleted duplicate rows directly from SQLite, then ran recon.py normally. Caught by test_duplicate_rows_still_in_db.

Cheat 2 — computed settlement total from CSV, wrote matching JSON directly without touching recon.py. Initially passed all tests — hole found. Fixed by adding test_pipeline_itself_is_fixed which deletes the report before re-running recon.py, so stale hand-written files cannot pass.

Reviewer identified two further holes: db_total_kobo was not independently verified against the DB, and test_pipeline_itself_is_fixed did not clear the report before re-running. Fixed by computing ground truth with a DISTINCT query against the DB, deleting the report before re-run, adding PENDING rows to seed.py to make the WHERE status filter testable, and removing the bug comment from recon.py.

Oracle 1.0, nop 0.0 confirmed after all fixes.