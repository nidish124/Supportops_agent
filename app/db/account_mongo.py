import os
from typing import Dict, Any, Optional
from pymongo import MongoClient
import mongomock
from dotenv import load_dotenv

load_dotenv()
import certifi

class MongoAccountDB:
    def __init__(self, uri: Optional[str]=None, db_name: Optional[str]=None, client: Optional[Any] = None):
        self.uri = uri or os.getenv("MONGO_URI")
        self.db_name = db_name or os.getenv("MONGO_DB", "SupportOPS")

        if self.uri:
            client = MongoClient(self.uri)
        else:
            client = mongomock.MongoClient()

        self.db = client[self.db_name]
        self.collection = self.db["accounts"]

    def get_account(self, user_id:str) -> Optional[Dict[str,Any]]:
        return self.collection.find_one({"user_id": user_id}, {"_id": 0})

    def upsert_account(self, account: Dict[str, Any]):
        self.collection.update_one(
            {"user_id": account["user_id"]},
            {"$set": account},
            upsert=True
        )
        
    def close(self):
        pass