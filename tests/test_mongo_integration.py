from app.db.account_mongo import MongoAccountDB
from app.db.audit_mongo import MongoAuditDB

def test_mongo_account_and_audit_integration():
    acc = MongoAccountDB()
    audit = MongoAuditDB()

    acc.upsert_account({"user_id": "u1", "subscription": "active", "metadata": {}})
    doc = acc.get_account("u1")
    assert doc["user_id"] == "u1"

    audit_doc = audit.create_audit("req1", "u1", "create_ticket", {}, "sys", "pending", "tok123")
    assert "id" in audit_doc

    fetched = audit.get_audit(audit_doc["id"])
    assert fetched["status"] == "pending"
