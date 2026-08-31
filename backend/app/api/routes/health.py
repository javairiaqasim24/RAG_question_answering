import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import get_settings
from app.rag.embeddings import is_model_loaded
from app.rag.llm import get_llm_provider
from app.schemas.common import HealthResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:  # noqa: BLE001
        logger.exception("Database health check failed")
        db_status = "unavailable"

    llm_health = get_llm_provider().check_health()
    if llm_health.reachable and llm_health.model_available:
        llm_status = "ready"
    elif llm_health.reachable:
        llm_status = "model_not_found"
    else:
        llm_status = "unreachable"

    overall_status = "ok" if db_status == "ok" and llm_status == "ready" else "degraded"

    return HealthResponse(
        status=overall_status,
        database=db_status,
        embedding_model=settings.embedding_model,
        embedding_model_loaded=is_model_loaded(),
        llm_provider=settings.llm_provider,
        llm_model=settings.active_model,
        llm_configured=llm_status == "ready",
        llm_status=llm_status,
        llm_message=llm_health.error,
    )
