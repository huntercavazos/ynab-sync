import os
from dotenv import load_dotenv

# Load environment variables from a .env file into the environment.
# This allows the application to access sensitive configuration values securely.
load_dotenv()


def get_env(key: str) -> str:
    """
    Retrieve the value of an environment variable.

    Args:
        key (str): The name of the environment variable to retrieve.

    Returns:
        str: The value of the environment variable.

    Raises:
        ValueError: If the environment variable is not set.
    """
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Missing required environment variable: {key}")
    return value


# Configuration dictionary containing required environment variables for the application.
# Each key corresponds to a specific configuration value needed for the YNAB synchronization process.
CONFIG = {
    "source_api_key": get_env("SOURCE_API_KEY"),  # API key for the source YNAB budget.
    "source_budget_id": get_env("SOURCE_BUDGET_ID"),  # ID of the source YNAB budget.
    "target_api_key": get_env("TARGET_API_KEY"),  # API key for the target YNAB budget.
    "target_budget_id": get_env("TARGET_BUDGET_ID"),  # ID of the target YNAB budget.
    "shared_category_id": get_env("SHARED_CATEGORY_ID"),  # ID of the shared category to filter transactions.
    "shared_account_id": get_env("SHARED_ACCOUNT_ID")  # ID of the shared account in the target budget.
}