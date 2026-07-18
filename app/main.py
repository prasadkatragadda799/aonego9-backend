from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings

app = FastAPI(
    title="AOneGo9 API",
    description="Backend for the AOneGo9 platform — user, vendor, and superadmin apps.",
    version="1.0.0",
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    # All three frontends authenticate with a Bearer token, not cookies, so
    # credentialed (cookie-based) CORS requests are never needed — and
    # leaving this off lets CORS_ORIGINS stay "*" safely if ever needed.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
