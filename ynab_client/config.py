import os
from dotenv import load_dotenv

if os.path.exists(".env"):
    load_dotenv()

def get_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Missing required environment variable: {key}")
    return value

CONFIG = {
    "source_api_key": get_env("SOURCE_API_KEY"),
    "source_budget_id": get_env("SOURCE_BUDGET_ID"),
    "target_api_key": get_env("TARGET_API_KEY"),
    "target_budget_id": get_env("TARGET_BUDGET_ID"),
    "shared_category_id": get_env("SHARED_CATEGORY_ID"),
    "shared_account_id": get_env("SHARED_ACCOUNT_ID")
}
