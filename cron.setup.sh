# cron.setup.sh
apt-get update && apt-get install -y cron logrotate

mkdir -p /var/log/ynab-sync

cat <<EOF > /etc/cron.d/ynab-sync
0 * * * * /usr/local/bin/python3 /app/main.py >> /proc/1/fd/1 2>> /proc/1/fd/2
EOF

chmod 0644 /etc/cron.d/ynab-sync
crontab /etc/cron.d/ynab-sync