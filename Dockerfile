# Base setup
FROM python:3.11-slim
WORKDIR /app

# Install system packages needed for cron and logrotate
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    cron \
    logrotate \
    && rm -rf /var/lib/apt/lists/*

# Copy app and config
COPY requirements.txt .env main.py ./
COPY ynab_client/ ynab_client/
COPY cron.setup.sh .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Make sure shell script is executable with correct line endings
RUN chmod +x cron.setup.sh && ./cron.setup.sh

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
