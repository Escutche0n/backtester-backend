from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from html import unescape
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import HTTPException


@dataclass
class EastMoneyFundMeta:
    code: str
    name: str
    fund_type: str


@dataclass
class EastMoneyFundHistoryPoint:
    date: str
    unit_nav: float
    accumulated_nav: float


@dataclass
class EastMoneyFundHistory:
    code: str
    name: str
    fund_type: str
    points: list[EastMoneyFundHistoryPoint]


@dataclass
class EastMoneyFundRealtime:
    code: str
    name: str
    fund_type: str
    nav: float
    nav_date: str
    change_percent: float | None
    value_kind: str


class EastMoneyProvider:
    search_endpoint = "https://fundsuggest.eastmoney.com/FundSearch/api/FundSearchAPI.ashx"
    history_endpoint = "https://fundf10.eastmoney.com/F10DataApi.aspx"
    realtime_endpoint = "https://fundgz.1234567.com.cn/js"

    def search_funds(self, keyword: str, limit: int = 20) -> list[EastMoneyFundMeta]:
        normalized_keyword = keyword.strip()
        if not normalized_keyword:
            return []

        payload = self._get_json(
            self.search_endpoint,
            {"m": "1", "key": normalized_keyword},
            {"Referer": "https://fund.eastmoney.com/"},
        )
        items = payload.get("Datas") or []
        results: list[EastMoneyFundMeta] = []
        seen: set[str] = set()
        for item in items:
            if not self._looks_like_fund_item(item):
                continue
            code = self._normalize_code(item.get("CODE") or item.get("FCODE") or "")
            if not code:
                continue
            if code in seen:
                continue

            base = item.get("FundBaseInfo") or {}
            name = self._pick_first(
                base.get("SHORTNAME"),
                base.get("ShortName"),
                item.get("NAME"),
                item.get("Name"),
                base.get("FCODE"),
                code,
            )
            fund_type = self._pick_first(
                base.get("fundTypeDescription"),
                base.get("FundTypeDescription"),
                base.get("FTYPE"),
                item.get("categoryDescription"),
                item.get("CATEGORYDESC"),
                "基金",
            )
            results.append(EastMoneyFundMeta(code=code, name=name, fund_type=fund_type))
            seen.add(code)
            if len(results) >= limit:
                break

        return results

    def search_fund(self, keyword: str) -> EastMoneyFundMeta:
        results = self.search_funds(keyword, limit=1)
        if results:
            return results[0]

        raise HTTPException(status_code=404, detail=f"fund code or keyword not found: {keyword}")

    def fetch_fund_history(
        self,
        code: str,
        start_date: str | None,
        end_date: str | None,
    ) -> EastMoneyFundHistory:
        meta = self.search_fund(code)
        start = self._normalize_start_date(start_date)
        end = self._normalize_end_date(end_date)
        rows = self._fetch_history_page(meta.code, start, end, page=1, page_size=49)
        points = list(rows["points"])
        total_pages = rows["total_pages"]

        for page in range(2, total_pages + 1):
            page_rows = self._fetch_history_page(meta.code, start, end, page=page, page_size=49)
            points.extend(page_rows["points"])

        points.sort(key=lambda item: item.date)

        if not points:
            raise HTTPException(status_code=404, detail=f"no history found for fund: {meta.code}")

        return EastMoneyFundHistory(
            code=meta.code,
            name=meta.name,
            fund_type=meta.fund_type,
            points=points,
        )

    def fetch_fund_realtime(self, code: str) -> EastMoneyFundRealtime:
        meta = self.search_fund(code)
        try:
            raw = self._get_text(
                f"{self.realtime_endpoint}/{meta.code}.js",
                {},
                {"Referer": "https://fundgz.1234567.com.cn/"},
                timeout=6,
            )
            body = self._extract_jsonp_body(raw)
            if not body:
                raise HTTPException(status_code=502, detail="invalid eastmoney realtime response")

            payload = json.loads(body)
            estimate_nav = self._parse_number(str(payload.get("gsz") or ""))
            estimate_time = self._pick_first(payload.get("gztime"), payload.get("gzTime"))
            estimate_change = self._parse_number(str(payload.get("gszzl") or ""))

            unit_nav = self._parse_number(str(payload.get("dwjz") or ""))
            unit_nav_date = self._pick_first(payload.get("jzrq"))

            if estimate_nav is not None and estimate_time:
                return EastMoneyFundRealtime(
                    code=meta.code,
                    name=meta.name,
                    fund_type=meta.fund_type,
                    nav=estimate_nav,
                    nav_date=estimate_time,
                    change_percent=estimate_change,
                    value_kind="estimated",
                )

            if unit_nav is not None and unit_nav_date:
                return EastMoneyFundRealtime(
                    code=meta.code,
                    name=meta.name,
                    fund_type=meta.fund_type,
                    nav=unit_nav,
                    nav_date=unit_nav_date,
                    change_percent=None,
                    value_kind="unit_nav",
                )
        except HTTPException:
            pass

        latest_point = self.fetch_latest_fund_history_point(meta.code)
        return EastMoneyFundRealtime(
            code=meta.code,
            name=meta.name,
            fund_type=meta.fund_type,
            nav=latest_point.unit_nav,
            nav_date=latest_point.date,
            change_percent=None,
            value_kind="unit_nav",
        )

    def _fetch_history_page(
        self,
        code: str,
        start_date: str,
        end_date: str,
        page: int,
        page_size: int,
    ) -> dict[str, int | list[EastMoneyFundHistoryPoint]]:
        response = self._get_text(
            self.history_endpoint,
            {
                "type": "lsjz",
                "code": code,
                "page": str(page),
                "per": str(page_size),
                "sdate": start_date,
                "edate": end_date,
            },
            {"Referer": "https://fundf10.eastmoney.com/"},
        )

        content_match = re.search(r'content:"(.*?)",records:', response, re.S)
        pages_match = re.search(r"pages:(\d+)", response)
        if not content_match or not pages_match:
            raise HTTPException(status_code=502, detail="invalid eastmoney history response")

        html = content_match.group(1)
        row_matches = re.findall(r"<tr>(.*?)</tr>", html, re.S)
        points: list[EastMoneyFundHistoryPoint] = []
        for row_html in row_matches:
            columns = [
                self._strip_html(column)
                for column in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row_html, re.S)
            ]
            if len(columns) < 3 or columns[0] == "净值日期":
                continue

            unit_nav = self._parse_number(columns[1])
            accumulated_nav = self._parse_number(columns[2])
            if unit_nav is None or accumulated_nav is None:
                continue

            points.append(
                EastMoneyFundHistoryPoint(
                    date=columns[0],
                    unit_nav=unit_nav,
                    accumulated_nav=accumulated_nav,
                )
            )

        return {
            "points": points,
            "total_pages": max(int(pages_match.group(1)), 1),
        }

    def fetch_latest_fund_history_point(self, code: str) -> EastMoneyFundHistoryPoint:
        end_date = date.today().isoformat()
        rows = self._fetch_history_page(
            code=code,
            start_date="2000-01-01",
            end_date=end_date,
            page=1,
            page_size=1,
        )
        points = rows["points"]
        if not points:
            raise HTTPException(status_code=404, detail=f"no latest history point found for fund: {code}")
        return points[0]

    def _get_json(
        self,
        base_url: str,
        query: dict[str, str],
        headers: dict[str, str],
    ) -> dict:
        raw = self._get_text(base_url, query, headers)
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=502, detail="invalid eastmoney json response") from exc

    def _get_text(
        self,
        base_url: str,
        query: dict[str, str],
        headers: dict[str, str],
        timeout: int = 15,
    ) -> str:
        url = f"{base_url}?{urlencode(query)}" if query else base_url
        request = Request(url, headers=headers)
        try:
            with urlopen(request, timeout=timeout) as response:
                return response.read().decode("utf-8", errors="ignore")
        except HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"upstream http error: {exc.code}") from exc
        except Exception as exc:
            raise HTTPException(status_code=502, detail="failed to reach eastmoney upstream") from exc

    def _normalize_code(self, value: str) -> str:
        return value.strip()

    def _looks_like_fund_item(self, item: dict) -> bool:
        if item.get("FundBaseInfo"):
            return True

        category = self._pick_first(
            item.get("categoryDescription"),
            item.get("CATEGORYDESC"),
        )
        return category == "基金"

    def _pick_first(self, *values: str | None) -> str:
        for value in values:
            if value and value.strip():
                return value.strip()
        return ""

    def _normalize_start_date(self, value: str | None) -> str:
        if value:
            return self._parse_date(value).isoformat()
        return "2000-01-01"

    def _normalize_end_date(self, value: str | None) -> str:
        if value:
            return self._parse_date(value).isoformat()
        return date.today().isoformat()

    def _parse_date(self, value: str) -> date:
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"invalid date: {value}") from exc

    def _parse_number(self, raw: str) -> float | None:
        cleaned = raw.replace(",", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return None

    def _extract_jsonp_body(self, raw: str) -> str | None:
        text = raw.strip()
        prefix = "jsonpgz("
        suffix = ");"
        if text.startswith(prefix) and text.endswith(suffix):
            return text[len(prefix):-len(suffix)]
        return None

    def _strip_html(self, raw: str) -> str:
        text = re.sub(r"<[^>]+>", "", raw)
        return unescape(text).replace("\xa0", " ").strip()


eastmoney_provider = EastMoneyProvider()
