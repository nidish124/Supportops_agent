from calendar import c
import pytest
from app.graph.nodes import ParseInputNode, IntentClassifierNode
from app.llm.mock_llm import Mockllm
from datetime import datetime

VALID_PAYLOAD = {
    "request_id": "req-123",
    "user_id": "user-1",
    "channel": "email",
    "message": "My payment failed and I lost access to premium features.",
    "metadata": {
        "product_version": "1.0.0",
        "region": "IN"
    }
}

INVALID_PAYLOAD = {
    # missing user_id, request_id
    "channel": "chat",
    "text": "hello"
}

def test_parse_input_valid():
    node = ParseInputNode()
    parsed = node.parse(VALID_PAYLOAD)
    assert parsed.request_id == "req-123"
    assert parsed.user_id == "user-1"
    assert parsed.channel == "email"
    assert parsed.metadata.product_version == "1.0.0"


def test_parse_input_invalid_raises():
    node = ParseInputNode()
    with pytest.raises(Exception):
        node.parse(INVALID_PAYLOAD)


def test_intent_classifier_billing_keyword():
    node = ParseInputNode()
    parsed = node.parse(VALID_PAYLOAD)

    classifynode = IntentClassifierNode(llm = Mockllm())
    classify_var = classifynode.classify(parsed)

    assert classify_var["intent"] == "billing_issue"
    assert classify_var["severity"] == "high"
    assert classify_var["confidence"] >= 0.95
    assert "payment" in classify_var["explanation"].lower()


def test_intent_classifier_default():
    node = ParseInputNode()
    
    payload = VALID_PAYLOAD.copy()
    payload["message"] = "Just saying hi, How are you?."
    parsed = node.parse(payload)
    classifynode = IntentClassifierNode(llm = Mockllm())
    classify_var = classifynode.classify(parsed)
    print(parsed)
    print(classify_var)
    assert classify_var["intent"] == "general_query"
    assert classify_var["severity"] == "low"



