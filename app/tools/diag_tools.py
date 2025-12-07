"""
Tools that wrap AccountDB and ProductDiagSimulator.

- AccountTool: fetch account state from AccountDB
- ProductDiagTool: run diagnotstivs via ProductDiagSimulator
- CombinedDiagnosticsTool: convenience function to run both and merge into a single dict.
"""

from typing import Dict, Any
from app.db.account_db import AccountDB
from app.simulator.diag_simulator import ProductDiagSimulator

class AccountTool:
    def __init__(self, account_db: AccountDB):
        self.account_db = account_db

    def fetch_account(self, user_id: str) -> Dict[str, Any]:
        acc = self.account_db.get_account(user_id)
        if acc is None:
            return {"user_id": user_id, "subscription": None, "last_payment_attempt": None, "metadata": None}
        return acc

class ProductDiagTool:
    def __init__(self, simulator : ProductDiagSimulator):
        self.simulator = simulator

    def run(self, user_id: str, product_version: str) -> Dict[str, Any]:
        return self.simulator.run_diagnostic(user_id, product_version)

class CombinedDiagnosticsTool:
    def __init__(self, account_tool: AccountTool, diag_tool: ProductDiagTool) -> Dict[str, Any]:
        self.account_tool = account_tool
        self.diag_tool = diag_tool

    def run(self, user_id: str, product_version:str) -> Dict[str, Any]:
        acc = self.account_tool.fetch_account(user_id)
        diag = self.diag_tool.run(user_id,product_version)
        return {
            "account_state": acc,
            "product_diagnostics": diag
        }