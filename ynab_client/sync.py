from ynab_client import config, api
from datetime import datetime, timedelta


def sync_transactions():
    users = config.load_user_config()

    user_a = users["user_a"]
    user_b = users["user_b"]

    api_client_a, _, _, transactions_api_a = api.get_api_clients(user_a["token"])
    api_client_b, _, _, transactions_api_b = api.get_api_clients(user_b["token"])

    since_date = (datetime.now() - timedelta(days=3)).date()

    with api_client_a, api_client_b:
        # Fetch transactions from User A
        response_a = transactions_api_a.get_transactions(
            user_a["budget_id"],
            user_a["account_id"],
            since_date=since_date
        )
        all_txns_a = response_a.data.transactions

        # Filter only those in the shared category
        filtered_txns = [
            txn for txn in all_txns_a
            if txn.category_id == user_a["shared_category_id"]
        ]

        # Fetch recent transactions from User B
        response_b = transactions_api_b.get_transactions(
            user_b["budget_id"],
            user_b["account_id"],
            since_date=since_date
        )
        existing_txns_b = response_b.data.transactions

        # Index B's transactions by import_id
        b_txn_map = {
            txn.import_id: txn
            for txn in existing_txns_b
            if txn.import_id
        }

        print(f"Found {len(filtered_txns)} transactions to sync...")

        for txn in filtered_txns:
            import_id = f"SYNCED:{txn.date}:{txn.amount}"

            new_txn_data = {
                "account_id": user_b["account_id"],
                "date": txn.date,
                "memo": txn.memo,
                "cleared": txn.cleared,
                "approved": txn.approved,
                "import_id": import_id
            }

            existing = b_txn_map.get(import_id)

            if existing:
                print(f"🔄 Updating existing transaction: {txn.memo}")
                transactions_api_b.update_transaction(
                    user_b["budget_id"],
                    existing.id,
                    {"transaction": new_txn_data}
                )
            else:
                print(f"➕ Creating new transaction: {txn.memo}")
                transactions_api_b.create_transaction(
                    user_b["budget_id"],
                    {"transaction": new_txn_data}
                )
