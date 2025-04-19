import logging
from collections import defaultdict
from datetime import date, timedelta

import ynab
from ynab.api.transactions_api import TransactionsApi
from ynab.models.new_transaction import NewTransaction
from ynab.models.patch_transactions_wrapper import PatchTransactionsWrapper
from ynab.models.post_transactions_wrapper import PostTransactionsWrapper
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


def fetch_source_transactions(api_a, budget_id_a, shared_category_id, shared_account_id, since_date, log):
    """
    Fetch transactions from the source budget and filter shared transactions.

    Args:
        api_a (TransactionsApi): The API client for the source budget.
        budget_id_a (str): The ID of the source budget.
        shared_category_id (str): The ID of the shared category.
        shared_account_id (str): The ID of the shared account.
        since_date (date): The date from which to fetch transactions.
        log (Logger): The logger instance for logging errors.

    Returns:
        list: A list of shared transactions as NewTransaction objects.
    """
    try:
        source_txns = api_a.get_transactions(budget_id_a, since_date=since_date).data.transactions
    except ApiException as e:
        log.error(f"Error fetching transactions from SOURCE: {e}")
        return []

    shared_txns = []
    for txn in source_txns:
        if txn.category_id == shared_category_id:
            shared_txns.append(NewTransaction(
                account_id=shared_account_id,
                date=txn.var_date,
                amount=txn.amount,
                payee_name=txn.payee_name,
                memo=txn.memo,
                cleared=txn.cleared
            ))
        elif txn.subtransactions:
            for sub in txn.subtransactions:
                if sub.category_id == shared_category_id:
                    shared_txns.append(NewTransaction(
                        account_id=shared_account_id,
                        date=txn.var_date,
                        amount=sub.amount,
                        payee_name=txn.payee_name,
                        memo=sub.memo,
                        cleared=txn.cleared
                    ))

    return shared_txns


def fetch_target_transactions(api_b, budget_id_b, since_date, log):
    """
    Fetch transactions from the target budget.

    Args:
        api_b (TransactionsApi): The API client for the target budget.
        budget_id_b (str): The ID of the target budget.
        since_date (date): The date from which to fetch transactions.
        log (Logger): The logger instance for logging errors.

    Returns:
        list: A list of transactions from the target budget.
    """
    try:
        return api_b.get_transactions(budget_id_b, since_date=since_date).data.transactions
    except ApiException as e:
        log.error(f"Error fetching transactions from TARGET: {e}")
        return []


def classify_transactions(shared_txns, target_txns, import_ids, shared_account_id):
    """
    Classify transactions into new and updated transactions.

    Args:
        shared_txns (list): A list of shared transactions.
        target_txns (list): A list of transactions from the target budget.
        import_ids (list): A list of unique import IDs for the shared transactions.
        shared_account_id (str): The ID of the shared account.

    Returns:
        tuple: A tuple containing two lists - new transactions and updated transactions.
    """
    new_txns = []
    update_txns = []

    for txn, import_id in zip(shared_txns, import_ids):
        existing = next((t for t in target_txns if t.import_id == import_id), None)

        if existing:
            if (
                    existing.account_id != shared_account_id or
                    existing.var_date != txn.var_date or
                    existing.amount != txn.amount or
                    existing.payee_name != txn.payee_name or
                    existing.memo != txn.memo or
                    existing.cleared != txn.cleared
            ):
                update_txns.append({
                    "id": existing.id,
                    "account_id": shared_account_id,
                    "date": txn.var_date,
                    "amount": txn.amount,
                    "payee_name": txn.payee_name,
                    "memo": txn.memo,
                    "cleared": txn.cleared
                })
        else:
            txn.import_id = import_id
            new_txns.append(txn)

    return new_txns, update_txns


def delete_stale_transactions(api_b, budget_id_b, target_txns, source_import_ids, log):
    """
    Delete stale transactions from the target budget.

    Args:
        api_b (TransactionsApi): The API client for the target budget.
        budget_id_b (str): The ID of the target budget.
        target_txns (list): A list of transactions from the target budget.
        source_import_ids (set): A set of import IDs from the source transactions.
        log (Logger): The logger instance for logging errors.

    Returns:
        list: A list of stale transactions that were deleted.
    """
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

    return stale_txns


def sync_transactions():
    """
    Synchronize transactions between two YNAB budgets.

    This function fetches transactions from a source budget, filters shared transactions,
    and synchronizes them with a target budget. It handles creating, updating, and deleting
    transactions as needed.

    Logs:
        Logs the progress and any errors encountered during the synchronization process.
    """
    log = logging.getLogger("ynab_sync")
    log.info("Starting sync process")

    token_a = CONFIG["source_api_key"]
    token_b = CONFIG["target_api_key"]
    budget_id_a = CONFIG["source_budget_id"]
    budget_id_b = CONFIG["target_budget_id"]
    shared_category_id = CONFIG["shared_category_id"]
    shared_account_id = CONFIG["shared_account_id"]

    since_date = date.today() - timedelta(days=3)

    api_a = create_api(token_a)
    api_b = create_api(token_b)

    shared_txns = fetch_source_transactions(api_a, budget_id_a, shared_category_id, shared_account_id, since_date, log)
    if not shared_txns:
        log.info("No shared transactions found to sync")
        return

    target_txns = fetch_target_transactions(api_b, budget_id_b, since_date, log)
    if not target_txns:
        return

    import_ids = generate_import_ids(shared_txns)
    new_txns, update_txns = classify_transactions(shared_txns, target_txns, import_ids, shared_account_id)

    if new_txns:
        log.info(f"Creating {len(new_txns)} new transactions...")
        try:
            wrapper = PostTransactionsWrapper(transactions=new_txns)
            api_b.create_transaction(budget_id_b, wrapper)
        except ApiException as e:
            log.error(f"Failed to create transactions: {e}")

    if update_txns:
        log.info(f"Updating {len(update_txns)} existing transactions...")
        try:
            patch_wrapper = PatchTransactionsWrapper(transactions=update_txns)
            api_b.update_transactions(budget_id_b, patch_wrapper)
        except ApiException as e:
            log.error(f"Failed to update transactions: {e}")

    stale_txns = delete_stale_transactions(api_b, budget_id_b, target_txns, set(import_ids), log)

    if not new_txns and not update_txns and not stale_txns:
        log.info("No changes were necessary.")

    log.info("Sync complete.")
