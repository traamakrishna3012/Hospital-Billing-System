"""
Report export routes — CSV and PDF.
"""

from __future__ import annotations

import csv
import io
from datetime import datetime, timezone

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.deps import CurrentUser, DBSession, TenantID
from app.models.bill import Bill

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/export/csv", summary="Export bills as CSV")
async def export_bills_csv(
    db: DBSession,
    tenant_id: TenantID,
    current_user: CurrentUser,
    status_filter: str = Query("", alias="status", max_length=20),
    date_from: str = Query("", max_length=10),
    date_to: str = Query("", max_length=10),
):
    """Export bills as a CSV file with optional date and status filters."""
    query = (
        select(Bill)
        .options(selectinload(Bill.patient), selectinload(Bill.doctor))
        .where(Bill.tenant_id == tenant_id)
    )

    if status_filter:
        query = query.where(Bill.status == status_filter)

    if date_from:
        try:
            from_date = datetime.strptime(date_from, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            query = query.where(Bill.created_at >= from_date)
        except ValueError:
            pass

    if date_to:
        try:
            to_date = datetime.strptime(date_to, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59, tzinfo=timezone.utc
            )
            query = query.where(Bill.created_at <= to_date)
        except ValueError:
            pass

    result = await db.execute(query.order_by(Bill.created_at.desc()))
    bills = result.scalars().unique().all()

    # Build CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Bill Number",
        "Date",
        "Patient Name",
        "Patient Phone",
        "Doctor Name",
        "Subtotal",
        "Tax %",
        "Tax Amount",
        "Discount %",
        "Discount Amount",
        "Total",
        "Status",
        "Payment Mode",
    ])

    for bill in bills:
        writer.writerow([
            bill.bill_number,
            bill.created_at.strftime("%Y-%m-%d %H:%M") if bill.created_at else "",
            bill.patient.name if bill.patient else "N/A",
            bill.patient.phone if bill.patient else "N/A",
            bill.doctor.name if bill.doctor else "N/A",
            float(bill.subtotal),
            float(bill.tax_percent),
            float(bill.tax_amount),
            float(bill.discount_percent),
            float(bill.discount_amount),
            float(bill.total),
            bill.status,
            bill.payment_mode,
        ])

    output.seek(0)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="bills_report_{timestamp}.csv"'
        },
    )
