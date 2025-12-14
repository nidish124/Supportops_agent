from dotenv.main import load_dotenv
import pytest
import os
from app.tools.github_ticket_tool import GitHubTicketTool
from app.db.audit import AuditDB
from app.graph.safety import SafetyGateNode
from app.graph.executor import ActionExecutorNode
from types import SimpleNamespace
from dotenv import load_dotenv

load_dotenv()


REQUEST_ID = "req-gh-1"
USER_ID = "user-gh-1"

class DummyGHTool:
    def __init__(self):
        self.calls = []

    def create_issue(self, title, body, labels):
        self.calls.append({"title": title, "body": body, "labels": labels})
        return {"ticket_id": "42", "ticket_url": "https://github.com/owner/repo/issues/42", "title": title, "labels": labels}

def test_executor_with_github_tool_executes_and_updates_audit():
    audit_db = AuditDB(":memory:")
    gate = SafetyGateNode(audit_db=audit_db, secret="test-secret")

    recommended_action = {
        "type": "create_ticket",
        "summary": "payment gateway timeout",
        "body": "user payment failed",
        "action_payload": {"ticket_labels": ["billing"]}
    }

    safety = gate.evaluate(REQUEST_ID, USER_ID, recommended_action, executor_id="system_bot", confirm=False)
    assert safety["action_allowed"] is True

    gh_tool = DummyGHTool()
    executor = ActionExecutorNode(audit_db=audit_db, ticket_tool=gh_tool)
    res = executor.execute(REQUEST_ID, USER_ID, recommended_action, safety, executor_id="system_bot")

    assert res["executed"] is True
    assert res["external_response"]["ticket_id"] == "42"
    assert res["audit"]["status"] == "executed"

def test_executor_handles_github_failure_and_marks_audit_rejected(monkeypatch):
    audit_db = AuditDB(":memory:")
    gate = SafetyGateNode(audit_db=audit_db, secret="test-secret")

    recommended_action = {
        "type": "create_ticket",
        "summary": "Payment gateway timeout",
        "body": "user payment failed",
        "action_payload": {"ticket_labels": ["billing"]}
    }

    safety = gate.evaluate(REQUEST_ID, USER_ID, recommended_action, executor_id="system_bot", confirm=False)
    assert safety["action_allowed"] is True

    class FailingTool:
        def create_issue(self, title, body, labels):
            raise RuntimeError("github down")

    executor = ActionExecutorNode(audit_db=audit_db, ticket_tool=FailingTool())
    res = executor.execute(REQUEST_ID, USER_ID, recommended_action, safety, executor_id="system_bot")

    assert res["executed"] is False
    assert res["reason"].startswith("external_failure")
    assert res["audit"]["status"] == "rejected"

def test_executor_github_issue_create():
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPO")
    
    print(token)
    # if not token or not repo:
    #     pytest.skip("GITHUB_TOKEN or GITHUB_REPO not set")

    audit_db = AuditDB(":memory:")
    gate = SafetyGateNode(audit_db=audit_db, secret="test-secret")
    
    # Use real tool
    gh_tool = GitHubTicketTool(token=token, repo_full_name=repo)
    executor = ActionExecutorNode(audit_db=audit_db, ticket_tool=gh_tool)

    recommended_action = {
        "type": "create_ticket",
        "summary": "Integration Test Ticket",
        "body": "This is an automated test ticket from the agent.",
        "action_payload": {"ticket_labels": ["test"]}
    }

    # We assume safety allows it (mocking safety or just relying on logic)
    # Re-using the logic from other tests, we need a safety result.
    safety = gate.evaluate("req-real-1", "user-real-1", recommended_action, executor_id="system_bot", confirm=False)
    print("safety:", safety)
    res = executor.execute("req-real-1", "user-real-1", recommended_action, safety, executor_id="system_bot")
    print("executor:", res)
    assert res["executed"] is True
    assert res["external_response"] is not None
    assert "ticket_url" in res["external_response"]
    assert res["audit"]["status"] == "executed"
