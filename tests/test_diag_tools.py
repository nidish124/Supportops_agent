import pytest
from app.db.account_db import AccountDB
from app.simulator.diag_simulator import ProductDiagSimulator
from app.tools.diag_tools import CombinedDiagnosticsTool, AccountTool, ProductDiagTool
from datetime import datetime

def test_account_db_upsert_and_get():
    db = AccountDB(':memory:')
    user_id = "abc"
    account = {
        "user_id": user_id,
        "subscription": "active",
        "last_payment_attempt": "2025-12-01T12:00:00Z",
        "metadata": {"plan": "pro"}
    }

    db.upsert_account(account)
    fetch = db.get_account(user_id)
    assert fetch is not None
    assert fetch["user_id"] == user_id
    assert fetch["subscription"] == "active"
    assert fetch["metadata"]["plan"] == "pro"
    db.close()

def test_product_diag_simulator_rules():
    sim = ProductDiagSimulator()
    r1 = sim.run_diagnostic("u1", "1.6.1")
    assert r1['payment_gateway_status'] == 'timeout'
    assert "PAY_GATEWAY_TIMEOUT" in r1["error_codes"]

    r2 = sim.run_diagnostic("u2", "2.0.0")
    assert r2["payment_gateway_status"] == "ok"
    assert r2["service_health"] == "healthy"

    r3 = sim.run_diagnostic("u3", "beta-0.9")
    assert r3["service_health"] == "degraded"
    assert "SERVICE_HIGH_LATENCY" in r3["error_codes"]

def test_diag_tools_combined():
    db = AccountDB(":memory:")
    user_id = "acct-1"
    db.upsert_account({
        "user_id": user_id,
        "subscription": "active",
        "last_payment_attempt": "2025-12-01T12:00:00Z",
        "metadata": {"plan": "starter"}
    })

    account_tool = AccountTool(db)
    diag_tool = ProductDiagTool(ProductDiagSimulator())
    combined = CombinedDiagnosticsTool(account_tool, diag_tool)

    out = combined.run(user_id, "1.6.2")
    assert "account_state" in out and "product_diagnostics" in out
    assert out["account_state"]["user_id"] == user_id
    assert out["product_diagnostics"]["payment_gateway_status"] == "timeout"

    db.close()