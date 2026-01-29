#!/bin/bash
# Scheduled scraper runner
# Runs at 11:59 PM EST daily via cron

set -e

LOG_DIR="/exports/logs"
mkdir -p "$LOG_DIR"

TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
LOG_FILE="$LOG_DIR/scrape_${TIMESTAMP}.log"

echo "=== SCHEDULED SCRAPE START: $(date) ===" | tee -a "$LOG_FILE"
echo "Running incremental scrape..." | tee -a "$LOG_FILE"

cd /app

# Run the scraper in incremental mode
node scraper.js incremental 2>&1 | tee -a "$LOG_FILE"

EXIT_CODE=${PIPESTATUS[0]}

if [ $EXIT_CODE -eq 0 ]; then
    echo "=== SCRAPE COMPLETED SUCCESSFULLY: $(date) ===" | tee -a "$LOG_FILE"
else
    echo "=== SCRAPE FAILED WITH CODE $EXIT_CODE: $(date) ===" | tee -a "$LOG_FILE"
fi

# Cleanup old logs (keep last 30 days)
find "$LOG_DIR" -name "scrape_*.log" -mtime +30 -delete 2>/dev/null || true

exit $EXIT_CODE
