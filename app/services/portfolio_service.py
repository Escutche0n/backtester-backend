from app.schemas.portfolio import (
    PortfolioHistoryPoint,
    PortfolioHistoryRequest,
    PortfolioHistoryResponse,
)


class PortfolioService:
    def build_history(self, payload: PortfolioHistoryRequest) -> PortfolioHistoryResponse:
        # Placeholder output. The next step is replacing this with fund-history aggregation.
        points = [
            PortfolioHistoryPoint(date="2026-04-18", portfolio_nav=1.0000, daily_return=0.0000),
            PortfolioHistoryPoint(date="2026-04-19", portfolio_nav=1.0040, daily_return=0.0040),
            PortfolioHistoryPoint(date="2026-04-20", portfolio_nav=1.0115, daily_return=0.0075),
            PortfolioHistoryPoint(date="2026-04-21", portfolio_nav=1.0090, daily_return=-0.0025),
            PortfolioHistoryPoint(date="2026-04-22", portfolio_nav=1.0168, daily_return=0.0077),
        ]
        return PortfolioHistoryResponse(
            start_date=payload.start_date,
            end_date=payload.end_date,
            rebalance=payload.rebalance,
            points=points,
            warnings=["mock implementation: portfolio history is not using real fund data yet"],
        )


portfolio_service = PortfolioService()
