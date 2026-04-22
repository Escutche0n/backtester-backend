from fastapi import APIRouter, Query

from app.schemas.fund import FundHistoryResponse, FundRealtimeResponse, FundSearchResponse
from app.services.fund_service import fund_service

router = APIRouter(prefix="/fund", tags=["fund"])


@router.get("/search", response_model=FundSearchResponse)
def search_fund(
    keyword: str = Query(..., min_length=1, description="Fund code or keyword"),
) -> FundSearchResponse:
    return fund_service.search(keyword=keyword)


@router.get("/realtime", response_model=FundRealtimeResponse)
def get_fund_realtime(
    code: str = Query(..., min_length=1, description="Fund code"),
) -> FundRealtimeResponse:
    return fund_service.get_realtime(code=code)


@router.get("/history", response_model=FundHistoryResponse)
def get_fund_history(
    code: str = Query(..., min_length=1, description="Fund code"),
    start_date: str | None = Query(default=None, description="YYYY-MM-DD"),
    end_date: str | None = Query(default=None, description="YYYY-MM-DD"),
) -> FundHistoryResponse:
    return fund_service.get_history(code=code, start_date=start_date, end_date=end_date)

