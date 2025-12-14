"""
GitHubTicketTool - creates GitHub issues via PyGithub.

Usage:
    tool = GitHubTicketTool(token=os.getenv("GITHUB_TOKEN"), repo_full_name="yourorg/support-ops-demo")
    resp = tool.create_issue(title, body, labels=["billing"])
Notes:
- Use a throwaway repo and a scoped token with repo:issues (or repo scope for private repos).
- This module will raise exceptions on HTTP/network errors; the executor handles audit updates accordingly.
"""

from typing import List, Dict, Any, Optional
import os

from github import Github, GithubException


class GitHubTicketTool:
    def __init__(self, token: Optional[str] = None, repo_full_name: Optional[str] = None):
        """
        token: GitHub token with 'repo' or 'public_repo' / 'repo:issues' scopes.
        repo_full_name: "owner/repo"
        """
        self.token = token or os.getenv("GITHUB_TOKEN")

        self.repo_full_name = repo_full_name or os.getenv("GITHUB_REPO")

        if not self.token:
            raise ValueError("Github Tocken not provided. Set GITHUB_TOKEN env or pass token.")
        if not repo_full_name:
            raise ValueError("repo_full_name must be provided (owner/repo).")

        self.client = Github(self.token)
        self.repo = self.client.get_repo(repo_full_name)

    def create_issue(self, title: str, body: str, lables: List[str] = None) -> Dict[str, Any]:
        lables = lables or []
        try:
            gh_lables = [self.repo.create_issue(l, "ffffff") if not self._label_exists(l) else self.repo.get_label(l) for l in lables]
        except GithubException:
            gh_labels = lables

        try:
            issue = self.repo.create_issue(title = title, body= body, labels=lables)
            return {"ticket_id": str(issue.number), "ticket_url": issue.html_url, "title": title, "labels": lables}
        except GithubException as exc:
            raise RuntimeError(f"GitHub API error: {exc.data if hasattr(exc, 'data') else str(exc)}")

    def _label_exists(self, label_name: str) -> bool:
        try:
            self.repo.get_label(label_name)
            return True
        except GithubException:
            return False            
