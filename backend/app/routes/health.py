from fastapi import APIRouter, Request
from app.config import settings
from app.schemas import HealthResponse

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=HealthResponse)
async def get_health(request: Request):
    catalog_store = request.app.state.catalog_store
    feedback_store = request.app.state.feedback_store

    data_loaded = catalog_store.data_loaded if catalog_store else False
    feedback_ok = feedback_store.is_ok if feedback_store else False
    llm_configured = bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip())
    catalog_size = len(catalog_store.tracks) if catalog_store else 0

    return HealthResponse(
        status="ok",
        data_loaded=data_loaded,
        feedback_db_ok=feedback_ok,
        llm_configured=llm_configured,
        catalog_size=catalog_size,
    )
