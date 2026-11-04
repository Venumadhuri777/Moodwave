import json
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.middleware import MoodwaveMiddleware
from app.routes import catalog, feedback, health, recommend
from app.services.catalog_store import CatalogStore
from app.services.feedback_store import FeedbackStore
from app.services.index import CatalogIndex
from app.services.feedback_model import FeedbackModel
from app.services.recommender import Recommender

logger = logging.getLogger("moodwave.main")

def init_app_state(target_app: FastAPI):
    if getattr(target_app.state, "_initialized", False):
        return

    logger.info("Initializing CatalogStore from %s", settings.DATA_DIR)
    catalog_store = CatalogStore(data_dir=settings.DATA_DIR)
    catalog_store.load_data()
    target_app.state.catalog_store = catalog_store

    logger.info("Initializing FeedbackStore at %s", settings.FEEDBACK_DB_PATH)
    feedback_store = FeedbackStore(db_path=settings.FEEDBACK_DB_PATH)
    feedback_store.init_db()
    target_app.state.feedback_store = feedback_store

    logger.info("Initializing CatalogIndex from %s", settings.DATA_DIR)
    catalog_index = CatalogIndex(data_dir=settings.DATA_DIR)
    catalog_index.load()
    target_app.state.catalog_index = catalog_index

    logger.info("Initializing FeedbackModel at %s", settings.FEEDBACK_DB_PATH)
    feedback_model = FeedbackModel(db_path=settings.FEEDBACK_DB_PATH)
    feedback_model.init_db()
    target_app.state.feedback_model = feedback_model

    recommender = Recommender(index=catalog_index, feedback_model=feedback_model)
    target_app.state.recommender = recommender
    target_app.state._initialized = True

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_app_state(app)
    yield
    logger.info("Shutting down Moodwave backend.")

app = FastAPI(
    title="Moodwave API",
    description="Spotify-style language-steerable music discovery API",
    version="1.0.0",
    lifespan=lifespan,
)

# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    req_id = getattr(request.state, "request_id", None)
    errors = exc.errors()
    # Check if this is a JSON decode failure
    is_json_invalid = any(e.get("type") == "json_invalid" for e in errors)
    if is_json_invalid:
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "BAD_REQUEST",
                    "message": "Malformed JSON in request body",
                    "request_id": req_id,
                }
            },
            headers={"X-Request-ID": req_id} if req_id else None,
        )

    first_err = errors[0] if errors else {}
    msg = first_err.get("msg", "Validation error")
    loc = " -> ".join(str(l) for l in first_err.get("loc", []))
    full_msg = f"{loc}: {msg}" if loc else msg
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": full_msg,
                "request_id": req_id,
            }
        },
        headers={"X-Request-ID": req_id} if req_id else None,
    )

@app.exception_handler(json.decoder.JSONDecodeError)
async def json_decode_exception_handler(request: Request, exc: json.decoder.JSONDecodeError):
    req_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "BAD_REQUEST",
                "message": f"Malformed JSON: {exc.msg}",
                "request_id": req_id,
            }
        },
        headers={"X-Request-ID": req_id} if req_id else None,
    )

@app.exception_handler(StarletteHTTPException)
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    req_id = getattr(request.state, "request_id", None)
    code_map = {
        400: "BAD_REQUEST",
        404: "NOT_FOUND",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMIT_EXCEEDED",
        503: "SERVICE_UNAVAILABLE",
    }
    code = code_map.get(exc.status_code, "HTTP_ERROR")
    headers = dict(exc.headers or {})
    if req_id and "X-Request-ID" not in headers:
        headers["X-Request-ID"] = req_id

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": code,
                "message": str(exc.detail),
                "request_id": req_id,
            }
        },
        headers=headers,
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    req_id = getattr(request.state, "request_id", None)
    logger.error("Unhandled server exception for request %s: %s", req_id, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Internal server error. Please try again later.",
                "request_id": req_id,
            }
        },
        headers={"X-Request-ID": req_id} if req_id else None,
    )

# Middlewares (MoodwaveMiddleware wraps app, then CORSMiddleware wraps outside)
app.add_middleware(MoodwaveMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(recommend.router)
app.include_router(feedback.router)
app.include_router(catalog.router)

# ── Serve the web-based presentation frontend ──────────────────
# The frontend lives at PROJECT_ROOT/frontend/
# Resolve path relative to this file: backend/app/main.py → ../../frontend
_project_root = Path(__file__).resolve().parent.parent.parent
_frontend_dir = Path(os.environ.get("FRONTEND_DIR", str(_project_root / "frontend")))

if _frontend_dir.is_dir():
    # Serve CSS/JS/assets under /static
    app.mount("/static", StaticFiles(directory=str(_frontend_dir)), name="static_frontend")

    # Serve index.html at the root URL
    @app.get("/", include_in_schema=False)
    async def serve_frontend():
        index_path = _frontend_dir / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path), media_type="text/html")
        return JSONResponse({"error": "Frontend index.html not found"}, status_code=404)
else:
    logger.warning("Frontend directory not found at %s — web UI will not be served.", _frontend_dir)
