"""
TicketTool - deterministic mock for ticketing system (GitHub/Zendesk-like).

Methods:
 - Create_ticket(title: str, body: str, labels: list) -> dict
 Returns deterministic ticket dict: {"ticket_id": "<repo>-<seq>", "ticket_url": "..."}
 This sequence is stable per process using an incrementing counter stored in the tool instance.
"""

from typing import List, Dict

class Tickettool:
    def __init__(self, repo: str = "support_agent"):
        self.repo = repo
        self._counter = 100

    def create_ticket(self,  title: str, body: str,lables: List[str] = None) -> Dict[str, str]:
        lables = lables or []
        self._counter += 1
        ticket_id = f"{self.repo}-{self._counter}"
        ticket_url = f"https://example.com/{self.repo}/issues/{self._counter}"
        return {"ticket_id": ticket_id, "ticket_url": ticket_url, "title": title, "labels": lables, "body": body}

    def create_issue(self, title: str, body: str, lables: List[str] = None) -> Dict[str, str]:
        return self.create_ticket(title, body, lables)
