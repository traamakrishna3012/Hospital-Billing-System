"""
Dashboard routes — analytics and recent activity.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.core.deps import CurrentUser, DBSession, TenantID
from app.schemas.schemas import DashboardStats, RevenueChartData, RecentTransaction
from app.services.dashboard_service import (
    get_dashboard_stats,
    get_recent_transactions,
    get_revenue_chart_data,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats, summary="Dashboard statistics")
async def dashboard_stats(
    db: DBSession,
    tenant_id: TenantID,
    current_user: CurrentUser,
):
    """Get aggregate statistics: revenue, patient count, bill count, etc."""
    return await get_dashboard_stats(db, tenant_id)


@router.get("/chart-data", response_model=list[RevenueChartData], summary="Revenue chart data")
async def chart_data(
    db: DBSession,
    tenant_id: TenantID,
    current_user: CurrentUser,
    period: str = Query("daily", pattern="^(daily|weekly|monthly)$"),
    days: int = Query(30, ge=7, le=365),
):
    """Get time-series revenue data for charts."""
    return await get_revenue_chart_data(db, tenant_id, period, days)


@router.get("/recent", response_model=list[RecentTransaction], summary="Recent transactions")
async def recent_transactions(
    db: DBSession,
    tenant_id: TenantID,
    current_user: CurrentUser,
    limit: int = Query(10, ge=1, le=50),
):
    """Get the most recent bills/transactions."""
    return await get_recent_transactions(db, tenant_id, limit)
