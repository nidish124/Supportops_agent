import os
from typing import Dict, Any, Optional
from pymongo import MongoClient
from bson.objectid import ObjectId
import mongomock
from datetime import datetime, UTC
from dotenv import load_dotenv
import certifi


load_dotenv()
class MongoAuditDB:
    def __init__(self, uri: Optional[str] = None, db_name: Optional[str] = None):
        self.uri = uri or os.getenv("MONGO_URI")
        self.db_name = db_name or os.getenv("MONGO_DB", "supportops")

        if self.uri:
            client = MongoClient(self.uri, tlsCAFile=certifi.where())
        else:
            client = mongomock.MongoClient()

        self.db = client[self.db_name]
        self.collection = self.db["audit"]

    def create_audit(self, request_id: str, user_id: str, action_type: str, 
    action_payload: Dict[str, Any], executor_id: str, status: str, audit_token: str):
        doc = {
            "request_id":request_id,
            "user_id": user_id,
            "action_type": action_type,
            "action_payload":action_payload,
            "executor_id": executor_id,
            "status":status,
            "audit_token":audit_token,
            "created_at": datetime.now(UTC).isoformat()
        }
        result = self.collection.insert_one(doc)
        return {"id":str(result.inserted_id), **doc}

    def update_status(self, audit_id:Any, status: str, audit_token:Optional[str]= None):
        if isinstance(audit_id, str):
            audit_id = ObjectId(audit_id)
            
        if audit_token is None:
            self.collection.update_one({"_id":audit_id},{"$set": {"status": status}})
        else:
            self.collection.update_one({"_id":audit_id},{"$set": {"status": status,"audit_token": audit_token}})
    
    def get_audit(self, audit_id: Any)-> Optional[Dict[str, Any]]:
        if isinstance(audit_id, str):
            try:
                audit_id = ObjectId(audit_id)
            except Exception:
                return None

        doc = self.collection.find_one({"_id": audit_id})
        if not doc:
            return None
        doc["id"] = str(doc["_id"])

        del doc["_id"]
        return doc

    def close(self):
        pass