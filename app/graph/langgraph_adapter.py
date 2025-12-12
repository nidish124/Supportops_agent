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
from app.db.account_db import AccountDB
from app.db.audit import AuditDB
from app.tools.ticket_tool import Tickettool
from app.tools.github_ticket_tool import GitHubTicketTool  # may raise if token missing
from app.tools.ticket_tool import Tickettool as LocalTicketTool

# LLMs and adapters
from app.llm.mock_llm import Mockllm
from app.llm.adapter import MockLLMAdapter, LangchainLLM  # LangChainLLM optional skeleton

# Executor
from app.graph.executor import ActionExecutorNode
from app.graph.safety import SafetyGateNode

class TriageState(TypedDict, total=False):
    payload: Dict[str, Any]
    model: Any
    classification: Dict[str, Any]
    diagnostics: Dict[str, Any]
    decision: Dict[str, Any]
    safety: Dict[str, Any]
    execution: Dict[str, Any]


class LangGraphTriage:
    def __init__(self, db_path: str = ":memory:", github_token : Optional[str] = None, github_repo: Optional[str]= None,
    classifier_llm: Optional[Any] = None, synthesis_llm: Optional[Any] = None):
        github_token = github_token or os.getenv("GITHUB_TOKEN")
        github_repo = github_repo or os.getenv("GITHUB_REPO")

        self.account_db = AccountDB(db_path)
        self.audit_db = AuditDB(db_path)

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