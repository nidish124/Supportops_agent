from fastapi import FastAPI,Query ,HTTPException, Response, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import logging 
from app.schemas import triageRequest
from app.graph.langgraph_flow import LangGraphTriage
from app.logging_utils import configure_logging
from dotenv import load_dotenv
import os
import logging
from time import time

load_dotenv()
configure_logging()

logger = logging.getLogger("request")

app = FastAPI(title="supportops agent", version="0.1.0")

@app.get("/")
def read_root():
    return Response(status_code=302, headers={"Location": "/docs"})

logger = logging.getLogger("supportops")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

@app.get("/health")
def health():
    """Basic healthcheck used in CI / smoke tests """
    return {"status": "ok"}

@app.get("/ready")
def ready():
    """Ensures core system wiring works."""
    try:
        triage  = LangGraphTriage()
        payload = {
            "request_id": "ready-check",
            "user_id": "system",
            "channel": "internal",
            "message": "ready check",
            "metadata": {}
        }

        result = triage.invoke(payload)
        assert "decision" in result
        assert "recommended_action" in result["decision"]
        return {"status": "ready"}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Readiness check failed: {str(e)}"
        )

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
        flow  = LangGraphTriage()
        result = flow.invoke(payload_dict)
        flow.close()
        logger.info("Triage completed: request_id=%s user_id=%s decision=%s", result.get("request_id"), result.get("user_id"), result.get("decision", {}).get("recommended_action", {}).get("type"))
        return JSONResponse(status_code=200, content=result)
        
    except Exception as e:
        logger.exception("Error in triage flow")
        return JSONResponse(status_code=500, content = str(e))

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time()

    request_id = request.headers.get("X-Request-ID", "unknown")

    logger.info(
        "request_start",
        extra={
            "extra": {
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method,
            }
        },
    )
    try:
        response = await call_next(request)
        return response
    finally:
        duration = round((time() - start) * 1000, 2)
        logger.info(
            "request_end",
            extra={
                "extra": {
                    "request_id": request_id,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration,
                }
            },
        )