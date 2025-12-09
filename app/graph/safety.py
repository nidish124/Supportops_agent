"""
SafetyGateNode - enforce action safety, create audit records, and produce audit tokens for allowed actions.

Rules implemented (strict):
 - action_levels mapping:
    - non-destructive: create_ticket, collect_account_info, suggest_runbook -> allowed automatically
    - destructive: reset_credentials, delete_account                        -> require human approval (confirm=True) and authorize executor
 - For allowed actions: insert audit row with status 'allowed' and return audit_token (HMAC of audit_id)
 - For requires approval: insert audit row with status 'requires_approval' and return required_approvals list
 - Authorization for confirmations: 
                                executor_id must be in 'authorized_approvers' list passed to SafetyGateNode (default ['human_approver'])
"""

import hmac
import hashlib
from typing import Dict, Any, List, Optional

from app.db.audit import AuditDB

class SafetyGateNode:
    def __init__(self, audit_db: Optional[AuditDB], secret : str = 'dev-secret', authorized_approvers: Optional[List[str]] = None):
        self.audit_db = audit_db or AuditDB(":memory:")
        self.secret = secret
        self.authorized_approvers = authorized_approvers or ["human_approver"]

        self.non_destructive = {"create_ticket", "collect_account_info", "suggest_runbook"}
        self.destructive = {"reset_credentials", "delete_account"}

    def _make_audit_token(self, audit_id: int) -> str:
        hm = hmac.new(self.secret.encode("utf-8"), str(audit_id).encode("utf-8"), hashlib.sha256)
        return hm.hexdigest()

    def evaluate(self, request_id: str, user_id: str, recommended_action: Dict[str, Any], 
        executor_id: Optional[str] = None, confirm : bool = False) -> Dict[str, Any]:
        """
        Evaluate action safety and record an audit row.

        Returns dict:
        {
          action_allowed: bool,
          required_approvals: [],
          audit_id: int,
          audit_token: str | None,
          status: 'allowed'|'requires_approval'|'rejected'
        }
        """

        action_type = recommended_action.get("type")
        payload = recommended_action.get("action_payload") or {}

        if action_type in self.non_destructive:
            status = 'allowed'
            audit_id = self.audit_db.insert_audit(request_id, user_id, action_type, payload, executor_id, status, None)
            token = self._make_audit_token(audit_id)
            self.audit_db.update_status(audit_id ,status,token )
            return {
                "action_allowed": True,
                "required_approvals": [],
                "audit_id": audit_id,
                "audit_token": token,
                "status": status
            }

        if action_type in self.destructive:
            if confirm and executor_id in self.authorized_approvers:
                status = 'allowed'
                audit_id = self.audit_db.insert_audit(request_id, user_id, action_type, payload, executor_id, status, None)
                token = self._make_audit_token(audit_id)

                self.audit_db.update_status( audit_id, status, token)
                return {
                    "action_allowed": True,
                    "required_approvals": [],
                    "audit_id": audit_id,
                    "audit_token": token,
                    "status": status
                }
            status = "requires_approval"
            audit_id = self.audit_db.insert_audit(request_id, user_id, action_type, payload, executor_id, status, None)
            return {
                "action_allowed": False,
                "required_approvals": ["human_support_agent"],
                "audit_id": audit_id,
                "audit_token": None,
                "status": status
            }

        status = "requires_approval"
        audit_id = self.audit_db.insert_audit(request_id, user_id, action_type or "unknown", payload, executor_id, status, None)
        return {
            "action_allowed": False,
            "required_approvals": ["human_support_agent"],
            "audit_id": audit_id,
            "audit_token": None,
            "status": status
        }


