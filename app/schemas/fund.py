from pydantic import BaseModel, Field


class FundSearchItem(BaseModel):
    code: str
    name: str
    fund_type: str
    currency: str = "CNY"


class FundSearchResponse(BaseModel):
    keyword: str
    source: str
    items: list[FundSearchItem]


class FundRealtimeData(BaseModel):
    code: str
    name: str
    fund_type: str
    nav: float = Field(description="Latest known net asset value")
    nav_date: str
    change_percent: float | None = None
    value_kind: str
    source: str


class FundRealtimeResponse(BaseModel):
    data: FundRealtimeData


class FundHistoryPoint(BaseModel):
    date: str
    unit_nav: float
    accumulated_nav: float


class FundHistoryResponse(BaseModel):
    fund_code: str
    fund_name: str
    fund_type: str
    source: str
    start_date: str | None = None
    end_date: str | None = None
    points: list[FundHistoryPoint]
