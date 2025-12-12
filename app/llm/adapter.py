"""
LLM Adapter: small abstraction so you can later plug LangChain LLMs.

Example usage:
    from app.llm.adapter import LangChainLLM
    llm = LangChainLLM(openai_key=os.getenv("OPENAI_API_KEY"))

This adapter implements .predict(prompt: str) -> str to match MockLLM in tests.
"""

import os
from typing import Optional

class MockLLMAdapter:
    def __init__(self, mock_impl):
        self.mock_impl = mock_impl

    def predict(self, prompt: str) -> str:
        return self.mock_impl.predict(prompt)

class LangchainLLM:
    def __init__(self, llm_client=None):
        self.llm = llm_client

    def predict(self, prompt: str) -> str:
        resp = self.llm(predict) if callable(self.llm) else self.llm.generate(prompt)
        if isinstance(resp, str):
            return resp
        return str(resp)
        