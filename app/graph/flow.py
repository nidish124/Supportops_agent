"""
TriageFlow - composes PraseInoutNode, IntentClassifierNode, DiagnosticOrchestratorNode, DecisionNode.

Usage:

flow = TriageFlow()
result = flow.run(payload_dict)
"""
from typing import Dict, Any
from app.graph.nodes import ParseInputNode, IntentClassifierNode
from app.graph.diag_nodes import DiagnosticsOrchestratorNode, DecisionNode
from app.tools.diag_tools import AccountTool, ProductDiagTool, CombinedDiagnosticsTool
from app.simulator.diag_simulator import ProductDiagSimulator
from app.db.account_db import AccountDB

class TriageFlow:
    def __init__(self, db_path: str = "accounts.db"):
        self.db = AccountDB(db_path)
        #tools
        self.acc_tool = AccountTool(self.db)
        self.diag_tool = ProductDiagTool(ProductDiagSimulator())
        self.combined = CombinedDiagnosticsTool(self.acc_tool, self.diag_tool)

        #Nodes
        self.parser = ParseInputNode()
        self.clasifier = IntentClassifierNode()
        self.orchestrator = DiagnosticsOrchestratorNode(self.combined)
        self.decision = DecisionNode()

    
    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        
        model = self.parser.parse(payload)

        classification = self.clasifier.classify(model)

        product_version = None
        if model.metadata and getattr(model.metadata, "product_version", None):
            product_version = model.metadata.product_version

        diagnostic = self.orchestrator.run(model.user_id, product_version)

        diagnostic["classification"] = classification

        decision = self.decision.decide(diagnostic)

        if diagnostic.get("account_state") and diagnostic["account_state"].get("user_id"):
            acc = diagnostic["account_state"]

            try:
                self.db.upsert_account({
                    "user_id": acc["user_id"],
                    "subscription": acc.get("subscription"),
                    "last_payment_attempt": acc.get("last_payment_attempt"),
                    "metadata": acc.get("metadata", {})
                })
            except Exception:
                pass

        return {
            "request_id": model.request_id,
            "user_id": model.user_id,
            "triage": classification,
            "diagnostics": diagnostic,
            "decision": decision
        }

    def close(self):
        try:
            self.db.close()
        except Exception:
            pass