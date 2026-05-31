from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.agents import router as agents_router
from app.api.v1.approvals import router as approvals_router
from app.api.v1.evaluations import router as evaluations_router
from app.api.v1.runs import router as runs_router
from app.api.v1.traces import router as traces_router

api_v1_router = APIRouter()
api_v1_router.include_router(agents_router)
api_v1_router.include_router(approvals_router)
api_v1_router.include_router(evaluations_router)
api_v1_router.include_router(runs_router)
api_v1_router.include_router(traces_router)
