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
    """Get aggregate statistics across all tenants."""
    total_tenants = (await db.execute(select(func.count(Tenant.id)))).scalar() or 0
    active_tenants = (await db.execute(
        select(func.count(Tenant.id)).where(Tenant.is_active == True)  # noqa: E712
    )).scalar() or 0
    total_users = (await db.execute(
        select(func.count(User.id)).where(User.role != "superadmin")
    )).scalar() or 0
    total_patients = (await db.execute(select(func.count(Patient.id)))).scalar() or 0
    total_doctors = (await db.execute(select(func.count(Doctor.id)))).scalar() or 0
    total_bills = (await db.execute(select(func.count(Bill.id)))).scalar() or 0
    total_revenue = (await db.execute(
        select(func.coalesce(func.sum(Bill.total), 0)).where(Bill.status == "paid")
    )).scalar() or 0.0

    return PlatformStatsResponse(
        total_tenants=total_tenants,
        active_tenants=active_tenants,
        total_users=total_users,
        total_patients=total_patients,
        total_doctors=total_doctors,
        total_bills=total_bills,
        total_revenue=float(total_revenue),
    )


# ── Tenant Management ───────────────────────────────────────

@router.get("/tenants", response_model=list[TenantDetailResponse], summary="List all clinics")
async def list_tenants(db: DBSession, is_active: bool | None = None):
    """List all registered clinics/hospitals with aggregated stats."""
    query = select(Tenant)
    if is_active is not None:
        query = query.where(Tenant.is_active == is_active)
    query = query.order_by(Tenant.created_at.desc())

    result = await db.execute(query)
    tenants = result.scalars().all()

    enriched = []
    for t in tenants:
        user_count = (await db.execute(
            select(func.count(User.id)).where(User.tenant_id == t.id)
        )).scalar() or 0
        patient_count = (await db.execute(
            select(func.count(Patient.id)).where(Patient.tenant_id == t.id)
        )).scalar() or 0
        doctor_count = (await db.execute(
            select(func.count(Doctor.id)).where(Doctor.tenant_id == t.id)
        )).scalar() or 0
        bill_count = (await db.execute(
            select(func.count(Bill.id)).where(Bill.tenant_id == t.id)
        )).scalar() or 0
        total_revenue = (await db.execute(
            select(func.coalesce(func.sum(Bill.total), 0)).where(
                Bill.tenant_id == t.id, Bill.status == "paid"
            )
        )).scalar() or 0.0

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
    """Get detailed info about a single tenant."""
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")

    user_count = (await db.execute(
        select(func.count(User.id)).where(User.tenant_id == t.id)
    )).scalar() or 0
    patient_count = (await db.execute(
        select(func.count(Patient.id)).where(Patient.tenant_id == t.id)
    )).scalar() or 0
    doctor_count = (await db.execute(
        select(func.count(Doctor.id)).where(Doctor.tenant_id == t.id)
    )).scalar() or 0
    bill_count = (await db.execute(
        select(func.count(Bill.id)).where(Bill.tenant_id == t.id)
    )).scalar() or 0
    total_revenue = (await db.execute(
        select(func.coalesce(func.sum(Bill.total), 0)).where(
            Bill.tenant_id == t.id, Bill.status == "paid"
        )
    )).scalar() or 0.0

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
        created_at=t.created_at,
        user_count=user_count,
        patient_count=patient_count,
        doctor_count=doctor_count,
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
