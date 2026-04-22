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

