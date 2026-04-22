from app.core.config import get_settings
from app.providers.eastmoney import eastmoney_provider
from app.schemas.fund import (
    FundHistoryPoint,
    FundHistoryResponse,
    FundRealtimeData,
    FundRealtimeResponse,
    FundSearchItem,
    FundSearchResponse,
)


class FundService:
    def __init__(self) -> None:
        self._source = get_settings().default_data_source

    def search(self, keyword: str) -> FundSearchResponse:
        items = [
            FundSearchItem(
                code=item.code,
                name=item.name,
                fund_type=item.fund_type,
            )
            for item in eastmoney_provider.search_funds(keyword=keyword)
        ]
        return FundSearchResponse(keyword=keyword, source="eastmoney", items=items)

    def get_realtime(self, code: str) -> FundRealtimeResponse:
        realtime = eastmoney_provider.fetch_fund_realtime(code=code)
        return FundRealtimeResponse(
            data=FundRealtimeData(
                code=realtime.code,
                name=realtime.name,
                fund_type=realtime.fund_type,
                nav=realtime.nav,
                nav_date=realtime.nav_date,
                change_percent=realtime.change_percent,
                value_kind=realtime.value_kind,
                source="eastmoney",
            )
        )

    def get_history(
        self,
        code: str,
        start_date: str | None,
        end_date: str | None,
    ) -> FundHistoryResponse:
        history = eastmoney_provider.fetch_fund_history(
            code=code,
            start_date=start_date,
            end_date=end_date,
        )
        points = [
            FundHistoryPoint(
                date=point.date,
                unit_nav=point.unit_nav,
                accumulated_nav=point.accumulated_nav,
            )
            for point in history.points
        ]
        return FundHistoryResponse(
            fund_code=history.code,
            fund_name=history.name,
            fund_type=history.fund_type,
            source="eastmoney",
            start_date=start_date,
            end_date=end_date,
            points=points,
        )


fund_service = FundService()
