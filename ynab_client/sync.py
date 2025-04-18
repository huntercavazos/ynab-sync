import logging
from collections import defaultdict
from datetime import date, timedelta

import ynab
from ynab.api.transactions_api import TransactionsApi
from ynab.models.existing_transaction import ExistingTransaction
from ynab.models.new_transaction import NewTransaction
from ynab.models.post_transactions_wrapper import PostTransactionsWrapper
from ynab.models.patch_transactions_wrapper import PatchTransactionsWrapper
from ynab.rest import ApiException

from ynab_client.config import CONFIG

def create_api(token: str) -> TransactionsApi:
    """
    Create a YNAB Transactions API client.

    Args:
        token (str): The personal access token for the YNAB API.

    Returns:
        TransactionsApi: An instance of the TransactionsApi client.
    """
    config = ynab.Configuration(access_token=token)
    return TransactionsApi(ynab.ApiClient(config))

def generate_import_ids(transactions):
    """
    Generate unique import IDs for a list of transactions.

    Args:
        transactions (list): A list of transaction objects.

    Returns:
        list: A list of unique import IDs for the transactions.
    """
    counter = defaultdict(int)
    import_ids = []

    for txn in transactions:
        key = f"{txn.var_date}:{txn.amount}"  # Unique key based on transaction date and amount
        count = counter[key]
        suffix = f":{count}" if count > 0 else ""  # Add a suffix if there are duplicate keys
        import_id = f"SYNCED:{key}{suffix}"  # Format the import ID
        import_ids.append(import_id)
        counter[key] += 1

    return import_ids

def sync_transactions():
    """
    Synchronize transactions between two YNAB budgets.

    This function fetches transactions from a source budget, filters shared transactions,
    and synchronizes them with a target budget. It handles creating, updating, and deleting
    transactions in batches where possible.

    Logs:
        Logs the progress and any errors encountered during the synchronization process.
    """
    log = logging.getLogger("ynab_sync")
    log.info("Starting sync process")

    # Retrieve configuration values
    token_a = CONFIG["source_api_key"]
    token_b = CONFIG["target_api_key"]
    budget_id_a = CONFIG["source_budget_id"]
    budget_id_b = CONFIG["target_budget_id"]
    shared_category_id = CONFIG["shared_category_id"]
    shared_account_id = CONFIG["shared_account_id"]

    # Define the date range for transactions to sync
    since_date = date.today() - timedelta(days=3)

    # Create API clients for source and target budgets
    api_a = create_api(token_a)
    api_b = create_api(token_b)

    try:
        # Fetch transactions from the source budget
        source_txns = api_a.get_transactions(budget_id_a, since_date=since_date).data.transactions
    except ApiException as e:
        log.error(f"Error fetching transactions from SOURCE: {e}")
        return

    # Filter transactions belonging to the shared category
    shared_txns = [txn for txn in source_txns if txn.category_id == shared_category_id]

    if not shared_txns:
        log.info("No shared transactions found to sync")
        return

    try:
        # Fetch transactions from the target budget
        target_txns = api_b.get_transactions(budget_id_b, since_date=since_date).data.transactions
    except ApiException as e:
        log.error(f"Error fetching transactions from TARGET: {e}")
        return

    # Generate unique import IDs for shared transactions
    import_ids = generate_import_ids(shared_txns)

    # Group transactions by type
    new_txns = []
    update_txns = []

    for txn, import_id in zip(shared_txns, import_ids):
        existing = next((t for t in target_txns if t.import_id == import_id), None)

        if existing:
            # Only update if any relevant fields have changed
            if (
                existing.var_date != txn.var_date or
                existing.amount != txn.amount or
                existing.payee_name != txn.payee_name or
                existing.memo != txn.memo or
                existing.cleared != txn.cleared or
                existing.approved != txn.approved
            ):
                update_txns.append({
                    "id": existing.id,
                    "account_id": shared_account_id,
                    "date": txn.var_date,
                    "amount": txn.amount,
                    "payee_name": txn.payee_name,
                    "memo": txn.memo,
                    "cleared": txn.cleared,
                    "approved": txn.approved
                })
        else:
            new_txns.append(NewTransaction(
                account_id=shared_account_id,
                date=txn.var_date,
                amount=txn.amount,
                payee_name=txn.payee_name,
                memo=txn.memo,
                cleared=txn.cleared,
                approved=txn.approved,
                import_id=import_id
            ))

    if new_txns or update_txns:
        log.info(f"Found {len(new_txns) + len(update_txns)} shared transactions to sync")

    # Batch create new transactions
    if new_txns:
        log.info(f"Creating {len(new_txns)} new transactions...")
        try:
            wrapper = PostTransactionsWrapper(transactions=new_txns)
            api_b.create_transaction(budget_id_b, wrapper)
        except ApiException as e:
            log.error(f"Failed to create transactions: {e}")

    # Batch update existing transactions
    if update_txns:
        log.info(f"Updating {len(update_txns)} existing transactions...")
        try:
            patch_wrapper = PatchTransactionsWrapper(transactions=update_txns)
            api_b.update_transactions(budget_id_b, patch_wrapper)
        except ApiException as e:
            log.error(f"Failed to update transactions: {e}")

    # Identify and delete stale transactions in the target budget
    source_import_ids = set(import_ids)
    stale_txns = [
        txn for txn in target_txns
        if txn.import_id and txn.import_id.startswith("SYNCED:") and txn.import_id not in source_import_ids
    ]

    if stale_txns:
        log.info(f"Deleting {len(stale_txns)} stale transactions...")
        for txn in stale_txns:
            try:
                api_b.delete_transaction(budget_id_b, txn.id)
                log.info(f"Deleted stale transaction: {txn.import_id}")
            except ApiException as e:
                log.error(f"Failed to delete stale transaction {txn.import_id}: {e}")

    if not new_txns and not update_txns and not stale_txns:
        log.info("No changes were necessary.")

    log.info("Sync complete.")
