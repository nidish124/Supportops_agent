"""
LangGraph-based triage flow.

This flow wires:
- classifier_llm -> IntentClassifierNode (pluggable)
- synthesis_llm -> DecisionNode (pluggable)
- ticket tool -> GitHubTicketTool when GITHUB_TOKEN & GITHUB_REPO env present, otherwise TicketTool fallback

Behavior:
- Deterministic by default (MockLLM + TicketTool).
- When running with env vars set, the flow will use the real GitHub API for issue creation.
- The graph uses LangGraph StateGraph to run nodes in sequence and branch on safety.
"""

import os
from typing import TypedDict, Dict, Any, Optional
from datetime import datetime

from app.graph.nodes import ParseInputNode, IntentClassifierNode
from app.graph.diag_nodes import DiagnosticsOrchestratorNode, DecisionNode
from app.tools.diag_tools import AccountTool, ProductDiagTool, CombinedDiagnosticsTool
from app.simulator.diag_simulator import ProductDiagSimulator
from app.db.account_mongo import MongoAccountDB
from app.db.audit_mongo import MongoAuditDB
from app.tools.ticket_tool import Tickettool
from app.tools.github_ticket_tool import GitHubTicketTool  # may raise if token missing
from app.tools.ticket_tool import Tickettool as LocalTicketTool

# LLMs and adapters
from app.llm.mock_llm import Mockllm
from app.llm.adapter import MockLLMAdapter, LangchainLLM  # LangChainLLM optional skeleton

# Executor
from app.graph.executor import ActionExecutorNode
from app.graph.safety import SafetyGateNode

from langgraph.graph import StateGraph
from langgraph.constants import START, END
from dotenv import load_dotenv

load_dotenv()

class TriageState(TypedDict, total=False):
    payload: Dict[str, Any]
    model: Any
    classification: Dict[str, Any]
    diagnostics: Dict[str, Any]
    decision: Dict[str, Any]
    safety: Dict[str, Any]
    execution: Dict[str, Any]

class LangGraphTriage:
    def __init__(self, db_path: str = None, github_token : Optional[str] = None, github_repo: Optional[str]= None,
    classifier_llm: Optional[Any] = None, synthesis_llm: Optional[Any] = None):
        github_token = github_token or os.getenv("GITHUB_TOKEN")
        github_repo = github_repo or os.getenv("GITHUB_REPO")

        self.account_db = MongoAccountDB()
        self.audit_db = MongoAuditDB()

        self.account_tool = AccountTool(self.account_db)
        self.diag_tool = ProductDiagTool(ProductDiagSimulator())
        self.combined = CombinedDiagnosticsTool(self.account_tool, self.diag_tool)

        if github_token and github_repo:
            try:
                self.ticket_tool = GitHubTicketTool(github_token, github_repo)
            except Exception as e:
                self.ticket_tool = LocalTicketTool()

        else:
            self.ticket_tool = LocalTicketTool()

        ##LLM Adapters:
        if classifier_llm:
            self.classifier_llm = classifier_llm
        else:
            self.classifier_llm = Mockllm()

        if synthesis_llm:
            self.synthesis_llm = synthesis_llm
        else:
            self.synthesis_llm = Mockllm()

        self.parser_node_impl = ParseInputNode()

        self.classifier_node_impl = IntentClassifierNode(llm=self.classifier_llm)
        self.orch_impl = DiagnosticsOrchestratorNode(self.combined)
        self.decision_impl = DecisionNode()

        setattr(self.decision_impl, "synthesis_llm", self.synthesis_llm)

        self.safety_impl = SafetyGateNode(audit_db=self.audit_db, secret="lg-secret", authorized_approvers=["human_approver"])
        self.executor_impl = ActionExecutorNode(audit_db=self.audit_db, ticket_tool=self.ticket_tool)

        self.graph = self._build_graph()

    def node_parse(self, state: TriageState) -> TriageState:
        model = self.parser_node_impl.parse(state["payload"])
        return {"model": model}

    def node_classify(self, state: TriageState) -> TriageState:
        model = state["model"]
        classification = self.classifier_node_impl.classify(model)
        return {"classification": classification}

    def node_diagnostics(self, state: TriageState) -> TriageState:
        model = state["model"]
        pv = None
        if model.metadata and model.metadata.product_version:
            pv = model.metadata.product_version
        diagnostic = self.orch_impl.run(model.user_id, pv)
        diagnostic["classification"] = state.get("classification", {})
        return {"diagnostics": diagnostic}

    def node_decision(self, state: TriageState) -> TriageState:
        diag = state["diagnostics"]
        decision = self.decision_impl.decide(diag)
        return {"decision": decision}

    def node_safety(self, state: TriageState) -> TriageState:
        model = state["model"]
        decision = state["decision"]
        safety = self.safety_impl.evaluate(model.request_id, model.user_id, decision["recommended_action"], executor_id="system_bot", confirm= False)
        return {"safety": safety}

    def node_execution(self, state: TriageState) -> TriageState:
        model = state["model"]
        decision = state["decision"]
        safety = state["safety"]
        exec_res  = self.executor_impl.execute(model.request_id, model.user_id, decision["recommended_action"], safety, executor_id="system_bot")
        return {"execution": exec_res}

    def node_noop_execution(self, state: TriageState) -> TriageState:
        return {"execution": {"executed": False, 
                "reason": "not_allowed", 
                "external_response": None,
                "audit": self.audit_db.get_audit(state["safety"]["audit_id"])}}

    def _build_graph(self):
        graph = StateGraph(TriageState)

        graph.add_node("parse", self.node_parse)
        graph.add_node("classification", self.node_classify)
        graph.add_node("diagnostics", self.node_diagnostics)
        graph.add_node("decision", self.node_decision)
        graph.add_node("safety", self.node_safety)
        graph.add_node("execute", self.node_execution)
        graph.add_node("noexec", self.node_noop_execution)

        graph.add_edge(START, "parse")
        graph.add_edge("parse", "classification")
        graph.add_edge("classification", "diagnostics")
        graph.add_edge("diagnostics", "decision")
        graph.add_edge("decision", "safety")
        
        def route_safety(state: TriageState):
            if state["safety"].get("action_allowed"):
                return "execute"
            return "noexec"

        graph.add_conditional_edges("safety", route_safety, {"execute": "execute", "noexec": "noexec"})

        graph.add_edge("execute", END)
        graph.add_edge("noexec", END)

        graph.set_entry_point("parse")
        graph.set_finish_point("execute")
        graph.set_finish_point("noexec")

        app = graph.compile()
        return app

    def invoke(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke the compiled graph.
        """

        initial = {"payload": payload}
        res = self.graph.invoke(initial)

        try:
            acc = res.get("diagnostics", {}).get("account_status")
            if acc:
                self.account_db.upsert_account({
                    "user_id": acc.get("user_id"),
                    "subscription": acc.get("subscription"),
                    "last_payment_attempt": acc.get("last_payment_attempt"),
                    "metadata": acc.get("metadata", {})
                })
        except Exception:
            pass

        return {
            "request_id": res["model"].request_id,
            "user_id": res["model"].user_id,
            "triage": res.get("classification"),
            "diagnostics": res.get("diagnostics"),
            "decision": res.get("decision"),
            "safety": res.get("safety"),
            "execution": res.get("execution")
        }

    def close(self):
        try:
            self.account_db.close()
        except Exception:
            pass
        try:
            self.audit_db.close()
        except Exception:
            pass