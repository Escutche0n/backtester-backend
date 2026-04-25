# backtester-backend

Lightweight backend v1 for `backtester_note` (`回测手记`).

This repo focuses on a small, deployable JSON backend:

- fetch fund nav data
- clean and normalize data
- expose stable API responses
- support iOS, Shortcuts, and Python clients

It intentionally avoids heavy platform architecture, user systems, and microservices.

Current v1 target:

- input a fund code
- fetch fund history from Eastmoney
- return clean JSON with fund metadata and historical nav points

## Stack

- Python 3.11+
- FastAPI
- Uvicorn
- Pydantic Settings

## Project Layout

```text
app/
  api/routes/         HTTP route handlers
  core/               config and shared settings
  providers/          upstream data providers
  schemas/            request and response models
  services/           business logic
  main.py             FastAPI entrypoint
scripts/
  backup_git.sh       commit and push helper
```

## Quick Start

1. Create and activate a virtualenv:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -e .
```

For local API verification or future tests:

```bash
pip install -e ".[dev]"
```

3. Create local env file:

```bash
cp .env.example .env
```

4. Run the server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. Open:

- API root: <http://127.0.0.1:8000/>
- Docs: <http://127.0.0.1:8000/docs>

## API Endpoints

- `GET /health`
- `GET /api/fund/search`
- `GET /api/fund/realtime`
- `GET /api/fund/history`
- `POST /api/portfolio/history`

Full API usage guide:

- `docs/API_USAGE.md`

Current status:

- `GET /api/fund/search` uses Eastmoney search upstream
- `GET /api/fund/realtime` uses Eastmoney realtime upstream with fallback to latest confirmed unit nav
- `GET /api/fund/history` uses Eastmoney history upstream
- `POST /api/portfolio/realtime` calculates estimated intraday portfolio profit/loss from holdings and fund realtime data
- `POST /api/portfolio/history` is still a mock implementation

## Fund History JSON

Example request:

```bash
curl --noproxy '*' "http://127.0.0.1:8000/api/fund/history?code=161725&start_date=2024-01-01&end_date=2024-01-05"
```

Example response:

```json
{
  "fund_code": "161725",
  "fund_name": "招商中证白酒指数(LOF)A",
  "fund_type": "指数型-股票",
  "source": "eastmoney",
  "start_date": "2024-01-01",
  "end_date": "2024-01-05",
  "points": [
    {
      "date": "2024-01-02",
      "unit_nav": 0.9201,
      "accumulated_nav": 2.6362
    },
    {
      "date": "2024-01-03",
      "unit_nav": 0.9159,
      "accumulated_nav": 2.6320
    }
  ]
}
```

Response fields:

- `fund_code`: fund code
- `fund_name`: fund name
- `fund_type`: fund type from Eastmoney search metadata
- `date`: nav date
- `unit_nav`: unit nav
- `accumulated_nav`: accumulated nav

`fund_type` is resolved with this priority:

1. `fundBaseInfo.fundTypeDescription`
2. `categoryDescription`
3. fallback to `"基金"`

The current provider also accepts the uppercase field names returned by the live Eastmoney API.

## Fund Realtime JSON

Example request:

```bash
curl --noproxy '*' "http://127.0.0.1:8000/api/fund/realtime?code=006195"
```

Example response:

```json
{
  "data": {
    "code": "006195",
    "name": "国金量化多因子股票A",
    "fund_type": "股票型",
    "nav": 3.5202,
    "nav_date": "2026-04-22 15:00",
    "change_percent": 1.32,
    "value_kind": "estimated",
    "source": "eastmoney"
  }
}
```

Realtime notes:

- `value_kind = "estimated"` means intraday estimated nav
- `value_kind = "unit_nav"` means the realtime upstream failed or had no estimate, so the service fell back to the latest confirmed unit nav
- `change_percent` is only present for estimated values

## Portfolio Realtime JSON

This endpoint is designed for personal Shortcuts / mobile usage.

Example request:

```bash
curl --noproxy '*' \
  -X POST "http://127.0.0.1:8000/api/portfolio/realtime" \
  -H "Content-Type: application/json" \
  -d '{
    "holdings": [
      {"fund_code": "006195", "shares": 1000},
      {"fund_code": "008163", "shares": 2000}
    ]
  }'
