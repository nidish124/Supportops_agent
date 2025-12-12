"""
ActionExecutorNode - executes allowed actions (non-destructive) using TicketTool and updates AuditDB.

Behavior:
 - Accepts safety_result dict from SafetyGateNode and recommended_action dict
 - If safety_result['action_allowed] is False -> return blocked result.
 - If allowed -> execute support action:
    - create_ticket -> call TicketTool.create_ticket(...)
- after successfull execution, update audit row status -> 'executed' and return execution result plus updated audit info.
- If unknown action type but allowed (unlikely), return rejected status.
"""

from typing import Dict, Any
from app.db.audit import AuditDB
from app.tools.github_ticket_tool import GitHubTicketTool
from app.tools.ticket_tool import Tickettool

class ActionExecutorNode:
    def __init__(self,  audit_db: AuditDB, ticket_tool: GitHubTicketTool = None):
        self.audit_db = audit_db or AuditDB(":memory:")
        self.tickettool = ticket_tool or GitHubTicketTool()
    
    def execute(self, request_id: str, user_id: str, recommended_action: Dict[str, Any], 
    safety_result: Dict[str, Any], executor_id: str = "system_bot") -> Dict[str, Any]:
        """
        Execute the action if allowed and update audit DB.

        Returns {
          "executed": bool,
          "reason": str,
          "external_response": dict | None,
          "audit": audit_row
        }
        """
        audit_id = safety_result.get("audit_id")
        if not safety_result.get("action_allowed", False):
            return {
                "executed": False,
                "reason" : "action_not_allowed",
                "external_response": None,
                "audit": self.audit_db.get_audit(audit_id) if audit_id else None
            }
        action_type = recommended_action.get("type")
        payload = recommended_action.get("action_payload", {})

        if action_type == "create_ticket":
            title = recommended_action.get("summary") or "Support ticket"
            body = recommended_action.get("body") or ""
            lables = payload.get("ticket_labels") or []

            try:
                external = self.tickettool.create_issue(title, body, lables)
            except Exception as exc:
                self.audit_db.update_status(audit_id, "rejected")
                audit_row = self.audit_db.get_audit(audit_id)
                return {
                    "executed": False,
                    "reason": f"external_failure: {str(exc)}",
                    "external_response": None,
                    "audit": audit_row
                }

            self.audit_db.update_status(audit_id, "executed")
            audit_row = self.audit_db.get_audit(audit_id)

            return {
                "executed": True,
                "reason": "ok",
                "external_response": external,
                "audit": audit_row
            }

        self.audit_db.update_status(audit_id, "rejected")
        audit_row = self.audit_db.get_audit(audit_id)
        return {
            "executed": False,
            "reason": f"unsupported_action_{action_type}",
            "external_response": None,
            "audit": audit_row
        }