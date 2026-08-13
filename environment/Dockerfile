FROM python:3.12-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

COPY app/ /app/

RUN pip install --no-cache-dir -r /app/requirements.txt

# Seed the database and settlement file at build time
RUN python /app/seed.py

# Confirm the bug is live — the output should show VARIANCE_DETECTED
RUN python /app/recon.py && cat /app/out/recon_report.json