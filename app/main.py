from fastapi import FastAPI,Query ,HTTPException, Response, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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



# @app.get("/")
# def read_root():
#     return Response(status_code=302, headers={"Location": "/docs"})

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

# Mount the static files directory
# We assume 'frontend/dist' exists (it will in the Docker container)
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))

if os.path.exists(static_dir):
    # Serve assets (js, css, images) directly
    # Vite usually puts them in /assets, but we mount the root dist for things like favicon.ico
    app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve the frontend index.html for any unmatched route (SPA pattern)."""
        # If it's an API route (starts with /support, /health, /ready, /docs, /openapi.json), 
        # let FastAPI handle it (though they are defined above, so this runs last).
        # We explicitly skip known API prefixes just in case, though route ordering usually handles it.
        if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("openapi.json"):
            raise HTTPException(status_code=404, detail="Not found")

        # Check if the file actually exists (e.g. favicon.ico)
        file_path = os.path.join(static_dir, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
             return FileResponse(file_path)
        
        # Otherwise return index.html
        return FileResponse(os.path.join(static_dir, "index.html"))
else:
    logger.warning(f"Frontend dist directory not found at {static_dir}. Frontend will not be served.")

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