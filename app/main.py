from fastapi import FastAPI,Query ,HTTPException, Response, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import logging 
from app.schemas import triageRequest

app = FastAPI(title="supportops agent", version="0.1.0")

logger = logging.getLogger("supportops")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

@app.get("/health")
def health():
    """Basic healthcheck used in CI / smoke tests """
    return {"status": "ok"}

@app.post("/support/triage")
def triage(payload: triageRequest):
    """Triage the user message and return the appropriate action"""
    logger.info(f"Triage request received for request_id: {payload.request_id}")

    ##TODO: Implement the triage logic using langchain integration

    return JSONResponse(status_code=501, content={"message": "Not Implemented"})


