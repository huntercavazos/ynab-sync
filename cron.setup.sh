# cron.setup.sh
apt-get update && apt-get install -y cron logrotate

mkdir -p /var/log/ynab-sync

cat <<EOF > /etc/cron.d/ynab-sync
0 * * * * SOURCE_API_KEY=$SOURCE_API_KEY TARGET_API_KEY=$TARGET_API_KEY SOURCE_BUDGET_ID=$SOURCE_BUDGET_ID TARGET_BUDGET_ID=$TARGET_BUDGET_ID SHARED_CATEGORY_ID=$SHARED_CATEGORY_ID SHARED_ACCOUNT_ID=$SHARED_ACCOUNT_ID /usr/local/bin/python3 /app/main.py >> /var/log/ynab-sync/sync.log 2>&1
EOF

chmod 0644 /etc/cron.d/ynab-sync
crontab /etc/cron.d/ynab-sync

cat <<EOF > /etc/logrotate.d/ynab-sync
/var/log/ynab-sync/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    create 644 root root
}
EOF
