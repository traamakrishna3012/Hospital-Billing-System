"""
Dashboard analytics service — revenue and statistics aggregation.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select, func, and_, case, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bill import Bill
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.schemas.schemas import DashboardStats, RevenueChartData, RecentTransaction


async def get_dashboard_stats(db: AsyncSession, tenant_id: UUID) -> DashboardStats:
    """Get aggregate statistics for the dashboard."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Execute sequentially to prevent AsyncSession concurrent transaction corruption issue in asyncpg
    t1 = await db.execute(select(func.coalesce(func.sum(Bill.total), 0)).where(Bill.tenant_id == tenant_id, Bill.status == "paid"))
    t2 = await db.execute(select(func.coalesce(func.sum(Bill.total), 0)).where(Bill.tenant_id == tenant_id, Bill.status == "paid", Bill.created_at >= today_start))
    t3 = await db.execute(select(func.coalesce(func.sum(Bill.total), 0)).where(Bill.tenant_id == tenant_id, Bill.status == "paid", Bill.created_at >= month_start))
    t4 = await db.execute(select(func.count(Patient.id)).where(Patient.tenant_id == tenant_id))
    t5 = await db.execute(select(func.count(Bill.id)).where(Bill.tenant_id == tenant_id))
    t6 = await db.execute(select(func.count(Bill.id)).where(Bill.tenant_id == tenant_id, Bill.created_at >= today_start))
    t7 = await db.execute(select(func.count(Bill.id)).where(Bill.tenant_id == tenant_id, Bill.created_at >= month_start))
    t8 = await db.execute(select(func.count(Doctor.id)).where(Doctor.tenant_id == tenant_id, Doctor.is_active == True))

    total_revenue = float(t1.scalar() or 0)
    today_revenue = float(t2.scalar() or 0)
    month_revenue = float(t3.scalar() or 0)
    total_patients = t4.scalar() or 0
    total_bills = t5.scalar() or 0
    today_bills = t6.scalar() or 0
    month_bills = t7.scalar() or 0
    total_doctors = t8.scalar() or 0

    return DashboardStats(
        total_revenue=total_revenue,
        total_patients=total_patients,
        total_bills=total_bills,
        total_doctors=total_doctors,
        today_revenue=today_revenue,
        today_bills=today_bills,
        month_revenue=month_revenue,
        month_bills=month_bills,
    )


async def get_revenue_chart_data(
    db: AsyncSession,
    tenant_id: UUID,
    period: str = "daily",  # daily | weekly | monthly
    days: int = 30,
) -> list[RevenueChartData]:
    """Get time-series revenue data for charts."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    start_date = now - timedelta(days=days)

    if period == "monthly":
        # Group by month
        result = await db.execute(
            select(
                func.to_char(Bill.created_at, "YYYY-MM").label("period"),
                func.coalesce(func.sum(Bill.total), 0).label("revenue"),
                func.count(Bill.id).label("count"),
            )
            .where(
                Bill.tenant_id == tenant_id,
                Bill.status == "paid",
                Bill.created_at >= start_date,
            )
            .group_by(func.to_char(Bill.created_at, "YYYY-MM"))
            .order_by(func.to_char(Bill.created_at, "YYYY-MM"))
        )
    elif period == "weekly":
        result = await db.execute(
            select(
                func.to_char(Bill.created_at, "IYYY-IW").label("period"),
                func.coalesce(func.sum(Bill.total), 0).label("revenue"),
                func.count(Bill.id).label("count"),
            )
            .where(
                Bill.tenant_id == tenant_id,
                Bill.status == "paid",
                Bill.created_at >= start_date,
            )
            .group_by(func.to_char(Bill.created_at, "IYYY-IW"))
            .order_by(func.to_char(Bill.created_at, "IYYY-IW"))
        )
    else:
        # Daily
        result = await db.execute(
            select(
                func.to_char(Bill.created_at, "YYYY-MM-DD").label("period"),
                func.coalesce(func.sum(Bill.total), 0).label("revenue"),
                func.count(Bill.id).label("count"),
            )
            .where(
                Bill.tenant_id == tenant_id,
                Bill.status == "paid",
                Bill.created_at >= start_date,
            )
            .group_by(func.to_char(Bill.created_at, "YYYY-MM-DD"))
            .order_by(func.to_char(Bill.created_at, "YYYY-MM-DD"))
        )

    rows = result.all()
    return [
        RevenueChartData(label=row.period, revenue=float(row.revenue), count=row.count)
        for row in rows
    ]


async def get_recent_transactions(
    db: AsyncSession,
    tenant_id: UUID,
    limit: int = 10,
) -> list[RecentTransaction]:
    """Get recent bills for the dashboard."""
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Bill)
        .options(selectinload(Bill.patient))
        .where(Bill.tenant_id == tenant_id)
        .order_by(Bill.created_at.desc())
        .limit(limit)
    )
    bills = result.scalars().all()

    transactions = []
    for bill in bills:
        # Get patient name
        patient = bill.patient
        patient_name = patient.name if patient else "Unknown"

        transactions.append(RecentTransaction(
            id=bill.id,
            bill_number=bill.bill_number,
            patient_name=patient_name,
            total=float(bill.total),
            status=bill.status,
            payment_mode=bill.payment_mode,
            created_at=bill.created_at,
        ))

    return transactions
