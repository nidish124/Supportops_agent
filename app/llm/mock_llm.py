"""Mock LLM for testing
This imitates the minimal behaviour we need from an LLM for triage.
- PromptTemplate.format(**Kwargs) -> str
- MockLLM.invoke(prompt) -> str
The mock return predictable JSON-like strings based on keywords so tests are deterministics.
"""

import json
from typing import Dict

class PromptTemplate:

    def __init__(self, template:str):
        self.template = template

    def format(self, **kwargs) -> str:
        return self.template.format(**kwargs)

class Mockllm:
    def __init__(self):
        pass

    def predict(self, prompt:str) -> str:
        # Extract the actual customer message from the prompt
        # Prompt format: ... Customer message: "{text}" ...
        import re
        match = re.search(r'Customer message: "(.*?)"', prompt, re.DOTALL)
        if match:
            text_to_analyze = match.group(1).lower()
        else:
            # Fallback if format doesn't match, though this shouldn't happen with our current templates
            text_to_analyze = prompt.lower()

        p = text_to_analyze

        # Rule: Payment/billing keywords -> billing_access
        if "payment" in p or "billing" in p or "credit card" in p or "refund" in p:
            resp = {
                "intent": "billing_issue",
                "severity": "high",
                "confidence": 0.95,
                "explanation": "Contains keywords related to payment or billing."
            }

            return json.dumps(resp)

        # Rule: password / login -> account_access
        if "password" in p or "login" in p or "sign in" in p or "can't access" in p:
            resp = {
                "intent": "account_access",
                "severity": "medium",
                "confidence": 0.9,
                "explanation": "Mentions access/login problems."
            }
            return json.dumps(resp)

        # Rule: feature or bug keywords -> product_issue
        if "bug" in p or "feature" in p or "not working" in p or "error" in p:
            resp = {
                "intent": "product_issue",
                "severity": "medium",
                "confidence": 0.85,
                "explanation": "Mentions errors or non-working features."
            }
            return json.dumps(resp)

        # Default fallback: general_query
        resp = {
            "intent": "general_query",
            "severity": "low",
            "confidence": 0.6,
            "explanation": "Default fallback."
        }
        return json.dumps(resp)