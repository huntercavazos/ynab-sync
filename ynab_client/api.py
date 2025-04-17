import ynab


def get_api_clients(token: str):
    configuration = ynab.Configuration(api_key=token)
    api_client = ynab.ApiClient(configuration)

    budgets_api = ynab.BudgetsApi(api_client)
    accounts_api = ynab.AccountsApi(api_client)
    transactions_api = ynab.TransactionsApi(api_client)

    return api_client, budgets_api, accounts_api, transactions_api
