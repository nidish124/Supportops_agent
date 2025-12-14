import pytest
from app.graph.diag_nodes import DecisionNode
from app.llm.mock_llm import Mockllm

def test_decisionnode_generates_justification_and_runbook_summary():
    node = DecisionNode(synthesis_llm=Mockllm())

    diagnostics = {
        "account_state": {"user_id": "u1", "subscription": "active"},
        "product_diagnostics": {
            "service_health": "degraded",
            "payment_gateway_status": "ok",
            "notes": "CPU high",
            "error_codes": []
        }
    }

    out = node.decide(diagnostics)
    assert "justification" in out
    assert isinstance(out["justification"], str)

    # degraded service → runbook
    assert out["runbook_id"] == "degraded_service_v1"
    assert out["runbook_summary"] is not None
    assert isinstance(out["runbook_summary"], str)