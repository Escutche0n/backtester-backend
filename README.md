# backtester-backend

Lightweight backend v1 for `backtester_note` (`回测手记`).

This repo focuses on a small, deployable JSON backend:

- fetch fund nav data
- clean and normalize data
- expose stable API responses
- support iOS, Shortcuts, and Python clients

It intentionally avoids heavy platform architecture, user systems, and microservices.

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
  schemas/            request and response models
  services/           business logic and mock data providers
  main.py             FastAPI entrypoint
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

Current implementations are mock-first placeholders with stable response shapes so the data layer can evolve without rewriting the API contract.

## Environment Variables

See `.env.example`.

Key variables:

- `APP_ENV`: `development` or `production`
- `APP_HOST`: bind host
- `APP_PORT`: bind port
- `API_PREFIX`: API path prefix, default `/api`
- `DEFAULT_DATA_SOURCE`: current default provider label

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

When you are ready, the next step is wiring real fund data providers into `app/services/`.
