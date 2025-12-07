"""
Script to seed the SQLite database with 100 diverse account scenarios.
"""
from app.db.account_db import AccountDB
import random
from datetime import datetime, timedelta

def seed():
    db = AccountDB("accounts.db")
    print("Seeding accounts.db with 100 scenarios...")

    # Scenario types
    scenarios = []

    # 1. Healthy Pro Users (40%)
    for i in range(40):
        scenarios.append({
            "user_id": f"user-pro-{i}",
            "subscription": "active",
            "last_payment_attempt": (datetime.now() - timedelta(days=random.randint(1, 20))).isoformat(),
            "metadata": {"plan": "pro", "region": random.choice(["US", "EU", "IN"])}
        })

    # 2. Healthy Starter Users (30%)
    for i in range(30):
        scenarios.append({
            "user_id": f"user-starter-{i}",
            "subscription": "active",
            "last_payment_attempt": (datetime.now() - timedelta(days=random.randint(1, 20))).isoformat(),
            "metadata": {"plan": "starter", "region": random.choice(["US", "EU", "IN"])}
        })

    # 3. Payment Failed Users (15%)
    for i in range(15):
        scenarios.append({
            "user_id": f"user-failed-{i}",
            "subscription": "past_due",
            "last_payment_attempt": (datetime.now() - timedelta(hours=random.randint(1, 48))).isoformat(),
            "metadata": {"plan": "pro", "last_failure_reason": "insufficient_funds"}
        })

    # 4. Cancelled/Expired Users (10%)
    for i in range(10):
        scenarios.append({
            "user_id": f"user-cancelled-{i}",
            "subscription": "cancelled",
            "last_payment_attempt": (datetime.now() - timedelta(days=random.randint(40, 100))).isoformat(),
            "metadata": {"plan": "starter"}
        })

    # 5. New Users / No Subscription (5%)
    for i in range(5):
        scenarios.append({
            "user_id": f"user-new-{i}",
            "subscription": None,
            "last_payment_attempt": None,
            "metadata": {"source": "signup_page"}
        })

    # Specific Scenario for Integration Tests
    scenarios.append({
        "user_id": "user-int-1",
        "subscription": "active", 
        "last_payment_attempt": "2025-12-01T12:00:00",
        "metadata": {"plan": "pro"}
    })
    scenarios.append({
        "user_id": "user-int-2",
        "subscription": "active",
        "last_payment_attempt": "2025-12-01T12:00:00",
        "metadata": {"plan": "starter"}
    })

    for acc in scenarios:
        db.upsert_account(acc)

    print(f"Seeded {len(scenarios)} accounts.")
    db.close()

if __name__ == "__main__":
    seed()
