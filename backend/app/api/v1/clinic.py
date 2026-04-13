"""
Clinic settings routes — profile, logo, subscription.
"""

from __future__ import annotations

import os
import shutil
from uuid import UUID

from fastapi import APIRouter, HTTPException, UploadFile, File, status
from sqlalchemy import select

from app.core.config import get_settings
from app.core.deps import CurrentUser, DBSession, TenantID, require_role
from app.models.tenant import Tenant
from app.schemas.schemas import TenantResponse, TenantUpdateRequest

settings = get_settings()
router = APIRouter(prefix="/clinic", tags=["Clinic Settings"])

ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp", "image/svg+xml"}


@router.get("", response_model=TenantResponse, summary="Get clinic profile")
async def get_clinic_profile(
    db: DBSession,
    tenant_id: TenantID,
    current_user: CurrentUser,
):
    """Get the current clinic's profile and settings."""
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinic not found")
    return TenantResponse.model_validate(tenant)


@router.put("", response_model=TenantResponse, summary="Update clinic profile")
async def update_clinic_profile(
    data: TenantUpdateRequest,
    db: DBSession,
    tenant_id: TenantID,
    current_user: CurrentUser,
):
    """Update clinic profile. Admin only."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinic not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(tenant, key, value)

    await db.commit()
    await db.refresh(tenant)
    return TenantResponse.model_validate(tenant)


@router.post("/logo", response_model=TenantResponse, summary="Upload clinic logo")
async def upload_logo(
    db: DBSession,
    tenant_id: TenantID,
    current_user: CurrentUser,
    file: UploadFile = File(...),
):
    """Upload or replace the clinic logo. Admin only."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    # Validate file type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_IMAGE_TYPES)}",
        )

    # Validate file size
    content = await file.read()
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    # Save file
    ext = (file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "png").lower()
    logo_dir = os.path.join(settings.UPLOAD_DIR, "logos", str(tenant_id))
    os.makedirs(logo_dir, exist_ok=True)
    logo_filename = f"logo.{ext}"
    logo_path = os.path.join(logo_dir, logo_filename)

    with open(logo_path, "wb") as f:
        f.write(content)

    # Store as a public URL path (served via /uploads static mount)
    public_logo_url = f"uploads/logos/{tenant_id}/{logo_filename}"

    # Update tenant
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one()
    tenant.logo_url = public_logo_url
    await db.commit()
    await db.refresh(tenant)

    return TenantResponse.model_validate(tenant)


@router.get("/subscription", summary="Get subscription info")
async def get_subscription(
    db: DBSession,
    tenant_id: TenantID,
    current_user: CurrentUser,
):
    """Get current subscription plan details."""
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one()

    return {
        "plan": tenant.subscription_plan,
        "expires_at": tenant.subscription_expires_at,
        "is_active": tenant.is_active,
        "available_plans": [
            {
                "name": "free",
                "price": 0,
                "features": ["Up to 50 patients", "Basic billing", "1 staff user"],
            },
            {
                "name": "basic",
                "price": 999,
                "features": ["Up to 500 patients", "PDF receipts", "5 staff users", "Email notifications"],
            },
            {
                "name": "premium",
                "price": 2499,
                "features": ["Unlimited patients", "PDF receipts", "Unlimited staff", "Email notifications", "Analytics dashboard", "Priority support"],
            },
        ],
    }
