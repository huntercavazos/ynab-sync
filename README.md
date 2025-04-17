# 🧾 YNAB Sync - Shared Transaction Syncing

Sync shared category transactions from one YNAB budget to another. Perfect for couples or shared financial tracking where each user has their own YNAB account and budget.

## What It Does

- Copies all transactions from a shared category in Budget A
- Pushes them into a designated account in Budget B
- Updates existing transactions or deletes stale ones
- Supports cron-based hourly syncing in a Docker container
- Designed for use with [Portainer](https://www.portainer.io/) and Docker

---

## Getting Started

### Prerequisites

- Two separate YNAB access tokens (one for each budget)
- Budget and category IDs for both sides
- Docker + Portainer (recommended for deployment)

### Environment Variables

Configure the following environment variables (in Portainer, `.env`, or `docker-compose.yml`):

```bash

| Variable             | Description                          |
|----------------------|--------------------------------------|
| `SOURCE_API_KEY`     | YNAB token for source budget         |
| `TARGET_API_KEY`     | YNAB token for target budget         |
| `SOURCE_BUDGET_ID`   | Budget ID to copy from               |
| `TARGET_BUDGET_ID`   | Budget ID to sync into               |
| `SHARED_CATEGORY_ID` | Category ID to track in source       |
| `SHARED_ACCOUNT_ID`  | Account ID to sync into in target    |
```

### 🐳 Docker Deployment

```bash
docker pull cavazosapps/ynab-shared-sync:latest
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

Set environment variables in Portainer or a Compose file, then run the container. It will:

- Run a sync immediately on startup
- Schedule hourly syncs using cron
- Rotate logs with logrotate

---

## Under the Hood

This project uses the official YNAB Python SDK to communicate with the YNAB API.

Features:

- Sync is idempotent: uses import_id to track duplicates
- Transactions updated if already synced
- Stale transactions removed from target budget

---

## Testing

Coming soon: Unit tests using pytest to cover sync logic and mock YNAB API responses.

---

## License

MIT License. Do what you want, just don’t blame me if it breaks your budget 😉

---

## Support

If you find this project helpful, consider supporting me:

<a href="https://www.buymeacoffee.com/huntercavazos" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>