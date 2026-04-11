"""
Super Admin routes — platform-level management for the SaaS provider.
All endpoints require superadmin role.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import DBSession, require_role
from app.models.tenant import Tenant
from app.models.user import User
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.bill import Bill

from app.schemas.schemas import (
    PlatformStatsResponse,
    TenantDetailResponse,
    TenantAdminUpdateRequest,
    TenantResponse,
    UserResponse,
)

router = APIRouter(
    prefix="/superadmin",
    tags=["Super Admin"],
    dependencies=[Depends(require_role("superadmin"))],
)


# ── Platform Stats ───────────────────────────────────────────

@router.get("/stats", response_model=PlatformStatsResponse, summary="Platform-wide analytics")
async def get_platform_stats(db: DBSession):
    """Get aggregate statistics across all tenants (Optimized)."""
    # Combine all stats into a single query using subqueries for cleaner aggregation
    query = select(
        func.count(Tenant.id).label("total_tenants"),
        select(func.count(Tenant.id)).where(Tenant.is_active == True).scalar_subquery().label("active_tenants"),  # noqa: E712
        select(func.count(User.id)).where(User.role != "superadmin").scalar_subquery().label("total_users"),
        select(func.count(Patient.id)).scalar_subquery().label("total_patients"),
        select(func.count(Doctor.id)).scalar_subquery().label("total_doctors"),
        select(func.count(Bill.id)).scalar_subquery().label("total_bills"),
        select(func.coalesce(func.sum(Bill.total), 0)).where(Bill.status == "paid").scalar_subquery().label("total_revenue")
    )
    
    result = await db.execute(query)
    row = result.first()

    return PlatformStatsResponse(
        total_tenants=row.total_tenants or 0,
        active_tenants=row.active_tenants or 0,
        total_users=row.total_users or 0,
        total_patients=row.total_patients or 0,
        total_doctors=row.total_doctors or 0,
        total_bills=row.total_bills or 0,
        total_revenue=float(row.total_revenue or 0.0),
    )


# ── Tenant Management ───────────────────────────────────────

@router.get("/tenants", response_model=list[TenantDetailResponse], summary="List all clinics")
async def list_tenants(db: DBSession, is_active: bool | None = None):
    """List all registered clinics/hospitals with aggregated stats (Optimized)."""
    # Subqueries for counts to avoid N+1
    user_counts = select(User.tenant_id, func.count(User.id).label("count")).group_by(User.tenant_id).subquery()
    patient_counts = select(Patient.tenant_id, func.count(Patient.id).label("count")).group_by(Patient.tenant_id).subquery()
    doctor_counts = select(Doctor.tenant_id, func.count(Doctor.id).label("count")).group_by(Doctor.tenant_id).subquery()
    bill_stats = select(
        Bill.tenant_id, 
        func.count(Bill.id).label("count"),
        func.coalesce(func.sum(case((Bill.status == "paid", Bill.total), else_=0)), 0).label("revenue")
    ).group_by(Bill.tenant_id).subquery()

    query = (
        select(
            Tenant,
            func.coalesce(user_counts.c.count, 0).label("user_count"),
            func.coalesce(patient_counts.c.count, 0).label("patient_count"),
            func.coalesce(doctor_counts.c.count, 0).label("doctor_count"),
            func.coalesce(bill_stats.c.count, 0).label("bill_count"),
            func.coalesce(bill_stats.c.revenue, 0.0).label("total_revenue"),
        )
        .outerjoin(user_counts, Tenant.id == user_counts.c.tenant_id)
        .outerjoin(patient_counts, Tenant.id == patient_counts.c.tenant_id)
        .outerjoin(doctor_counts, Tenant.id == doctor_counts.c.tenant_id)
        .outerjoin(bill_stats, Tenant.id == bill_stats.c.tenant_id)
    )

    if is_active is not None:
        query = query.where(Tenant.is_active == is_active)
    
    query = query.order_by(Tenant.created_at.desc())

    result = await db.execute(query)
    rows = result.all()

    enriched = []
    for row in rows:
        t, user_count, patient_count, doctor_count, bill_count, total_revenue = row
        enriched.append(TenantDetailResponse(
            id=t.id,
            name=t.name,
            slug=t.slug,
            email=t.email,
            phone=t.phone,
            address=t.address,
            city=t.city,
            state=t.state,
            subscription_plan=t.subscription_plan,
            is_active=t.is_active,
            is_approved=t.is_approved,
            biller_header=t.biller_header,
            created_at=t.created_at,
            user_count=user_count,
            patient_count=patient_count,
            doctor_count=doctor_count,
            bill_count=bill_count,
            total_revenue=float(total_revenue),
        ))

    return enriched


@router.get("/tenants/{tenant_id}", response_model=TenantDetailResponse, summary="Get clinic details")
async def get_tenant(tenant_id: UUID, db: DBSession):
    """Get detailed info about a single tenant (Optimized)."""
    user_counts = select(func.count(User.id)).where(User.tenant_id == tenant_id).scalar_subquery()
    patient_counts = select(func.count(Patient.id)).where(Patient.tenant_id == tenant_id).scalar_subquery()
    doctor_counts = select(func.count(Doctor.id)).where(Doctor.tenant_id == tenant_id).scalar_subquery()
    bill_stats = select(
        func.count(Bill.id).label("count"),
        func.coalesce(func.sum(case((Bill.status == "paid", Bill.total), else_=0)), 0).label("revenue")
    ).where(Bill.tenant_id == tenant_id).subquery()

    result = await db.execute(
        select(
            Tenant,
            user_counts.label("user_count"),
            patient_counts.label("patient_count"),
            doctor_counts.label("doctor_count"),
            func.coalesce(bill_stats.c.count, 0).label("bill_count"),
            func.coalesce(bill_stats.c.revenue, 0.0).label("total_revenue"),
        ).where(Tenant.id == tenant_id)
    )
    
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Tenant not found")

    t, user_count, patient_count, doctor_count, bill_count, total_revenue = row

    return TenantDetailResponse(
        id=t.id,
        name=t.name,
        slug=t.slug,
        email=t.email,
        phone=t.phone,
        address=t.address,
        city=t.city,
        state=t.state,
        subscription_plan=t.subscription_plan,
        is_active=t.is_active,
        is_approved=t.is_approved,
        biller_header=t.biller_header,
        created_at=t.created_at,
        user_count=user_count,
        patient_count=patient_count,
        doctor_count=doctor_count,
        bill_count=bill_count,
        total_revenue=float(total_revenue),
    )
        bill_count=bill_count,
        total_revenue=float(total_revenue),
    )


@router.patch("/tenants/{tenant_id}", response_model=TenantResponse, summary="Update clinic")
async def update_tenant(tenant_id: UUID, data: TenantAdminUpdateRequest, db: DBSession):
    """Enable/disable a clinic or change its subscription plan."""
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(tenant, key, value)

    if "is_approved" in update_data:
        from sqlalchemy import update
        await db.execute(
            update(User).where(User.tenant_id == tenant_id).values(is_approved=update_data["is_approved"])
        )

    if "is_active" in update_data:
        from sqlalchemy import update
        await db.execute(
            update(User).where(User.tenant_id == tenant_id).values(is_active=update_data["is_active"])
        )

    await db.commit()
    await db.refresh(tenant)
    return TenantResponse.model_validate(tenant)


@router.delete("/tenants/{tenant_id}", summary="Deactivate a clinic")
async def deactivate_tenant(tenant_id: UUID, db: DBSession):
    """Soft-delete (deactivate) a clinic. All users lose access."""
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    tenant.is_active = False
    
    from sqlalchemy import update
    await db.execute(
        update(User).where(User.tenant_id == tenant_id).values(is_active=False)
    )

    await db.commit()
    return {"detail": f"Clinic '{tenant.name}' has been deactivated"}


# ── Cross-Tenant User List ───────────────────────────────────

@router.get("/users", response_model=list[UserResponse], summary="List all users")
async def list_all_users(db: DBSession, role: str | None = None):
    """List all users across all tenants. Optionally filter by role."""
    query = select(User).where(User.role != "superadmin")
    if role:
        query = query.where(User.role == role)
    query = query.order_by(User.created_at.desc())

    result = await db.execute(query)
    users = result.scalars().all()
    return [UserResponse.model_validate(u) for u in users]
