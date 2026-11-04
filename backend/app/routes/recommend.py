from fastapi import APIRouter, HTTPException, Request
from app.schemas import RecommendItem, RecommendRequest, RecommendResponse
from app.services.rules_parser import rules_parser

router = APIRouter(prefix="/v1", tags=["Recommend"])

@router.post("/recommend", response_model=RecommendResponse)
async def post_recommend(request: Request, body: RecommendRequest):
    catalog_store = request.app.state.catalog_store
    request_id = getattr(request.state, "request_id", None)

    # Set query length for access logging in middleware
    request.state.query_length = len(body.query)

    if not catalog_store or not catalog_store.data_loaded:
        missing = catalog_store.missing_files if catalog_store else ["all"]
        raise HTTPException(
            status_code=503,
            detail=f"Catalog data is not loaded. Missing files: {', '.join(missing)}",
        )

    # Parse intent via rules parser (reliable offline fallback)
    intent = rules_parser.parse(body.query)

    recommender = getattr(request.app.state, "recommender", None)
    if recommender and recommender.index and recommender.index.is_loaded:
        items_raw, degraded, degraded_reason = recommender.recommend(
            query=body.query,
            user_id=body.user_id,
            mode=body.mode,
            intent=intent,
            limit=body.limit,
        )
        items = [RecommendItem(**it) for it in items_raw]
        return RecommendResponse(
            intent=intent,
            source="rules",
            items=items,
            degraded=degraded,
            degraded_reason=degraded_reason,
        )

    # Fallback to placeholder if index is unavailable
    raw_items = catalog_store.get_recommendations(query=body.query, limit=body.limit)
    items = [RecommendItem(**item) for item in raw_items]

    return RecommendResponse(
        intent=intent,
        source="rules",
        items=items,
        degraded=True,
        degraded_reason="placeholder_ranking",
    )
