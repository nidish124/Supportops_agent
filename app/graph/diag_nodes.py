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
    Decision node with:
      - Rule-based skeleton (deterministic)
      - LLM-based justification and runbook summarization (via synthesis_llm)
      - justification (LLM text)
      - runbook_summary (LLM generated if runbook_id exists)
    
    Backward compatibility:
      - Existing fields (recommended_action, runbook_id, severity, safety) unchanged
      - Tests expecting stable values continue to pass (LLM is MockLLM in tests)
    """
    def __init__(self, llm:Optional[Mockllm] = None, synthesis_llm: Optional[Any] = None):
        self.llm = llm or Mockllm()
        self.justify_prompt = (
            "You are an AI support agent.\n"
            "Given these diagnostics:\n{diagnostics}\n"
            "Explain in 1–2 sentences why the recommended action is appropriate.\n"
        )
        self.runbook_prompt = (
            "You are an AI runbook summarizer.\n"
            "Given the runbook id '{runbook_id}' and diagnostics:\n{diagnostics}\n"
            "Generate a short summary (2–3 lines) of the steps involved.\n"
        )
        self.synthesis_llm = synthesis_llm or Mockllm()


    def decide(self, diagnostics: Dict[str, Any], classify: Dict[str, Any]) -> Dict[str, Any]:
        acc = diagnostics.get("account_state") or {}
        product = diagnostics.get("product_diagnostics") or {}
        confidence = classify.get("confidence") or 0.0
        explanation = classify.get("explanation", "")
        issues = str(classify.get("issues", "")).lower()

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
            
        elif confidence > 0.70 and issues == "yes":
            recommended_action = {
                "type": "create_ticket",
                "summary": explanation or "Issue detected by classifier",
                "body": f"Auto-generated ticket. Classifier detected issue with high confidence ({confidence}).",
                "action_payload": {}
            }
            runbook_id = "User_issues_v1"
            severity = "low"
            safety["action_allowed"] = True
            safety["audit_hint"] = "Issues booked"

        else:
            recommended_action = {
                "type": "suggest_runbook",
                "summary": "No problem detected",
                "body": "System healthy. Suggest contacting user for more info if they persist.",
                "action_payload": {}
            }
            runbook_id = None
            severity = "low"
            # safety["action_allowed"] = False
            # safety["audit_hint"] = "no_action_needed"

        # Use mock LLM to create a short justification
        diagnostics_json = json.dumps(diagnostics, sort_keys=True)
        try:
            justification = self.synthesis_llm.predict(
                self.justify_prompt.format(diagnostics=diagnostics_json)
            )
            if isinstance(justification, dict):
                justification = json.dumps(justification)
        except Exception:
            justification = "Could not generate justification due to LLM error."
        
        runbook_summary = None
        if runbook_id:
            try:
                runbook_summary = self.synthesis_llm.predict(
                    self.runbook_prompt.format(runbook_id=runbook_id, diagnostics=diagnostics_json)
                )
                if isinstance(runbook_summary, dict):
                    runbook_summary = json.dump(runbook_summary)
            except Exception:
                runbook_summary = "Could not generate runbook summary due to LLM error."


        return {
            "recommended_action": recommended_action,
            "runbook_id": runbook_id,
            "severity": severity,
            "safety": safety,
            "justification": justification,
            "runbook_summary": runbook_summary
        }

    