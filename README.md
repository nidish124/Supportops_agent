# Supportops_agent

An agent that reads user messages, triages them, runs diagnostics (API calls to the product + account DB), suggests fixes or creates/upserts tickets Issues, and executes safe actions (e.g., reset config) via authenticated API calls.


# Task 1 (skeleton)

This repo contains the minimal skeleton for the SupportOps Agent demo service.

## What this task provides

- FastAPI app with `/health` and placeholder `/support/triage`
- Pydantic schemas for triage request
- Basic unit test for health endpoint
- Dockerfile for containerization

## Quick local run

1. Create venv and install:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
