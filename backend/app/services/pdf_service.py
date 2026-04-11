"""
PDF receipt generation service with dynamic clinic branding.
Uses ReportLab for professional invoice layout.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Optional
from uuid import UUID

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image,
    HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

from app.core.config import get_settings

settings = get_settings()


def _get_styles():
    """Custom paragraph styles for the receipt."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        "ClinicName",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=2,
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        "ClinicInfo",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#64748b"),
        alignment=TA_CENTER,
        spaceAfter=1,
    ))
    styles.add(ParagraphStyle(
        "InvoiceTitle",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#4f46e5"),
        spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        "SectionLabel",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#94a3b8"),
        spaceBefore=2,
    ))
    styles.add(ParagraphStyle(
        "SectionValue",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=1,
    ))
    styles.add(ParagraphStyle(
        "FooterText",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#94a3b8"),
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        "RightAlign",
        parent=styles["Normal"],
        fontSize=10,
        alignment=TA_RIGHT,
    ))

    return styles


def generate_receipt_pdf(
    bill_data: dict,
    tenant_data: dict,
    patient_data: dict,
    doctor_data: Optional[dict],
    items_data: list[dict],
    output_path: Optional[str] = None,
) -> bytes:
    """
    Generate a professional PDF receipt.

    Returns PDF bytes. Optionally saves to output_path.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = _get_styles()
    elements = []

    # ── Header: Clinic Branding ───────────────────────────────
    # Logo
    logo_url = tenant_data.get("logo_url")
    if logo_url and os.path.exists(logo_url):
        try:
            logo = Image(logo_url, width=60, height=60)
            logo.hAlign = "CENTER"
            elements.append(logo)
            elements.append(Spacer(1, 4 * mm))
        except Exception:
            pass

    # Clinic name
    elements.append(Paragraph(tenant_data.get("name", "Clinic"), styles["ClinicName"]))

    # Biller Header (Customization)
    biller_header = tenant_data.get("biller_header")
    if biller_header:
        elements.append(Paragraph(biller_header, styles["ClinicInfo"]))
        elements.append(Spacer(1, 2 * mm))

    # Address & Contact
    address_parts = []
    if tenant_data.get("address"):
        address_parts.append(tenant_data["address"])
    city_state = ", ".join(filter(None, [
        tenant_data.get("city"),
        tenant_data.get("state"),
        tenant_data.get("pincode"),
    ]))
    if city_state:
        address_parts.append(city_state)
    if address_parts:
        elements.append(Paragraph(" | ".join(address_parts), styles["ClinicInfo"]))

    contact_parts = []
    if tenant_data.get("phone"):
        contact_parts.append(f"Phone: {tenant_data['phone']}")
    if tenant_data.get("email"):
        contact_parts.append(f"Email: {tenant_data['email']}")
    if contact_parts:
        elements.append(Paragraph(" | ".join(contact_parts), styles["ClinicInfo"]))

    if tenant_data.get("tagline"):
        elements.append(Paragraph(tenant_data["tagline"], styles["ClinicInfo"]))

    elements.append(Spacer(1, 4 * mm))
    elements.append(HRFlowable(
        width="100%", thickness=1.5,
        color=colors.HexColor("#4f46e5"),
        spaceBefore=2, spaceAfter=6,
    ))

    # ── Invoice Header ────────────────────────────────────────
    bill_info = [
        [
            Paragraph("INVOICE", styles["InvoiceTitle"]),
            "",
            Paragraph(f"<b>#{bill_data['bill_number']}</b>", styles["RightAlign"]),
        ],
    ]
    bill_table = Table(bill_info, colWidths=["40%", "20%", "40%"])
    bill_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elements.append(bill_table)

    # ── Patient & Bill Details ────────────────────────────────
    created_at = bill_data.get("created_at", "")
    if isinstance(created_at, datetime):
        created_at = created_at.strftime("%d %b %Y, %I:%M %p")

    left_col = [
        Paragraph("Patient Details", styles["SectionLabel"]),
        Paragraph(f"<b>{patient_data.get('name', 'N/A')}</b>", styles["SectionValue"]),
        Paragraph(f"Phone: {patient_data.get('phone', 'N/A')}", styles["SectionValue"]),
        Paragraph(f"Age: {patient_data.get('age', 'N/A')} | Gender: {patient_data.get('gender', 'N/A').title()}", styles["SectionValue"]),
    ]

    right_col = [
        Paragraph("Bill Details", styles["SectionLabel"]),
        Paragraph(f"Date: <b>{created_at}</b>", styles["SectionValue"]),
        Paragraph(f"Status: <b>{bill_data.get('status', 'paid').upper()}</b>", styles["SectionValue"]),
        Paragraph(f"Payment: <b>{bill_data.get('payment_mode', 'cash').upper()}</b>", styles["SectionValue"]),
    ]

    if doctor_data:
        left_col.append(Spacer(1, 3 * mm))
        left_col.append(Paragraph("Consulting Doctor", styles["SectionLabel"]))
        left_col.append(Paragraph(f"<b>Dr. {doctor_data.get('name', 'N/A')}</b>", styles["SectionValue"]))
        left_col.append(Paragraph(f"{doctor_data.get('specialization', '')}", styles["SectionValue"]))

    detail_table = Table(
        [[left_col, right_col]],
        colWidths=["55%", "45%"],
    )
    detail_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elements.append(detail_table)
    elements.append(Spacer(1, 6 * mm))

    # ── Items Table ───────────────────────────────────────────
    header = ["#", "Description", "Qty", "Unit Price", "Total"]
    table_data = [header]

    for i, item in enumerate(items_data, 1):
        table_data.append([
            str(i),
            item.get("description", ""),
            str(item.get("quantity", 1)),
            f"₹{item.get('unit_price', 0):,.2f}",
            f"₹{item.get('total', 0):,.2f}",
        ])

    items_table = Table(
        table_data,
        colWidths=["8%", "42%", "10%", "20%", "20%"],
        repeatRows=1,
    )
    items_table.setStyle(TableStyle([
        # Header
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4f46e5")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        # Body
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        # Alternating rows
        *[
            ("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f8fafc"))
            for i in range(2, len(table_data), 2)
        ],
        # Grid
        ("LINEBELOW", (0, 0), (-1, 0), 1, colors.HexColor("#4f46e5")),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 4 * mm))

    # ── Totals ────────────────────────────────────────────────
    currency = tenant_data.get("currency", "INR")
    symbol = "₹" if currency == "INR" else currency

    totals_data = [
        ["Subtotal", f"{symbol}{bill_data.get('subtotal', 0):,.2f}"],
    ]
    if float(bill_data.get("discount_percent", 0)) > 0:
        totals_data.append([
            f"Discount ({bill_data['discount_percent']}%)",
            f"- {symbol}{bill_data.get('discount_amount', 0):,.2f}",
        ])
    if float(bill_data.get("tax_percent", 0)) > 0:
        totals_data.append([
            f"GST ({bill_data['tax_percent']}%)",
            f"{symbol}{bill_data.get('tax_amount', 0):,.2f}",
        ])
    totals_data.append(["TOTAL", f"{symbol}{bill_data.get('total', 0):,.2f}"])

    totals_table = Table(totals_data, colWidths=["70%", "30%"])
    totals_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        # Total row bold
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, -1), (-1, -1), 12),
        ("LINEABOVE", (0, -1), (-1, -1), 1.5, colors.HexColor("#4f46e5")),
        ("TOPPADDING", (0, -1), (-1, -1), 8),
    ]))
    elements.append(totals_table)

    # ── Notes ─────────────────────────────────────────────────
    if bill_data.get("notes"):
        elements.append(Spacer(1, 6 * mm))
        elements.append(Paragraph("Notes", styles["SectionLabel"]))
        elements.append(Paragraph(bill_data["notes"], styles["SectionValue"]))

    # ── Footer ────────────────────────────────────────────────
    elements.append(Spacer(1, 10 * mm))
    elements.append(HRFlowable(
        width="100%", thickness=0.5,
        color=colors.HexColor("#e2e8f0"),
        spaceBefore=4, spaceAfter=4,
    ))
    elements.append(Paragraph("Thank you for choosing our services!", styles["FooterText"]))
    elements.append(Paragraph("This is a computer-generated invoice.", styles["FooterText"]))

    # Build PDF
    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    # Save to file if path given
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

    return pdf_bytes
