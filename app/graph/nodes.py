"""
ParseInputNode and IntentClassifierNode.

- ParseInputNode: validate and normalize incoming dict into TriageRequest using pydantic model
- IntentClassifierNode: given parsed input, build a prompt (via PromptTemplate) and call Mockllm.predict to get structured JSON.

"""

from typing import Dict, Any
from pydantic import ValidationError
from app.schemas import triageRequest
from app.llm.mock_llm import PromptTemplate, Mockllm
import json


class ParseInputNode:
    """
    Validate input payload and return pydantic model dict.
    """
    def __init__(self):
        pass

    def parse(self, payload: Dict[str, Any]) -> triageRequest:
        model = triageRequest(**payload)
        return model

class IntentClassifierNode:
    """
    Build a prompt using a PromptTemplate and call an LLM (mocked) to return structured intent JSON.
    """

    def __init__(self, llm =  None, template: str = None):
        self.llm = llm or Mockllm()
        self.template = PromptTemplate(template or 
        "You are a support triage assistant. "
        "Return a JSON object with keys: intent, severity, confidence, explanation, issues.\n\n"
        "Customer message: \"{text}\"\n"
        "Account metadata: {metadata}\n\n"
        "Rules: If message mentions payment/billing terms, intent=billing_issue, issues= Yes/No.")


    def classify(self, triage_request: triageRequest) -> Dict[str, Any]:
        metadata_var = triage_request.metadata.model_dump(mode='json') if triage_request.metadata else {}
        prompt = self.template.format(text = triage_request.message, metadata = json.dumps(metadata_var))

        raw = self.llm.predict(prompt)
        try:
            parsed = json.loads(raw)
        except Exception as e:
            print(f"Error decoding JSON: {e}")
            parsed = {"intent": "general_query", "severity": "low", "confidence": 0.0, "explanation": "llm_parse_error", "issues": "No"}
        intent = parsed.get("intent", "general_query")
        severity = parsed.get("severity", "low")
        confidence = float(parsed.get("confidence", 0.0))
        explanation = parsed.get("explanation", "")
        issues = parsed.get("issues", "")
        return {
            "intent": intent,
            "severity": severity,
            "confidence": confidence,
            "explanation": explanation,
            "issues": issues
        }