```

Example response:

```json
{
  "summary": {
    "base_value": 5645.6,
    "estimated_value": 5662.0,
    "estimated_profit": 16.4,
    "estimated_return": 0.002905
  },
  "items": [
    {
      "fund_code": "006195",
      "fund_name": "国金量化多因子股票A",
      "fund_type": "股票型",
      "shares": 1000.0,
      "base_date": "2026-04-22",
      "base_nav": 3.5038,
      "estimated_time": "2026-04-22 15:00",
      "estimated_nav": 3.5202,
      "value_kind": "estimated",
      "base_value": 3503.8,
      "estimated_value": 3520.2,
      "estimated_profit": 16.4,
      "estimated_return": 0.004681
    }
  ],
  "disclaimer": "估算结果仅供个人记录，不代表确认净值或投资建议。"
}
```

Portfolio calculation:

- `base_value = shares * latest confirmed unit nav`
- `estimated_value = shares * realtime nav`
- `estimated_profit = estimated_value - base_value`
- `estimated_return = estimated_profit / base_value`

## Local Testing Notes

If `curl` hangs or shows no response, check whether your shell is forcing a local proxy.

Test health:

```bash
curl --noproxy '*' "http://127.0.0.1:8000/health"
```

If needed, clear proxy variables for the current shell:

```bash
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
```

## Environment Variables

See `.env.example`.

Key variables:

- `APP_ENV`: `development` or `production`
- `APP_HOST`: bind host
- `APP_PORT`: bind port
- `API_PREFIX`: API path prefix, default `/api`
- `DEFAULT_DATA_SOURCE`: current default provider label

## Upstream Notes

Current upstream endpoints used by this repo:

- search: `https://fundsuggest.eastmoney.com/FundSearch/api/FundSearchAPI.ashx`
- realtime: `https://fundgz.1234567.com.cn/js/<fund_code>.js`
- history: `https://fundf10.eastmoney.com/F10DataApi.aspx`

Important boundary:

- this repo currently uses website-facing Eastmoney / Tiantian Fund endpoints
- I did not find official public developer API documentation that explicitly authorizes these endpoints for third-party product integration
- I did find public legal / service pages for Eastmoney, but not a clear "open API" statement covering the JSON / JSONP endpoints used here

That means:

- treat these upstreams as unofficial website endpoints rather than stable public APIs
- expect upstream format changes, rate limits, anti-bot controls, or availability changes
- avoid representing this project as an officially supported Eastmoney API client
- if you later publish or commercialize this backend, re-check terms, copyright, attribution, and data usage constraints before broader rollout

Relevant public pages reviewed:

- Eastmoney legal disclaimer: [about.eastmoney.com/home/disclaimer](https://about.eastmoney.com/home/disclaimer)
- Eastmoney site homepage: [www.eastmoney.com](https://www.eastmoney.com/)
- Tiantian Fund homepage: [fund.eastmoney.com](https://fund.eastmoney.com/)

## Deploying To Tencent Cloud Lighthouse

Recommended v1 setup:

1. Buy a lightweight Lighthouse Linux instance.
2. Install Python 3.11+, `git`, and `nginx`.
3. Clone this repo to `/srv/backtester-backend`.
4. Create a virtualenv and install with `pip install -e .`.
5. Copy `.env.example` to `.env` and set production values.
6. Run Uvicorn behind `systemd`, optionally behind `nginx` reverse proxy.
7. Point your domain or subdomain to the server.

Suggested production layout:

- app process: `127.0.0.1:8000`
- reverse proxy: `nginx`
- process manager: `systemd`

## Git Backup Helper

This repo includes a small helper script for fast local backup to GitHub:

```bash
./scripts/backup_git.sh "update history endpoint"
```

It runs:

- `git add .`
- `git commit -m "..."`
- `git push`

Use it only when you want to back up the current working tree as-is.
