import os
import sys
import logging
from datetime import date, timedelta
from collections import defaultdict

import ynab
from ynab.api.transactions_api import TransactionsApi
from ynab.models.post_transactions_wrapper import PostTransactionsWrapper
from ynab.models.put_transaction_wrapper import PutTransactionWrapper
from ynab.models.new_transaction import NewTransaction
from ynab.models.existing_transaction import ExistingTransaction
from ynab.rest import ApiException
from dotenv import load_dotenv

# Load .env file if present
load_dotenv(dotenv_path="../.env")

def get_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(f"Missing required environment variable: {key}")
    return value

def create_api(token: str) -> TransactionsApi:
    config = ynab.Configuration(access_token=token)
    return TransactionsApi(ynab.ApiClient(config))

def generate_import_ids(transactions):
    counter = defaultdict(int)
    import_ids = []

    for txn in transactions:
        key = f"{txn.var_date}:{txn.amount}"
        count = counter[key]
        suffix = f":{count}" if count > 0 else ""
        import_id = f"SYNCED:{key}{suffix}"
        import_ids.append(import_id)
        counter[key] += 1

    return import_ids

def sync_transactions():
    log = logging.getLogger("ynab_sync")
    log.info("Starting sync process")

    token_a = get_env("SOURCE_API_KEY")
    token_b = get_env("TARGET_API_KEY")
    budget_id_a = get_env("SOURCE_BUDGET_ID")
    budget_id_b = get_env("TARGET_BUDGET_ID")
    shared_category_id = get_env("SHARED_CATEGORY_ID")
    shared_account_id = get_env("SHARED_ACCOUNT_ID")

    since_date = date.today() - timedelta(days=3)

    api_a = create_api(token_a)
    api_b = create_api(token_b)

    try:
        source_txns = api_a.get_transactions(
            budget_id_a, since_date=since_date
        ).data.transactions
    except ApiException as e:
        log.error(f"Error fetching transactions from SOURCE: {e}")
        return

    shared_txns = [
        txn for txn in source_txns if txn.category_id == shared_category_id
    ]
    log.info(f"Found {len(shared_txns)} shared transactions to sync")

    try:
        target_txns = api_b.get_transactions(
            budget_id_b, since_date=since_date
        ).data.transactions
    except ApiException as e:
        log.error(f"Error fetching transactions from TARGET: {e}")
        return

    import_ids = generate_import_ids(shared_txns)

    for txn, import_id in zip(shared_txns, import_ids):
        existing = next((t for t in target_txns if t.import_id == import_id), None)

        if existing:
            log.info(f"Updating existing transaction: {import_id}")
            try:
                updated_transaction = ExistingTransaction(
                    account_id=shared_account_id,
                    date=txn.var_date,
                    amount=txn.amount,
                    payee_name=txn.payee_name,
                    memo=txn.memo,
                    cleared=txn.cleared,
                    approved=txn.approved
                )
                api_b.update_transaction(
                    budget_id_b,
                    existing.id,
                    PutTransactionWrapper(transaction=updated_transaction)
                )
            except ApiException as e:
                log.error(f"Failed to update transaction {import_id}: {e}")
        else:
            log.info(f"Creating new transaction: {import_id}")
            try:
                new_transaction = NewTransaction(
                    account_id=shared_account_id,
                    date=txn.var_date,
                    amount=txn.amount,
                    payee_name=txn.payee_name,
                    memo=txn.memo,
                    cleared=txn.cleared,
                    approved=txn.approved,
                    import_id=import_id
                )
                wrapper = PostTransactionsWrapper(transactions=[new_transaction])
                api_b.create_transaction(budget_id_b, wrapper)
            except ApiException as e:
                log.error(f"Failed to create transaction {import_id}: {e}")

    source_import_ids = set(import_ids)

    for txn in target_txns:
        if txn.import_id and txn.import_id.startswith("SYNCED:") and txn.import_id not in source_import_ids:
            log.info(f"Deleting stale transaction: {txn.import_id}")
            try:
                api_b.delete_transaction(budget_id_b, txn.id)
            except ApiException as e:
                log.error(f"Failed to delete stale transaction {txn.import_id}: {e}")

    log.info("Sync complete.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    sync_transactions()
