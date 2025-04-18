import logging

from ynab_client.sync import sync_transactions

if __name__ == "__main__":
    # Configure the logging system to display messages with INFO level or higher.
    # The log messages will include the timestamp, log level, and the message content.
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    # Start the synchronization process for YNAB transactions.
    # This function is imported from the `ynab_client.sync` module.
    sync_transactions()