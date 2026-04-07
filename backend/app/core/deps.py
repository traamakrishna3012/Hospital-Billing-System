"""
FastAPI dependencies for authentication, authorization, and database access.
Enforces tenant isolation at the dependency level.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.security import decode_token
from app.models.user import User

# Bearer token scheme
bearer_scheme = HTTPBearer(auto_error=True)

# Type alias for database session dependency
DBSession = Annotated[AsyncSession, Depends(get_async_session)]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: DBSession,
) -> User:
    """
    Validate the JWT token and return the authenticated user.
    Raises 401 if token is invalid or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        raise credentials_exception

    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))  # noqa: E712
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


# Type alias for current user dependency
CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(*roles: str):
    """
    Dependency factory: restrict access to users with specific roles.

    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_role("admin"))])
    """
    async def _check_role(current_user: CurrentUser) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {', '.join(roles)}",
            )
        return current_user

    return _check_role


def get_tenant_id(current_user: CurrentUser) -> UUID:
    """Extract tenant_id from the current user — single source of truth."""
    return current_user.tenant_id


# Type alias for tenant ID dependency
TenantID = Annotated[UUID, Depends(get_tenant_id)]
