import pytest
from app.db.audit import AuditDB
from app.graph.safety import SafetyGateNode
from app.graph.executor import ActionExecutorNode
from app.tools.ticket_tool import Tickettool

REQUEST_ID = "req-exec-1"
USER_ID = "user-exec-1"

def test_executor_executes_create_ticket_and_updates_audit():
    db = AuditDB(":memory:")
    gate = SafetyGateNode(db, "test-secret")
    recommended_action = {
        "type": "create_ticket",
        "summary": "Payment gateway timeout",
        "body": "User payment failed",
        "action_payload": {"ticket_labels": ["billing"]}
    }

    safety = gate.evaluate(REQUEST_ID, USER_ID, recommended_action, "system_bot", True)
    assert safety["action_allowed"] is True
    audit_id = safety["audit_id"]

    # ticket_tool = Tickettool("demo-repo")
    executor = ActionExecutorNode(db, Tickettool("support_agent"))
    res = executor.execute(REQUEST_ID, USER_ID, recommended_action, safety, 'system_bot')
    print(res)
    assert res["executed"] is True
    assert res["external_response"] is not None
    assert "ticket_url" in res["external_response"]

    audit_row = db.get_audit(audit_id)
    print(audit_row)
    assert audit_row["status"] == "executed"
    db.close()


def test_executor_blocks_when_safety_denies_execution():
    audit_db = AuditDB(":memory:")
    gate = SafetyGateNode(audit_db, "test-secret")
    
    destructive_action = {
        "type": "reset_credentials",
        "summary": "Reset user creds",
        "body": "Resetting user's password",
        "action_payload": {"force": True}
    }
    safety_block = gate.evaluate(REQUEST_ID, USER_ID, destructive_action, 'system_bot', False)

    assert safety_block["action_allowed"] is False
    audit_id = safety_block["audit_id"]
    executor = ActionExecutorNode(audit_db, ticket_tool=Tickettool())
    res = executor.execute(REQUEST_ID, USER_ID, destructive_action, safety_block, executor_id="system_bot")

    assert res["executed"] is False
    assert res["reason"] == "action_not_allowed"

    audit_row = audit_db.get_audit(safety_block["audit_id"])
    assert audit_row["status"] == "requires_approval"
    audit_db.close()