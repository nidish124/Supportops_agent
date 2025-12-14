import pytest
from app.graph.safety import SafetyGateNode
from app.db.audit_mongo import MongoAuditDB

request_id = "req-safety-1"
user_id = "user-safety-1"

def test_create_ticket_is_allowed_and_audited():
    db = MongoAuditDB()
    gate = SafetyGateNode(db, "test-secrets")
    recommended_action = {
            "type": "create_ticket",
            "summary": "Payment gateway timeout detected",
            "body": f"Payment gateway returned timeout for user {user_id}. Recommend creating support ticket and investigate gateway.",
            "action_payload": {"ticket_labels": ["billing", "payment-gateway", "high-severity"]}
            }
    eval = gate.evaluate(request_id, user_id, recommended_action, "system-bot", False)
    assert eval["action_allowed"] == True
    assert eval["audit_id"] is not None
    assert eval["audit_token"] is not None
    row = db.get_audit(eval["audit_id"])
    assert row is not None
    assert eval["status"] == row["status"]
    assert eval["audit_token"] == row["audit_token"]
    db.close()


def test_destructive_action_requires_approval_and_blocks_then_allows_with_confirm():
    db = MongoAuditDB()
    gate = SafetyGateNode(db, "test-secrets", ["human_approver"])
    recommended_action = {
            "type": "reset_credentials",
            "summary": "Reset user creds",
            "body": "Resetting user's password",
            "action_payload": {"force": True}
            }
    #1 without confirm - should request approval
    res_blocked = gate.evaluate(request_id, user_id, recommended_action, "system-bot", False)
    assert res_blocked["action_allowed"] == False
    assert res_blocked["required_approvals"] == ["human_support_agent"]
    blocked_audit = db.get_audit(res_blocked["audit_id"])
    assert blocked_audit["status"] == "requires_approval"

    #2 with confirm but unauthorized executor -> still blocked
    res_blocked2 = gate.evaluate(request_id, user_id, recommended_action, "system_bot", True)
    assert res_blocked2["action_allowed"] is False
    row2 = db.get_audit(res_blocked2["audit_id"])
    assert row2["status"] == "requires_approval"


    #3 with confirm and authorized executor
    res_allowed = gate.evaluate(request_id, user_id, recommended_action, "human_approver", True)
    assert res_allowed["action_allowed"] is True
    assert res_allowed["audit_token"] is not None
    row3 = db.get_audit(res_allowed["audit_id"])
    assert row3["status"] == "allowed"

    db.close()
