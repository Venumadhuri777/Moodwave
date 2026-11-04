from fastapi import APIRouter, HTTPException, Request, status
from app.schemas import FeedbackRequest, FeedbackResponse

router = APIRouter(prefix="/v1", tags=["Feedback"])

@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def post_feedback(request: Request, body: FeedbackRequest):
    feedback_store = request.app.state.feedback_store

    if not feedback_store or not feedback_store.is_ok:
        raise HTTPException(
            status_code=503,
            detail="Feedback database is currently unavailable",
        )

    try:
        # 1. Feedback row is written first
        record = feedback_store.record_feedback(
            user_id=body.user_id,
            track_id=body.track_id,
            action=body.action,
        )

        # 2. Update user vector in feedback_model if available
        feedback_model = getattr(request.app.state, "feedback_model", None)
        catalog_index = getattr(request.app.state, "catalog_index", None)
        if feedback_model and catalog_index and catalog_index.is_loaded:
            track_emb = catalog_index.get_embedding(body.track_id)
            if track_emb is not None:
                feedback_model.update_user_vector(
                    user_id=body.user_id,
                    track_embedding=track_emb,
                    action=body.action,
                )

        return FeedbackResponse(**record)
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
