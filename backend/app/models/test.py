"""Test & TestCategory models — medical tests/services with dynamic pricing."""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import ForeignKey, String, Numeric, Boolean, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TestCategory(Base):
    __tablename__ = "test_categories"

    # ── Tenant Isolation ──────────────────────────────────────
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Category Details ──────────────────────────────────────
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Relationships ─────────────────────────────────────────
    tests: Mapped[list["MedicalTest"]] = relationship(
        "MedicalTest", back_populates="category", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("uq_test_categories_tenant_name", "tenant_id", "name", unique=True),
    )

    def __repr__(self) -> str:
        return f"<TestCategory {self.name}>"


class MedicalTest(Base):
    __tablename__ = "medical_tests"

    # ── Tenant Isolation ──────────────────────────────────────
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Category ──────────────────────────────────────────────
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("test_categories.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── Test Details ──────────────────────────────────────────
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # internal code

    # ── Status ────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    # ── Relationships ─────────────────────────────────────────
    category: Mapped[Optional["TestCategory"]] = relationship(
        "TestCategory", back_populates="tests"
    )

    __table_args__ = (
        Index("ix_medical_tests_tenant_name", "tenant_id", "name"),
        Index("ix_medical_tests_tenant_category", "tenant_id", "category_id"),
    )

    def __repr__(self) -> str:
        return f"<MedicalTest {self.name} ₹{self.price}>"
