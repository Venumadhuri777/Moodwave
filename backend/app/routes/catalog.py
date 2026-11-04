from fastapi import APIRouter, HTTPException, Request
from app.schemas import CatalogItemResponse

router = APIRouter(prefix="/v1", tags=["Catalog"])

@router.get("/catalog/{track_id}", response_model=CatalogItemResponse)
async def get_catalog_track(request: Request, track_id: str):
    catalog_store = request.app.state.catalog_store

    if not catalog_store or not catalog_store.data_loaded:
        missing = catalog_store.missing_files if catalog_store else ["all"]
        raise HTTPException(
            status_code=503,
            detail=f"Catalog data is not loaded. Missing files: {', '.join(missing)}",
        )

    track = catalog_store.get_track(track_id)
    if not track:
        raise HTTPException(
            status_code=404,
            detail=f"Track not found: {track_id}",
        )

    return CatalogItemResponse(**track)
