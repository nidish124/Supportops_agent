from fastapi.testclient import TestClient
from app.main import app
import json
from unittest.mock import patch
import mongomock

from app.graph.diag_nodes import DiagnosticsOrchestratorNode, DecisionNode
from app.db.account_mongo import MongoAccountDB
from app.simulator.diag_simulator import ProductDiagSimulator
from app.tools.diag_tools import AccountTool, ProductDiagTool, CombinedDiagnosticsTool
from app.llm.mock_llm import Mockllm
import os

VALID_PAYLOAD = {
    "request_id": "req-int-1",
    "user_id": "user-int-1",
    "channel": "email",
    "message": "My payment failed and I lost access to premium features.",
    "metadata": {
        "product_version": "1.6.2",
        "region": "IN",
        "timestamp": "2025-12-02T16:12:00+05:30"
    }
}

HEALTHY_PAYLOAD = {
    "request_id": "req-int-2",
    "user_id": "user-int-2",
    "channel": "chat",
    "message": "Just saying hi, how are you?",
    "metadata": {
        "product_version": "2.0.0",
        "region": "IN",
        "timestamp": "2025-12-02T16:12:00+05:30"
    }
}

client = TestClient(app)

def test_trige_endpoint_returns_decision_and_expected_keys():
    r = client.post("/support/triage", json=VALID_PAYLOAD)
    assert r.status_code == 200, f"Request failed with {r.status_code}: {r.text}"
    data = r.json()

    assert "request_id" in data and data["request_id"] == VALID_PAYLOAD["request_id"]
    assert "triage" in data and "decision" in data and "diagnostics" in data
    decision = data["decision"]

    assert decision["recommended_action"]["type"] == "create_ticket"
    assert decision["severity"] == "high"

@patch('app.db.account_mongo.mongomock.MongoClient')
def test_trige_endpoint_healthy_suggests_runbook(mock_mongo_cls):
    # Create a shared mock client for this test
    shared_client = mongomock.MongoClient()
    mock_mongo_cls.return_value = shared_client

    # Seed the database using the shared client
    # The app will also use this shared client when it instantiates MongoAccountDB
    seed_db = MongoAccountDB()
    seed_db.upsert_account({
        "user_id": HEALTHY_PAYLOAD["user_id"],
        "subscription": "active",
        "last_payment_attempt": "2025-12-10",
        "metadata": {}
    })
    
    # Run the request
    r = client.post("/support/triage", json=HEALTHY_PAYLOAD)

    assert r.status_code == 200
    data = r.json()
    decision = data["decision"]
    # Healthy product -> low severity suggestion
    assert decision["severity"] in ("low", "medium")
    assert "suggest_runbook" in decision["recommended_action"]["type"]