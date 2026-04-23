from app.providers.eastmoney import eastmoney_provider
from app.schemas.portfolio import (
    PortfolioHistoryPoint,
    PortfolioHistoryRequest,
    PortfolioHistoryResponse,
    PortfolioRealtimeItem,
    PortfolioRealtimeRequest,
    PortfolioRealtimeResponse,
    PortfolioRealtimeSummary,
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

    def build_realtime(self, payload: PortfolioRealtimeRequest) -> PortfolioRealtimeResponse:
        items: list[PortfolioRealtimeItem] = []

        for holding in payload.holdings:
            realtime = eastmoney_provider.fetch_fund_realtime(holding.fund_code)
            latest = eastmoney_provider.fetch_latest_fund_history_point(realtime.code)

            base_value = holding.shares * latest.unit_nav
            estimated_value = holding.shares * realtime.nav
            estimated_profit = estimated_value - base_value
            estimated_return = estimated_profit / base_value if base_value else 0

            items.append(
                PortfolioRealtimeItem(
                    fund_code=realtime.code,
                    fund_name=realtime.name,
                    fund_type=realtime.fund_type,
                    shares=holding.shares,
                    base_date=latest.date,
                    base_nav=round(latest.unit_nav, 6),
                    estimated_time=realtime.nav_date,
                    estimated_nav=round(realtime.nav, 6),
                    value_kind=realtime.value_kind,
                    base_value=round(base_value, 2),
                    estimated_value=round(estimated_value, 2),
                    estimated_profit=round(estimated_profit, 2),
                    estimated_return=round(estimated_return, 6),
                )
            )

        base_value_total = sum(item.base_value for item in items)
        estimated_value_total = sum(item.estimated_value for item in items)
        estimated_profit_total = estimated_value_total - base_value_total
        estimated_return_total = (
            estimated_profit_total / base_value_total
            if base_value_total
            else 0
        )

        return PortfolioRealtimeResponse(
            summary=PortfolioRealtimeSummary(
                base_value=round(base_value_total, 2),
                estimated_value=round(estimated_value_total, 2),
                estimated_profit=round(estimated_profit_total, 2),
                estimated_return=round(estimated_return_total, 6),
            ),
            items=items,
            disclaimer="估算结果仅供个人记录，不代表确认净值或投资建议。",
        )


portfolio_service = PortfolioService()
