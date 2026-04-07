"""Tenant (Clinic) model — represents a hospital or clinic organization."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Text, Boolean, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Tenant(Base):
    __tablename__ = "tenants"

    # ── Clinic Identity ───────────────────────────────────────
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)

    # ── Branding ──────────────────────────────────────────────
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pincode: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    tagline: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # ── Subscription ──────────────────────────────────────────
    subscription_plan: Mapped[str] = mapped_column(
        String(20), default="free", server_default="free"
    )
    subscription_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    # ── Settings ──────────────────────────────────────────────
    tax_percent: Mapped[float] = mapped_column(default=18.0, server_default="18.0")
    currency: Mapped[str] = mapped_column(String(5), default="INR", server_default="INR")

    # ── Relationships ─────────────────────────────────────────
    users: Mapped[list["User"]] = relationship("User", back_populates="tenant", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_tenants_email", "email"),
    )

    def __repr__(self) -> str:
        return f"<Tenant {self.name} ({self.slug})>"
