from pydantic import BaseModel, Field


class PortfolioHolding(BaseModel):
    fund_code: str = Field(min_length=1)
    weight: float = Field(gt=0, le=1)


class PortfolioHistoryRequest(BaseModel):
    holdings: list[PortfolioHolding] = Field(min_length=1)
    start_date: str | None = None
    end_date: str | None = None
    rebalance: str = "none"


class PortfolioHistoryPoint(BaseModel):
    date: str
    portfolio_nav: float
    daily_return: float


class PortfolioHistoryResponse(BaseModel):
    start_date: str | None = None
    end_date: str | None = None
    rebalance: str
    points: list[PortfolioHistoryPoint]
    warnings: list[str] = []


class PortfolioRealtimeHolding(BaseModel):
    fund_code: str = Field(min_length=1)
    shares: float = Field(gt=0)


class PortfolioRealtimeRequest(BaseModel):
    holdings: list[PortfolioRealtimeHolding] = Field(min_length=1)


class PortfolioRealtimeItem(BaseModel):
    fund_code: str
    fund_name: str
    fund_type: str
    shares: float
    base_date: str
    base_nav: float
    estimated_time: str
    estimated_nav: float
    value_kind: str
    base_value: float
    estimated_value: float
    estimated_profit: float
    estimated_return: float


class PortfolioRealtimeSummary(BaseModel):
    base_value: float
    estimated_value: float
    estimated_profit: float
    estimated_return: float


class PortfolioRealtimeResponse(BaseModel):
    summary: PortfolioRealtimeSummary
    items: list[PortfolioRealtimeItem]
    disclaimer: str
