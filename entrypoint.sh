#!/bin/sh

# Ensure log directory and file exist
mkdir -p /var/log/ynab-sync
touch /var/log/ynab-sync/sync.log

# Run the sync immediately once
echo "Running YNAB sync at container startup..."
/usr/local/bin/python /app/main.py

# Start cron
echo "Starting cron..."
cron

# Tail the log
tail -f /var/log/ynab-sync/sync.log
