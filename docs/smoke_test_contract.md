# Smoke Test Contract — SupportOps Agent

A deployment is considered HEALTHY if:

1. /health endpoint returns HTTP 200
2. LangGraph flow initializes without error
3. A minimal triage request completes without side-effects
4. Response schema contains:
   - request_id
   - triage.intent
   - decision.recommended_action.type
5. No external APIs are called
6. No secrets are required
