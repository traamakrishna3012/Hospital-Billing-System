"""Doctor model — doctors belonging to a tenant/clinic."""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import ForeignKey, String, Numeric, Boolean, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Doctor(Base):
    __tablename__ = "doctors"

    # ── Tenant Isolation ──────────────────────────────────────
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Doctor Details ────────────────────────────────────────
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    specialization: Mapped[str] = mapped_column(String(255), nullable=False)
    qualification: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # ── Consultation ──────────────────────────────────────────
    consultation_fee: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )
    availability: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON string: e.g., "Mon-Fri 9AM-5PM"

    # ── Status ────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    __table_args__ = (
        Index("ix_doctors_tenant_name", "tenant_id", "name"),
        Index("ix_doctors_tenant_specialization", "tenant_id", "specialization"),
    )

    def __repr__(self) -> str:
        return f"<Doctor {self.name} ({self.specialization})>"
