"""
Authentication routes — register, login, refresh, profile.
"""

from __future__ import annotations

import re
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.core.deps import CurrentUser, DBSession
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.email_service import send_welcome_email

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _slugify(name: str) -> str:
    """Convert a clinic name to a URL-friendly slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug[:100]


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new clinic",
)
async def register(data: RegisterRequest, db: DBSession, background_tasks: BackgroundTasks):
    """
    Register a new clinic/hospital. Creates a tenant and an admin user.
    Returns JWT tokens for immediate authentication.
    """
    # Check if admin email already exists
    existing = await db.execute(
        select(User).where(User.email == data.admin_email).limit(1)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    # Generate unique slug
    base_slug = _slugify(data.clinic_name)
    slug = base_slug
    counter = 1
    while True:
        existing_tenant = await db.execute(
            select(Tenant).where(Tenant.slug == slug).limit(1)
        )
        if not existing_tenant.scalar_one_or_none():
            break
        slug = f"{base_slug}-{counter}"
        counter += 1

    # Create tenant
    tenant = Tenant(
        name=data.clinic_name,
        slug=slug,
        email=data.clinic_email,
        phone=data.clinic_phone,
        address=data.clinic_address,
    )
    db.add(tenant)
    await db.flush()

    # Create admin user
    user = User(
        tenant_id=tenant.id,
        email=data.admin_email,
        password_hash=hash_password(data.admin_password),
        full_name=data.admin_name,
        role="admin",
        is_approved=tenant.is_approved
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Generate tokens
    access_token = create_access_token(user.id, tenant.id, user.role)
    refresh_token = create_refresh_token(user.id, tenant.id)

    # Send welcome email (background task)
    background_tasks.add_task(send_welcome_email, tenant.name, user.full_name, user.email)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse, summary="User login")
async def login(data: LoginRequest, db: DBSession):
    """Authenticate with email and password. Returns JWT tokens."""
    result = await db.execute(
        select(User).where(User.email == data.email, User.is_active == True)  # noqa: E712
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(user.id, user.tenant_id, user.role)
    refresh_token = create_refresh_token(user.id, user.tenant_id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse, summary="Refresh access token")
async def refresh_token(data: RefreshRequest, db: DBSession):
    """Get a new access token using a refresh token."""
    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = UUID(payload["sub"])
    
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)  # noqa: E712
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    access_token = create_access_token(user.id, user.tenant_id, user.role)
    new_refresh_token = create_refresh_token(user.id, user.tenant_id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse, summary="Get current user profile")
async def get_me(current_user: CurrentUser):
    """Get the authenticated user's profile."""
    return UserResponse.model_validate(current_user)
