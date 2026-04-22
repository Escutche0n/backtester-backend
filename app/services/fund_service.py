from app.core.config import get_settings
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
        sample_items = [
            FundSearchItem(code="161725", name="招商中证白酒指数", fund_type="index"),
            FundSearchItem(code="163406", name="兴全合润混合", fund_type="mixed"),
            FundSearchItem(code="110022", name="易方达消费行业股票", fund_type="equity"),
        ]
        items = [
            item
            for item in sample_items
            if keyword in item.code or keyword.lower() in item.name.lower()
        ]
        return FundSearchResponse(keyword=keyword, source=self._source, items=items)

    def get_realtime(self, code: str) -> FundRealtimeResponse:
        return FundRealtimeResponse(
            data=FundRealtimeData(
                code=code,
                name="Mock Fund",
                nav=1.2345,
                nav_date="2026-04-22",
                change_percent=0.82,
                source=self._source,
            )
        )

    def get_history(
        self,
        code: str,
        start_date: str | None,
        end_date: str | None,
    ) -> FundHistoryResponse:
        points = [
            FundHistoryPoint(date="2026-04-18", nav=1.2100, accumulated_nav=2.5100),
            FundHistoryPoint(date="2026-04-19", nav=1.2180, accumulated_nav=2.5180),
            FundHistoryPoint(date="2026-04-20", nav=1.2250, accumulated_nav=2.5250),
            FundHistoryPoint(date="2026-04-21", nav=1.2280, accumulated_nav=2.5280),
            FundHistoryPoint(date="2026-04-22", nav=1.2345, accumulated_nav=2.5345),
        ]
        return FundHistoryResponse(
            code=code,
            source=self._source,
            start_date=start_date,
            end_date=end_date,
            points=points,
        )


fund_service = FundService()

