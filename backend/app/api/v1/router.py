from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.agents import router as agents_router
from app.api.v1.runs import router as runs_router

api_v1_router = APIRouter()
api_v1_router.include_router(agents_router)
api_v1_router.include_router(runs_router)
