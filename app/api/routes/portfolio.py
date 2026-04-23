from fastapi import APIRouter

from app.schemas.portfolio import (
    PortfolioHistoryRequest,
    PortfolioHistoryResponse,
    PortfolioRealtimeRequest,
    PortfolioRealtimeResponse,
)
from app.services.portfolio_service import portfolio_service

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.post("/history", response_model=PortfolioHistoryResponse)
def get_portfolio_history(
    payload: PortfolioHistoryRequest,
) -> PortfolioHistoryResponse:
    return portfolio_service.build_history(payload)


@router.post("/realtime", response_model=PortfolioRealtimeResponse)
def get_portfolio_realtime(
    payload: PortfolioRealtimeRequest,
) -> PortfolioRealtimeResponse:
    return portfolio_service.build_realtime(payload)
