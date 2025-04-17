# 🧾 YNAB Sync - Shared Category Syncing

This is a lightweight Python app that syncs transactions between two YNAB budgets for a **shared category**. It's designed for couples or roommates who want to track shared expenses but keep separate YNAB accounts.

## 🔧 Features

- ✅ Automatically syncs transactions in a designated **shared category**
- ✅ Avoids duplicates using a smart `import_id` convention
- ✅ Updates or deletes previously synced transactions as needed
- ✅ Runs hourly via cron inside a Docker container
- ✅ Supports environment-based configuration for use in Docker/Portainer

---

## Usage

### 1. 🐳 Run with Docker

You can pull the image directly:

```bash
docker pull cavazosapps/ynab-sync:latest
```

Or use Docker Compose:

```yaml
services:
  ynab-sync:
    image: cavazosapps/ynab-sync:latest
    restart: unless-stopped
    environment:
      - SOURCE_API_KEY=...
      - TARGET_API_KEY=...
      - SOURCE_BUDGET_ID=...
      - TARGET_BUDGET_ID=...
      - SHARED_CATEGORY_ID=...
      - SHARED_ACCOUNT_ID=...
```
You can also set environment variables via the Portainer UI.

### 2. 🛠️ Environment Variables

| Variable           | Description                              |
|--------------------|------------------------------------------|
| SOURCE_API_KEY     | Personal access token for source account |
| TARGET_API_KEY     | Personal access token for target account |
| SOURCE_BUDGET_ID   | Budget ID from source YNAB account       |
| TARGET_BUDGET_ID   | Budget ID from target YNAB account       |
| SHARED_CATEGORY_ID | Category ID to watch in source account   |
| SHARED_ACCOUNT_ID  | Target account ID to create transactions |

### 3. 🕒 How It Works

- On container startup, it immediately runs the sync once.
- Then, it runs every hour via cron.
- Logs are stored in /var/log/ynab-sync/sync.log.

## 📜 License

MIT License. Do what you want, just don’t blame me if it breaks your budget 😉

## 🤝 Contributing

Pull requests are welcome! Let’s make YNAB syncing smarter together.

## ☕ Support

If you find this project helpful, consider supporting me:

<a href="https://www.buymeacoffee.com/huntercavazos" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>