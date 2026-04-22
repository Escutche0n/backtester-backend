from fastapi import FastAPI

from app.api.routes import fund, health, portfolio
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Backend v1 for backtester_note.",
)


@app.get("/", tags=["root"])
def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "env": settings.app_env,
        "docs": "/docs",
    }


app.include_router(health.router)
app.include_router(fund.router, prefix=settings.api_prefix)
app.include_router(portfolio.router, prefix=settings.api_prefix)

