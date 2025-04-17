# cron.setup.sh
apt-get update && apt-get install -y cron logrotate

mkdir -p /var/log/ynab-sync

cat <<EOF > /etc/cron.d/ynab-sync
0 * * * * /usr/local/bin/python /app/main.py >> /var/log/ynab-sync/sync.log 2>&1
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
