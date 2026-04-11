"""User model — staff and administrators belonging to a tenant."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.tenant import Tenant


class User(Base):
    __tablename__ = "users"

    # ── Tenant Isolation ──────────────────────────────────────
    # nullable=True for superadmin users who operate at platform level
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # ── User Details ──────────────────────────────────────────
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # ── Role & Status ─────────────────────────────────────────
    role: Mapped[str] = mapped_column(
        String(20), default="staff", server_default="staff"
    )  # superadmin | admin | staff
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    # ── Relationships ─────────────────────────────────────────
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")

    __table_args__ = (
        # Unique email per tenant (not globally unique — different tenants may re-use emails)
        Index("uq_users_tenant_email", "tenant_id", "email", unique=True),
    )

    def __repr__(self) -> str:
        return f"<User {self.email} role={self.role}>"
