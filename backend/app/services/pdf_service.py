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
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        "InstName", parent=styles["Normal"], fontSize=11, fontName="Helvetica-Bold", textColor=colors.HexColor("#1e293b"), spaceAfter=1
    ))
    styles.add(ParagraphStyle(
        "InstAddress", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#64748b"), leading=10
    ))
    styles.add(ParagraphStyle(
        "ReceiptTitle", parent=styles["Normal"], fontSize=22, fontName="Helvetica-Bold", textColor=colors.HexColor("#9ca3af"), spaceAfter=10, alignment=TA_RIGHT, rightIndent=10
    ))
    styles.add(ParagraphStyle(
        "SectionLabel", parent=styles["Normal"], fontSize=8, fontName="Helvetica-Bold", textColor=colors.HexColor("#103463"), spaceBefore=2
    ))
    styles.add(ParagraphStyle(
        "SectionValue", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#1e293b"), leading=12
    ))
    styles.add(ParagraphStyle(
        "TableHead", parent=styles["Normal"], fontSize=9, fontName="Helvetica-Bold", textColor=colors.white, alignment=TA_CENTER
    ))
    styles.add(ParagraphStyle(
        "TableBodyLeft", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#333333")
    ))
    styles.add(ParagraphStyle(
        "TableBodyCenter", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#333333"), alignment=TA_CENTER
    ))
    styles.add(ParagraphStyle(
        "NotesLabel", parent=styles["Normal"], fontSize=9, fontName="Helvetica-Bold", textColor=colors.HexColor("#333333"), spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        "SmallText", parent=styles["Normal"], fontSize=7, textColor=colors.HexColor("#333333")
    ))
    return styles

