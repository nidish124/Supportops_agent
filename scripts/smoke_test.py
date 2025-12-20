from httpx._api import request
import sys
import json
import requests
from typing import Dict
import os

TIMEOUT = 10

def fail(msg: str):
    print(f"[Smoke Test failed] {msg}")
    sys.exit(1)

def ok(msg: str):
    print(f"[Smoke Test Passed] {msg}")

def check_health(base_url: str):
    r = requests.get(f"{base_url}/health", timeout=TIMEOUT)
    if r.status_code != 200:
        fail(f"/health returned {r.status_code}")
    ok(f"health ok")

def check_ready(base_url: str):
    r = requests.get(f"{base_url}/ready", timeout=TIMEOUT)
    if r.status_code != 200:
        fail(f"/ready returned {r.status_code}: {r.message}")
    ok(f"ready ok")

def check_triage(base_url: str):
    payload: Dict = {
        "request_id": "smoke-test",
        "user_id": "system",
        "channel": "internal",
        "message": "smoke test",
        "metadata": {}
    }

    r = requests.post(f"{base_url}/support/triage",
        json=payload,
        timeout=TIMEOUT)

    if r.status_code != 200:
        fail(f"/support/triage returned {r.status_code}: {r.message}")

    data = r.json()

    required_paths = [
        ("request_id",),
        ("triage", "intent"),
        ("decision", "recommended_action", "type")
    ]

    for path in required_paths:
        cur = data
        for key in path:
            if key not in cur:
                fail(f"Missing field: {'.'.join(path)}")
            cur = cur[key]

    ok("/support/triage schema OK")

def main():
    base_url = None

    if len(sys.argv) == 2:
        base_url = sys.argv[1]
    else:
        base_url = os.getenv("SMOKE_TEST_URL")

    if not base_url:
        print("Usage: python smoke_test.py <BASE_URL>")
        print("or set SMOKE_TEST_URL env var")
        sys.exit(1)

    base_url = base_url.rstrip("/")

    print(f"[SMOKE TEST] Target: {base_url}")

    check_health(base_url)
    check_ready(base_url)
    check_triage(base_url)

    print("[SMOKE TEST 🎉] ALL CHECKS PASSED")

    sys.exit(0)

if __name__ == "__main__":
    main()