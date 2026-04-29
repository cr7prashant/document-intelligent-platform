import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api import validate, match, process
from app.core.logging_config import setup_logging

setup_logging()

app = FastAPI(title="Document Intelligence Platform", version="1.0.0")
log = logging.getLogger(__name__)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "doc-intelligence", "version": "1.0.0"}


@app.exception_handler(Exception)
async def catch_all(request: Request, exc: Exception):
    log.error("unhandled error on %s: %s", request.url.path, exc)
    return JSONResponse(status_code=500, content={"detail": "internal error"})


app.include_router(validate.router, tags=["validation"])
app.include_router(match.router, tags=["matching"])
app.include_router(process.router, tags=["pipeline"])
