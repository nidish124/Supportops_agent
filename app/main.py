from fastapi import FastAPI,Query ,HTTPException, Response, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import logging 
from app.schemas import triageRequest
from app.graph.flow import TriageFlow

app = FastAPI(title="supportops agent", version="0.1.0")

logger = logging.getLogger("supportops")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

@app.get("/health")
def health():
    """Basic healthcheck used in CI / smoke tests """
    return {"status": "ok"}

@app.post("/support/triage")
def triage(payload: triageRequest):
    """Full triage flow:
      1. Validate payload (pydantic)
      2. Run Parse -> Classify -> Diagnostics -> Decision
      3. Return structured JSON
    This uses in-memory DB for demo."""
    logger.info(f"Triage request received for request_id: {payload.request_id}")

    try:
        payload_dict = payload.model_dump()
        flow  = TriageFlow()
        result = flow.run(payload_dict)
        flow.close()
        logger.info("Triage completed: request_id=%s user_id=%s decision=%s", result.get("request_id"), result.get("user_id"), result.get("decision", {}).get("recommended_action", {}).get("type"))
        return JSONResponse(status_code=200, content=result)
        
    except Exception as e:
        logger.exception("Error in triage flow")
        return JSONResponse(status_code=500, content = str(e))