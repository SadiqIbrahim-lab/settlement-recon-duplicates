#sadiq-ibrahim/settlement-recon-duplicates
## Adversarial testing log

**Cheat 1 — delete duplicate rows (Cheat 3 in session):**
Deleted duplicates directly from SQLite, ran recon.py normally.
Result: 4/5 passed, test_duplicate_rows_still_in_db caught it. ✓

**Cheat 2 — hardcode output JSON from settlement CSV:**
Computed settlement total from CSV, wrote matching JSON directly
without touching recon.py or the DB.
Result: initially 5/5 passed — hole found.

**Fix applied:**
Added test_pipeline_itself_is_fixed — re-runs recon.py after
any output is written, overwriting hardcoded files with the
real broken output.
Result: cheat now fails, oracle still 1.0. ✓