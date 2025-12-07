"""
DiagnosticOrchestratorNode and DecisionNode.

- DiagnosticOrchestratorNode - glue(using) to CombinedDiagnosticTool.
- DecisionNode - rule-first decision logic with MockLLM for justification fallback

"""

from typing import Dict, Any, Optional
from app.tools.diag_tools import CombinedDiagnosticsTool
from app.llm.mock_llm import Mockllm, PromptTemplate
import json

class DiagnosticsOrchestratorNode:
    def __init__(self, combined_tool: CombinedDiagnosticsTool):
        self.combined_tool = combined_tool

    def run(self, user_id: str, product_id: Optional[str]) -> Dict[str, Any]:
        """
        Run account + product diagnostics and return a merged dict.
        """
        return self.combined_tool.run(user_id, product_id)

class DecisionNode:
    """
    Accept diagnostics dict and produce recommended_action + runbook + safety info.

    Priority rules (checked in order):
    1. If payment_gateway_status == "timeout" -> create_ticket (severity=high)
    2. If account subscription is None -> collect_account_info (severity=medium)
    3. If service_health == "degraded" -> suggest_runbook (severity=medium)
    4. Else -> suggest_runbook (severity=low, runbook_id=null)

    Use MockLLM to produce a short justification string (deterministic).
    """
    def __init__(self, llm:Optional[Mockllm] = None):
        self.llm = llm or Mockllm()
        self.template = PromptTemplate(
            "Decision maker. Given diagnostics: {diagnostics_json}\nReturn a short justification sentence."
        )

    def decide(self, diagnostics: Dict[str, Any]) -> Dict[str, Any]:
        acc = diagnostics.get("account_state") or {}
        product = diagnostics.get("product_diagnostics") or {}

        payment_status = (product.get("payment_gateway_status") or "").lower()
        service_health = (product.get("service_health") or "").lower()
        subscription = acc.get("subscription")

        recommended_action = {
            "type": "suggest_runbook",
            "summary": "No immediate issue detected",
            "body": "Suggest checking general runbooks.",
            "action_payload": {}
        }

        runbook_id = None
        severity = "low"
        safety = {"action_allowed": False, "required_approvals": [], "audit_hint": ""}

        # Rule 1: payment timeout -> create ticket
        if payment_status == "timeout":
            recommended_action = {
            "type": "create_ticket",
            "summary": "Payment gateway timeout detected",
            "body": f"Payment gateway returned timeout for user {acc.get('user_id')}. Recommend creating support ticket and investigate gateway.",
            "action_payload": {"ticket_labels": ["billing", "payment-gateway", "high-severity"]}
            }

            runbook_id = "payment_retry_flow_v1"
            severity = "high"
            safety["action_allowed"] = True
            safety["audit_hint"] = "create_ticket_requires_audit_record"
        
        # Rule 2: missing subscription -> collect info

        elif not subscription:
            recommended_action = {
                "type": "collect_account_info",
                "summary": "Account missing subscription details",
                "body": f"Account {acc.get('user_id')} has no subscription on record. Request details from user.",
                "action_payload": {"request_fields": ["subscription", "last_payment_attempt"]}
            }
            runbook_id = "collect_account_info_v1"
            severity = "medium"
            safety["action_allowed"] = False
            safety["required_approvals"] = ["human_support_agent"]
            safety["audit_hint"] = "requires_manual_interaction"

        # Rule 3: degraded service -> suggest runbook
        elif service_health == "degraded":
            recommended_action = {
                "type": "suggest_runbook",
                "summary": "Service degraded; follow degraded-service runbook",
                "body": f"Service reported degraded health: {product.get('notes')}",
                "action_payload": {"runbook": "degraded_service_v1"}
            }
            runbook_id = "degraded_service_v1"
            severity = "medium"
            safety["action_allowed"] = False
            safety["audit_hint"] = "runbook_suggestion"

        else:
            recommended_action = {
                "type": "suggest_runbook",
                "summary": "No problem detected",
                "body": "System healthy. Suggest contacting user for more info if they persist.",
                "action_payload": {}
            }
            runbook_id = None
            severity = "low"
            safety["action_allowed"] = False
            safety["audit_hint"] = "no_action_needed"

        # Use mock LLM to create a short justification
        diagnostics_json = json.dumps(diagnostics, sort_keys=True)
        prompt = self.template.format(diagnostics_json = diagnostics_json)
        justification = self.llm.predict(prompt)

        if isinstance(justification, str):
            justification_text = justification.strip()[:200]
        else:
            justification_text = str(justification)

        return {
            "recommended_action": recommended_action,
            "runbook_id": runbook_id,
            "severity": severity,
            "safety": safety,
            "justification": justification_text
        }