def draw_bg(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#7bb0db"))
    canvas.rect(0, A4[1] - 30*mm, A4[0], 30*mm, fill=1, stroke=0)
    canvas.rect(0, 0, A4[0], 30*mm, fill=1, stroke=0)
    canvas.restoreState()

def generate_receipt_pdf(
    bill_data: dict,
    tenant_data: dict,
    patient_data: dict,
    doctor_data: Optional[dict],
    items_data: list[dict],
    output_path: Optional[str] = None,
) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm,
        topMargin=35*mm, bottomMargin=35*mm
    )

    styles = _get_styles()
    elements = []

    # ── Header ─────────────────────────────────────────────
    # Logo Box
    logo_url = tenant_data.get("logo_url")
    logo_flowable = None
    if logo_url and os.path.exists(logo_url):
        try:
            logo_flowable = Image(logo_url, width=65, height=65)
        except:
            logo_flowable = Paragraph("<br/><br/>YOUR<br/>LOGO", ParagraphStyle("LG", parent=styles["Normal"], fontSize=10, fontName="Helvetica-Bold", alignment=TA_CENTER))
    else:
        logo_flowable = Paragraph("<br/><br/>YOUR<br/>LOGO", ParagraphStyle("LG", parent=styles["Normal"], fontSize=10, fontName="Helvetica-Bold", alignment=TA_CENTER))

    logo_table = Table([[logo_flowable]], colWidths=[65], rowHeights=[65])
    logo_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#e6eff6")),
        ("BOX", (0, 0), (0, 0), 1, colors.black),
        ("VALIGN", (0, 0), (0, 0), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "CENTER"),
    ]))

    inst_name = tenant_data.get("name", "Medical Institution Name")
    inst_info = [
        f"[{tenant_data.get('address') or 'Medical Institution Address'}]",
        f"[{tenant_data.get('email') or 'Medical Institution Email'}]",
        f"[{tenant_data.get('phone') or 'Medical Institution Contact No.'}]"
    ]
    
    left_info = [
        logo_table,
        Spacer(1, 4*mm),
        Paragraph(f"[ {inst_name} ]", styles["InstName"]),
        Paragraph("<br/>".join(inst_info), styles["InstAddress"]),
    ]

    created_at = bill_data.get("created_at", "")
    if isinstance(created_at, datetime):
        created_at = created_at.strftime("%d/%m/%Y")
        
    right_info = [
        Paragraph("RECEIPT", styles["ReceiptTitle"]),
        Spacer(1, 4*mm),
        Paragraph("DATE", ParagraphStyle("DL", parent=styles["SectionLabel"], alignment=TA_RIGHT, rightIndent=10)),
        HRFlowable(width="35%", thickness=0.5, color=colors.HexColor("#d1d5db"), hAlign="RIGHT", spaceBefore=2, spaceAfter=2),
        Paragraph(created_at, ParagraphStyle("DV", parent=styles["SectionValue"], alignment=TA_RIGHT, rightIndent=10)),
        Spacer(1, 4*mm),
        Paragraph("RECEIPT NO.", ParagraphStyle("DL", parent=styles["SectionLabel"], alignment=TA_RIGHT, rightIndent=10)),
        HRFlowable(width="35%", thickness=0.5, color=colors.HexColor("#d1d5db"), hAlign="RIGHT", spaceBefore=2, spaceAfter=2),
        Paragraph(bill_data.get('bill_number', ''), ParagraphStyle("DV", parent=styles["SectionValue"], alignment=TA_RIGHT, rightIndent=10)),
    ]

    header_table = Table([[left_info, right_info]], colWidths=["50%", "50%"])
    header_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    elements.append(header_table)
    elements.append(Spacer(1, 6*mm))

    # ── Patient / Practitioner ──────────────────────────────────────
    p_name = patient_data.get("name", "Customer Name")
    p_addr = patient_data.get("address") or "Customer Address"
    p_email = patient_data.get("email") or "Customer Email"
    p_phone = patient_data.get("phone", "Customer Contact No.")
    
    patient_block = [
        Paragraph("Patient Information", styles["SectionLabel"]),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#103463"), spaceBefore=2, spaceAfter=4),
        Paragraph(f"[ {p_name} ]", styles["SectionValue"]),
        Paragraph(f"[ {p_addr} ]", styles["SectionValue"]),
        Paragraph(f"[ {p_email} ]", styles["SectionValue"]),
        Paragraph(f"[ {p_phone} ]", styles["SectionValue"]),
    ]

    d_name = f"Dr. {doctor_data.get('name')}" if doctor_data else "Practitioner Name"
    d_lice = doctor_data.get("id", "Practitioner License") if doctor_data else "Practitioner License"
    if len(str(d_lice)) > 8: d_lice = str(d_lice)[:8].upper()
    d_title = doctor_data.get("specialization") or "Practitioner Title" if doctor_data else "Practitioner Title"

    doctor_block = [
        Paragraph("Practitioner Information", styles["SectionLabel"]),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#103463"), spaceBefore=2, spaceAfter=4),
        Paragraph(f"[ {d_name} ]", styles["SectionValue"]),
        Paragraph(f"[ {d_lice} ]", styles["SectionValue"]),
        Paragraph(f"[ {d_title} ]", styles["SectionValue"]),
    ]

    pp_table = Table([[patient_block, doctor_block]], colWidths=["48%", "48%"])
    # give some gap in the middle
    pp_table = Table([[patient_block, "", doctor_block]], colWidths=["45%", "10%", "45%"])
    pp_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    elements.append(pp_table)
    elements.append(Spacer(1, 8*mm))

    # ── Items Table ─────────────────────────────────────────────────
    th = styles["TableHead"]
    tb_l = styles["TableBodyLeft"]
    tb_c = styles["TableBodyCenter"]
    
    table_data = [
        [Paragraph("Code", th), Paragraph("Description of Service/Treatment/Medicine", ParagraphStyle("THL", parent=th, alignment=TA_LEFT)), Paragraph("Rate / Charge", th), Paragraph("Line total", th)]
    ]

    for i in range(max(len(items_data), 5)):
        if i < len(items_data):
            it = items_data[i]
            code = str(it.get('medical_test_id') or f"CST-{i+1}")[:6].upper()
            table_data.append([
                Paragraph(code, tb_c),
                Paragraph(it.get('description', ''), tb_l),
                Paragraph(f"{float(it.get('unit_price', 0)):.2f}", tb_c),
                Paragraph(f"{float(it.get('total', 0)):.2f}", tb_c),
            ])
        else:
            table_data.append([Paragraph("", tb_c), Paragraph("", tb_l), Paragraph("", tb_c), Paragraph("", tb_c)])

    t = Table(table_data, colWidths=["15%", "50%", "17.5%", "17.5%"])
    t_styles = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#103463")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
    ]
    for i in range(1, len(table_data)):
        t_styles.append(("BOTTOMPADDING", (0, i), (-1, i), 6))
        t_styles.append(("TOPPADDING", (0, i), (-1, i), 6))
        if i % 2 == 0:
            t_styles.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f2f2f2")))
            
    t.setStyle(TableStyle(t_styles))
    elements.append(t)
    elements.append(Spacer(1, 8*mm))

    # ── Footer Totals ───────────────────────────────────────────────
    pmode = str(bill_data.get('payment_mode', '')).lower()
    ch_cash = "( ✓ )" if pmode == "cash" else ""
    ch_card = "( ✓ )" if pmode == "card" else ""
    ch_ins = "✓" if pmode == "insurance" else "      "
    ch_oth_val = pmode.upper() if pmode in ["upi", "online"] else ""
    ch_oth = f"<u>  {ch_oth_val}  </u>" if ch_oth_val else "_________"

    notes_block = [
        Paragraph("Notes", styles["NotesLabel"]),
        HRFlowable(width="60%", thickness=0.5, color=colors.HexColor("#9ca3af"), spaceBefore=1, spaceAfter=4, hAlign="LEFT"),
        Paragraph("Payment by:", styles["SmallText"]),
        Paragraph(f"• Cash {ch_cash}", styles["SmallText"]),
        Paragraph("• Cheque with number <u>                </u>", styles["SmallText"]),
        Paragraph(f"• Credit card {ch_card}", styles["SmallText"]),
        Paragraph(f"• Insurance [ {ch_ins} ]", styles["SmallText"]),
        Paragraph(f"• Others {ch_oth}", styles["SmallText"]),
    ]

    t_lbl = ParagraphStyle("TLBL", parent=styles["SectionLabel"], alignment=TA_RIGHT, fontSize=7)
    t_val = ParagraphStyle("TVAL", parent=styles["SectionValue"], alignment=TA_RIGHT, fontSize=8)
    
    subt = float(bill_data.get('subtotal', 0))
    disc = float(bill_data.get('discount_amount', 0))
    tax_p = float(bill_data.get('tax_percent', 0))
    tax_v = float(bill_data.get('tax_amount', 0))
    
    totals_data = [
        [Paragraph("SUBTOTAL", t_lbl), Paragraph(f"{subt:.2f}", t_val)],
        [Paragraph("DISCOUNT", t_lbl), Paragraph(f"{disc:.2f}", t_val)],
        [Paragraph("SUBTOTAL LESS DISCOUNT", t_lbl), Paragraph(f"{(subt-disc):.2f}", t_val)],
        [Paragraph("TAX RATE", t_lbl), Paragraph(f"{tax_p}%", t_val)],
        [Paragraph("TOTAL TAX", t_lbl), Paragraph(f"{tax_v:.2f}", t_val)],
    ]
    t_tot = Table(totals_data, colWidths=["60%", "40%"])
    t_tot.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("LINEBELOW", (1, 0), (1, -1), 0.5, colors.HexColor("#9ca3af")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
    ]))

    bal_amt = "0.00" if str(bill_data.get('status')).lower() == 'paid' else f"{float(bill_data.get('total', 0)):.2f}"
    bal_table = Table([[Paragraph("Balance Due ₹", ParagraphStyle("BAL", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=10)), 
                        Paragraph(bal_amt, ParagraphStyle("BALV", parent=styles["Normal"], alignment=TA_RIGHT, fontName="Helvetica-Bold", fontSize=10))]], colWidths=["50%", "50%"])
    bal_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#cccccc")),
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    right_footer = [t_tot, Spacer(1, 6*mm), bal_table]
    footer_table = Table([[notes_block, "", right_footer]], colWidths=["45%", "15%", "40%"])
    footer_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    elements.append(footer_table)

    # Build PDF
    doc.build(elements, onFirstPage=draw_bg, onLaterPages=draw_bg)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    # Save to file if path given
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

    return pdf_bytes
