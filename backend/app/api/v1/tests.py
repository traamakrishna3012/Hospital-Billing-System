"""
Medical test and test category routes.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from app.core.deps import CurrentUser, DBSession, TenantID
from app.models.test import MedicalTest, TestCategory
from app.schemas.schemas import (
    MedicalTestCreate,
    MedicalTestResponse,
    MedicalTestUpdate,
    PaginatedResponse,
    TestCategoryCreate,
    TestCategoryResponse,
    TestCategoryUpdate,
)

router = APIRouter(prefix="/tests", tags=["Tests & Services"])


# ── Test Categories ───────────────────────────────────────────

@router.get("/categories", response_model=list[TestCategoryResponse], summary="List test categories")
async def list_categories(
    db: DBSession,
    tenant_id: TenantID,
    current_user: CurrentUser,
):
    result = await db.execute(
        select(TestCategory)
        .where(TestCategory.tenant_id == tenant_id)
        .order_by(TestCategory.name)
    )
    return [TestCategoryResponse.model_validate(c) for c in result.scalars().all()]


@router.post(
    "/categories",
    response_model=TestCategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create category",
)
async def create_category(
    data: TestCategoryCreate,
    db: DBSession,
    tenant_id: TenantID,
    current_user: CurrentUser,
):
    # Check uniqueness
    existing = await db.execute(
        select(TestCategory).where(
            TestCategory.tenant_id == tenant_id,
            TestCategory.name == data.name,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category with this name already exists",
        )

    category = TestCategory(tenant_id=tenant_id, **data.model_dump())
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return TestCategoryResponse.model_validate(category)


@router.put("/categories/{category_id}", response_model=TestCategoryResponse, summary="Update category")
async def update_category(
    category_id: UUID,
    data: TestCategoryUpdate,
    db: DBSession,
    tenant_id: TenantID,
    current_user: CurrentUser,
):
    result = await db.execute(
        select(TestCategory).where(
            TestCategory.id == category_id,
            TestCategory.tenant_id == tenant_id,
        )
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(category, key, value)

    await db.commit()
    await db.refresh(category)
    return TestCategoryResponse.model_validate(category)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete category")
async def delete_category(
    category_id: UUID,
    db: DBSession,
    tenant_id: TenantID,
    current_user: CurrentUser,
):
    result = await db.execute(
        select(TestCategory).where(
            TestCategory.id == category_id,
            TestCategory.tenant_id == tenant_id,
        )
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    await db.delete(category)
    await db.commit()


# ── Medical Tests ─────────────────────────────────────────────

@router.get("", response_model=PaginatedResponse, summary="List medical tests")
async def list_tests(
    db: DBSession,
    tenant_id: TenantID,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query("", max_length=100),
    category_id: UUID = Query(None),
    active_only: bool = Query(True),
):
    query = select(MedicalTest).options(selectinload(MedicalTest.category)).where(
        MedicalTest.tenant_id == tenant_id
    )
    count_query = select(func.count(MedicalTest.id)).where(
        MedicalTest.tenant_id == tenant_id
    )

    if active_only:
        query = query.where(MedicalTest.is_active == True)  # noqa: E712
        count_query = count_query.where(MedicalTest.is_active == True)  # noqa: E712

    if search:
        search_filter = or_(
            MedicalTest.name.ilike(f"%{search}%"),
            MedicalTest.code.ilike(f"%{search}%"),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    if category_id:
        query = query.where(MedicalTest.category_id == category_id)
        count_query = count_query.where(MedicalTest.category_id == category_id)

    total = (await db.execute(count_query)).scalar() or 0
    total_pages = max(1, (total + page_size - 1) // page_size)

    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(MedicalTest.name).offset(offset).limit(page_size)
    )
    tests = result.scalars().all()

    return PaginatedResponse(
        items=[MedicalTestResponse.model_validate(t) for t in tests],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{test_id}", response_model=MedicalTestResponse, summary="Get test details")
async def get_test(
    test_id: UUID,
    db: DBSession,
    tenant_id: TenantID,
    current_user: CurrentUser,
):
    result = await db.execute(
        select(MedicalTest)
        .options(selectinload(MedicalTest.category))
        .where(MedicalTest.id == test_id, MedicalTest.tenant_id == tenant_id)
    )
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")
    return MedicalTestResponse.model_validate(test)


@router.post("", response_model=MedicalTestResponse, status_code=status.HTTP_201_CREATED, summary="Add medical test")
async def create_test(
    data: MedicalTestCreate,
    db: DBSession,
    tenant_id: TenantID,
    current_user: CurrentUser,
):
    test = MedicalTest(tenant_id=tenant_id, **data.model_dump())
    db.add(test)
    await db.commit()
    await db.refresh(test)

    # Reload with category
    result = await db.execute(
        select(MedicalTest)
        .options(selectinload(MedicalTest.category))
        .where(MedicalTest.id == test.id)
    )
    test = result.scalar_one()
    return MedicalTestResponse.model_validate(test)


@router.put("/{test_id}", response_model=MedicalTestResponse, summary="Update medical test")
async def update_test(
    test_id: UUID,
    data: MedicalTestUpdate,
    db: DBSession,
    tenant_id: TenantID,
    current_user: CurrentUser,
):
    result = await db.execute(
        select(MedicalTest).where(
            MedicalTest.id == test_id, MedicalTest.tenant_id == tenant_id
        )
    )
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(test, key, value)

    await db.commit()
    await db.refresh(test)
    return MedicalTestResponse.model_validate(test)


@router.delete("/{test_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete medical test")
async def delete_test(
    test_id: UUID,
    db: DBSession,
    tenant_id: TenantID,
    current_user: CurrentUser,
):
    result = await db.execute(
        select(MedicalTest).where(
            MedicalTest.id == test_id, MedicalTest.tenant_id == tenant_id
        )
    )
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")

    await db.delete(test)
    await db.commit()
