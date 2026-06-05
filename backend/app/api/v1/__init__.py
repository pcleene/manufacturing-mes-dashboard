from fastapi import APIRouter

from app.api.v1.routes import telemetry, dashboard

api_router = APIRouter()

api_router.include_router(telemetry.router, prefix="/telemetry", tags=["telemetry"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
