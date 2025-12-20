import pytest
from app.graph.diag_nodes import DiagnosticsOrchestratorNode, DecisionNode
from app.db.account_mongo import MongoAccountDB
from app.simulator.diag_simulator import ProductDiagSimulator
from app.tools.diag_tools import AccountTool, ProductDiagTool, CombinedDiagnosticsTool
from app.llm.mock_llm import Mockllm

def make_combined_tool_with_account(user_id: str, subscription: str = "active", product_version: str = "1.6.2"):
    db = MongoAccountDB()
    db.upsert_account(
        {"user_id" : user_id,
        "subscription": subscription,
        "last_payment_attempt": "2025-12-01T12:00:00",
        "metadata": {"plan": "pro"}
        }
    )
    account_tool = AccountTool(db)
    diag_tool = ProductDiagTool(ProductDiagSimulator())
    combined = CombinedDiagnosticsTool(account_tool, diag_tool)
    return combined, db

def test_orchestrator_runs_and_returns_expected_shape():
    combined, db = make_combined_tool_with_account(user_id="nidish", subscription="active", product_version="1.6.0")
    orch = DiagnosticsOrchestratorNode(combined)
    out = orch.run("nidish", "1.6.0")
    assert "account_state" in out
    assert "product_diagnostics" in out
    assert out["account_state"]["user_id"] == "nidish"
    db.close()

def test_decision_node_payment_timeout_creates_ticket():
    combined, db = make_combined_tool_with_account(user_id="nidish", subscription="active", product_version="1.6.0")
    orch = DiagnosticsOrchestratorNode(combined)
    diag = orch.run("nidish", "1.6.0")

    decision = DecisionNode(llm = Mockllm())
    out = decision.decide(diag, {})

    assert out["recommended_action"]["type"] == "create_ticket"
    assert out["runbook_id"] == "payment_retry_flow_v1"
    assert out["severity"] == "high"
    assert out["safety"]["action_allowed"] == True
    assert "PAY_GATEWAY_TIMEOUT" in diag["product_diagnostics"]["error_codes"]
    db.close()

def test_decision_node_missing_subscription_collects_info():
    combined, db = make_combined_tool_with_account(user_id="nidish", subscription=None, product_version="1.6.0")
    orch = DiagnosticsOrchestratorNode(combined)
    diag = orch.run("nidish", "1.2.0")

    decision = DecisionNode(llm = Mockllm())
    out = decision.decide(diag, {})

    assert out["recommended_action"]["type"] == "collect_account_info"
    assert out["runbook_id"] == "collect_account_info_v1"
    assert out["severity"] == "medium"
    assert out["safety"]["action_allowed"] == False
    db.close()

def test_decision_node_degraded_service_suggest_runbook():
    combined, db = make_combined_tool_with_account(user_id="nidish", subscription="active", product_version="1.6.0")
    orch = DiagnosticsOrchestratorNode(combined)
    diag = orch.run("nidish", "beta-1.2")

    decision = DecisionNode(llm = Mockllm())
    out = decision.decide(diag, {})

    assert out["recommended_action"]["type"] == "suggest_runbook"
    assert out["runbook_id"] == "degraded_service_v1"
    assert out["severity"] == "medium"
    db.close()

def test_decision_node_high_confidence_issue_creates_ticket():
    combined, db = make_combined_tool_with_account(user_id="nidish", subscription="active", product_version="1.6.0")
    orch = DiagnosticsOrchestratorNode(combined)
    diag = orch.run("nidish", "1.6.0")

    # Mock classification with high confidence and issues=yes
    classification = {
        "confidence": 0.95,
        "issues": "Yes",
        "explanation": "Predicted critical issue"
    }

    decision = DecisionNode(llm = Mockllm())
    out = decision.decide(diag, classification)

    assert out["recommended_action"]["type"] == "create_ticket"
    #assert out["recommended_action"]["summary"] == "Predicted critical issue"
    #assert out["runbook_id"] == "User_issues_v1"
    assert out["safety"]["action_allowed"] == True
    db.close()