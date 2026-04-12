"""
PDF receipt generation — matches Medical Receipt Template (Style 1).
Uses ReportLab with inline canvas drawing for pixel-perfect layout.
"""

from __future__ import annotations

import io
import os
import tempfile
import urllib.request
import urllib.error
from datetime import datetime
from io import BytesIO
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame,
    Table, TableStyle, Paragraph, Spacer, Image, HRFlowable, KeepTogether,
)
from reportlab.platypus.flowables import Flowable

# ── Colours matching the template ────────────────────────────────────────
BLUE_DARK  = colors.HexColor("#1A4882")   # header/footer band & table header
BLUE_MID   = colors.HexColor("#5B9BD5")   # thin divider lines below section titles
GREY_ROW   = colors.HexColor("#F2F2F2")   # alternating row fill
GREY_BAL   = colors.HexColor("#C0C0C0")   # Balance Due bar
LOGO_BG    = colors.HexColor("#DEEAF1")   # logo placeholder background
TEXT_DARK  = colors.HexColor("#1A1A2E")
TEXT_MID   = colors.HexColor("#444444")
TEXT_LIGHT = colors.HexColor("#666666")

PW, PH = A4   # 595.27, 841.89 pts
BAND_H = 28 * mm   # top/bottom blue band height
MARGIN = 18 * mm


# ─────────────────────────────────────────────────────────────────────────
# Canvas background (blue bands top and bottom)
# ─────────────────────────────────────────────────────────────────────────
def _draw_bands(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(BLUE_DARK)
    canvas.rect(0, PH - BAND_H, PW, BAND_H, fill=1, stroke=0)   # top
    canvas.rect(0, 0,              PW, BAND_H, fill=1, stroke=0)  # bottom
    canvas.restoreState()


# ─────────────────────────────────────────────────────────────────────────
# Style helpers
# ─────────────────────────────────────────────────────────────────────────
def _S(name, **kw):
    """Quick ParagraphStyle factory."""
    base = getSampleStyleSheet()["Normal"]
    return ParagraphStyle(name, parent=base, **kw)


# ─────────────────────────────────────────────────────────────────────────
# Logo helper — supports local paths AND http(s) URLs
# ─────────────────────────────────────────────────────────────────────────
def _load_logo(logo_url: Optional[str], w=60*mm, h=20*mm):
    """Return an Image flowable or None."""
    if not logo_url:
        return None

    # Local path
    if os.path.exists(logo_url):
        try:
            return Image(logo_url, width=w, height=h)
        except Exception:
            return None

    # HTTP/HTTPS URL
    if logo_url.startswith("http://") or logo_url.startswith("https://"):
        try:
            req = urllib.request.Request(logo_url, headers={"User-Agent": "Mozilla/5.0"})
            data = urllib.request.urlopen(req, timeout=5).read()
            buf = BytesIO(data)
            return Image(buf, width=w, height=h)
        except Exception:
            return None

    return None


# ─────────────────────────────────────────────────────────────────────────
# Checkbox helper (draws ☑ / ☐ using canvas)
# ─────────────────────────────────────────────────────────────────────────
def _cb(checked: bool, label: str, extra: str = "") -> str:
    tick = "&#x2611;" if checked else "&#x2610;"
    suffix = f" <u>{extra}</u>" if extra else ""
    return f"{tick} {label}{suffix}"


# ─────────────────────────────────────────────────────────────────────────
# Main generator
# ─────────────────────────────────────────────────────────────────────────
def generate_receipt_pdf(
    bill_data: dict,
    tenant_data: dict,
    patient_data: dict,
    doctor_data: Optional[dict],
    items_data: list[dict],
    output_path: Optional[str] = None,
) -> bytes:
    """
    Generate a PDF receipt matching the Medical Receipt Template (Style 1).
    Returns raw PDF bytes.
    """
    buffer = BytesIO()

    # Page setup — leave room for blue bands
    frame = Frame(
        MARGIN, BAND_H + 5*mm,
        PW - 2*MARGIN, PH - 2*BAND_H - 10*mm,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
    )
    tpl = PageTemplate(id="receipt", frames=[frame], onPage=_draw_bands)
    doc = BaseDocTemplate(buffer, pagesize=A4, pageTemplates=[tpl])

    els = []   # flowables list
    PAGE_W = PW - 2*MARGIN   # usable width in points

    # ── 1. HEADER ────────────────────────────────────────────────────────
    # Left: logo + institution details   |   Right: RECEIPT title + date/no

    logo_img = _load_logo(tenant_data.get("logo_url"), w=18*mm, h=18*mm)
    if logo_img:
        logo_cell = logo_img
    else:
        # Placeholder box
        logo_cell = Table(
            [[Paragraph("<b>YOUR<br/>LOGO</b>",
                        _S("LP", fontSize=7, alignment=TA_CENTER, textColor=TEXT_MID))]],
            colWidths=[18*mm], rowHeights=[18*mm],
        )
        logo_cell.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), LOGO_BG),
            ("BOX",        (0,0), (-1,-1), 0.8, colors.HexColor("#90A8BE")),
            ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
            ("ALIGN",      (0,0), (-1,-1), "CENTER"),
        ]))

    inst_name  = tenant_data.get("name")  or "[ Medical Institution Name ]"
    inst_addr  = tenant_data.get("address") or "[ Medical Institution Address ]"
    inst_email = tenant_data.get("email")  or "[ Medical Institution Email ]"
    inst_phone = tenant_data.get("phone")  or "[ Medical Institution Contact No. ]"

    inst_details = [
        logo_cell,
        Spacer(1, 2*mm),
        Paragraph(inst_name,  _S("IN",  fontSize=10, fontName="Helvetica-Bold",  textColor=TEXT_DARK)),
        Paragraph(inst_addr,  _S("IA",  fontSize=8,  textColor=TEXT_LIGHT, leading=11)),
        Paragraph(inst_email, _S("IE",  fontSize=8,  textColor=TEXT_LIGHT, leading=11)),
        Paragraph(inst_phone, _S("IP",  fontSize=8,  textColor=TEXT_LIGHT, leading=11)),
    ]

    # Date formatting
    created_raw = bill_data.get("created_at", "")
    if isinstance(created_raw, datetime):
        date_str = created_raw.strftime("%d %B %Y")
    else:
        date_str = str(created_raw)[:10] if created_raw else ""

    bill_number = bill_data.get("bill_number", "")

    s_label = _S("HL",  fontSize=7, fontName="Helvetica-Bold",
                 textColor=BLUE_DARK, alignment=TA_RIGHT)
    s_val   = _S("HV",  fontSize=9,  textColor=TEXT_DARK, alignment=TA_RIGHT)

    right_header = [
        Paragraph("RECEIPT", _S("RT", fontSize=24, fontName="Helvetica-Bold",
                                 textColor=colors.HexColor("#AAAAAA"), alignment=TA_RIGHT)),
        Spacer(1, 3*mm),
        Paragraph("DATE",       s_label),
        HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey,
                   spaceBefore=1, spaceAfter=2),
        Paragraph(date_str,     s_val),
        Spacer(1, 2*mm),
        Paragraph("RECEIPT NO.", s_label),
        HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey,
                   spaceBefore=1, spaceAfter=2),
        Paragraph(bill_number,  s_val),
    ]

    LEFT_W  = PAGE_W * 0.52
    RIGHT_W = PAGE_W * 0.48

    header_tbl = Table([[inst_details, right_header]],
                       colWidths=[LEFT_W, RIGHT_W])
    header_tbl.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
    ]))
    els.append(header_tbl)
    els.append(Spacer(1, 5*mm))

    # ── 2. THIN DIVIDER ──────────────────────────────────────────────────
    els.append(HRFlowable(width="100%", thickness=0.8,
                          color=colors.HexColor("#CCCCCC"),
                          spaceBefore=0, spaceAfter=4*mm))

    # ── 3. PATIENT / PRACTITIONER COLUMNS ────────────────────────────────
    def _section_header(title):
        return [
            Paragraph(title, _S("SH", fontSize=8, fontName="Helvetica-Bold",
                                 textColor=BLUE_DARK)),
            HRFlowable(width="100%", thickness=1, color=BLUE_MID,
                       spaceBefore=1, spaceAfter=3),
        ]

    sv = _S("SV", fontSize=8, textColor=TEXT_MID, leading=12)

    p_name  = patient_data.get("name")  or "[ Customer Name ]"
    p_addr  = patient_data.get("address") or "[ Customer Address ]"
    p_email = patient_data.get("email") or "[ Customer Email ]"
    p_phone = patient_data.get("phone") or "[ Customer Contact No. ]"

    patient_col = (
        _section_header("Patient Information") +
        [
            Paragraph(f"[ {p_name} ]",  sv),
            Paragraph(f"[ {p_addr} ]",  sv),
            Paragraph(f"[ {p_email} ]", sv),
            Paragraph(f"[ {p_phone} ]", sv),
        ]
    )

    d_name  = f"Dr. {doctor_data['name']}"          if doctor_data else "[ Practitioner Name ]"
    d_lic   = doctor_data.get("license_number", "—") if doctor_data else "[ Practitioner License ]"
    d_title = doctor_data.get("specialization", "—") if doctor_data else "[ Practitioner Title ]"

    prac_col = (
        _section_header("Practitioner Information") +
        [
            Paragraph(f"[ {d_name} ]",  sv),
            Paragraph(f"[ {d_lic} ]",   sv),
            Paragraph(f"[ {d_title} ]", sv),
        ]
    )

    COL_W = PAGE_W * 0.48
    GAP_W = PAGE_W * 0.04
    pp_tbl = Table([[patient_col, Spacer(GAP_W, 1), prac_col]],
                   colWidths=[COL_W, GAP_W, COL_W])
    pp_tbl.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP")]))
    els.append(pp_tbl)
    els.append(Spacer(1, 5*mm))

    # ── 4. SERVICES TABLE ─────────────────────────────────────────────────
    th_s  = _S("TH",  fontSize=8, fontName="Helvetica-Bold",
                textColor=colors.white, alignment=TA_CENTER)
    th_sl = _S("THL", fontSize=8, fontName="Helvetica-Bold",
                textColor=colors.white, alignment=TA_LEFT)
    tb_c  = _S("TBC", fontSize=8, textColor=TEXT_MID, alignment=TA_CENTER)
    tb_l  = _S("TBL", fontSize=8, textColor=TEXT_MID, alignment=TA_LEFT)

    BLANK_ROWS = max(6, len(items_data) + 2)   # always at least 6 data rows

    tbl_data = [[
        Paragraph("Code",                            th_s),
        Paragraph("Description of Service / Treatment / Medicine", th_sl),
        Paragraph("Rate / Charge",                   th_s),
        Paragraph("Line Total",                      th_s),
    ]]

    for i in range(BLANK_ROWS):
        if i < len(items_data):
            it   = items_data[i]
            code = str(it.get("medical_test_id") or f"CST-{i+1:03d}")[:6].upper()
            tbl_data.append([
                Paragraph(code,                             tb_c),
                Paragraph(it.get("description", ""),        tb_l),
                Paragraph(f"\u20b9{float(it.get('unit_price', 0)):,.2f}", tb_c),
                Paragraph(f"\u20b9{float(it.get('total', 0)):,.2f}",      tb_c),
            ])
        else:
            tbl_data.append([Paragraph("", tb_c), Paragraph("", tb_l),
                              Paragraph("", tb_c), Paragraph("", tb_c)])

    C1 = PAGE_W * 0.14
    C2 = PAGE_W * 0.46
    C3 = PAGE_W * 0.20
    C4 = PAGE_W * 0.20

    svc_tbl = Table(tbl_data, colWidths=[C1, C2, C3, C4],
                    rowHeights=[8*mm] + [6.5*mm] * BLANK_ROWS)
    svc_ts  = [
        ("BACKGROUND", (0,0), (-1,0), BLUE_DARK),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("GRID",       (0,0), (-1,-1), 0.4, colors.HexColor("#CCCCCC")),
        ("TOPPADDING",    (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
    ]
    for r in range(2, len(tbl_data), 2):
        svc_ts.append(("BACKGROUND", (0,r), (-1,r), GREY_ROW))

    svc_tbl.setStyle(TableStyle(svc_ts))
    els.append(svc_tbl)
    els.append(Spacer(1, 5*mm))

    # ── 5 & 6. NOTES + PAYMENT  |  FINANCIAL SUMMARY ────────────────────
    pmode = str(bill_data.get("payment_mode", "")).lower()

    is_cash  = pmode == "cash"
    is_cheq  = pmode == "cheque"
    is_card  = pmode in ("card", "credit card")
    is_ins   = pmode == "insurance"
    is_upi   = pmode in ("upi", "online")

    def _tick(checked): return "[X]" if checked else "[ ]"

    note_sv = _S("NSV", fontSize=8, textColor=TEXT_MID, leading=13)
    notes_txt = bill_data.get("notes") or "—"

    notes_lines = [
        Paragraph("Notes", _S("NLB", fontSize=9, fontName="Helvetica-Bold",
                               textColor=TEXT_DARK)),
        HRFlowable(width="80%", thickness=0.5, color=colors.lightgrey,
                   spaceBefore=1, spaceAfter=3),
        Paragraph(notes_txt, note_sv),
        Spacer(1, 4*mm),
        Paragraph("Payment by:", _S("PBL", fontSize=8, fontName="Helvetica-Bold",
                                     textColor=TEXT_DARK)),
        Spacer(1, 2*mm),
        Paragraph(
            f"{_tick(is_cash)} Cash",
            note_sv),
        Paragraph(
            f"{_tick(is_cheq)} Cheque  No: {'______________' if not is_cheq else bill_data.get('cheque_number','______________')}",
            note_sv),
        Paragraph(
            f"{_tick(is_card)} Credit Card",
            note_sv),
        Paragraph(
            f"{_tick(is_ins)} Insurance  Carrier: {'______________' if not is_ins else ''}",
            note_sv),
        Paragraph(
            f"{_tick(is_upi)} Others: {'UPI / Online' if is_upi else '______________'}",
            note_sv),
    ]

    # Financials
    subt = float(bill_data.get("subtotal", 0))
    disc = float(bill_data.get("discount_amount", 0))
    tax_p = float(bill_data.get("tax_percent", 0))
    tax_v = float(bill_data.get("tax_amount", 0))
    total = float(bill_data.get("total", 0))
    balance = 0.0 if str(bill_data.get("status", "")).lower() == "paid" else total

    fl = _S("FL", fontSize=7, fontName="Helvetica-Bold",
             textColor=BLUE_DARK, alignment=TA_RIGHT)
    fv = _S("FV", fontSize=8, textColor=TEXT_DARK, alignment=TA_RIGHT)

    fin_rows = [
        [Paragraph("SUBTOTAL",              fl), Paragraph(f"\u20b9{subt:,.2f}",         fv)],
        [Paragraph("DISCOUNT",              fl), Paragraph(f"\u20b9{disc:,.2f}",         fv)],
        [Paragraph("SUBTOTAL LESS DISCOUNT",fl), Paragraph(f"\u20b9{subt - disc:,.2f}",  fv)],
        [Paragraph("TAX RATE",              fl), Paragraph(f"{tax_p:.2f}%",              fv)],
        [Paragraph("TOTAL TAX",             fl), Paragraph(f"\u20b9{tax_v:,.2f}",        fv)],
    ]

    fin_tbl = Table(fin_rows, colWidths=["60%", "40%"])
    fin_tbl.setStyle(TableStyle([
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("LINEBELOW",     (1,0), (1,-1), 0.5, colors.lightgrey),
        ("TOPPADDING",    (0,0), (-1,-1), 2),
        ("BOTTOMPADDING", (0,0), (-1,-1), 2),
    ]))

    bal_l = _S("BL", fontSize=10, fontName="Helvetica-Bold", textColor=TEXT_DARK)
    bal_v = _S("BV", fontSize=11, fontName="Helvetica-Bold",
                textColor=TEXT_DARK, alignment=TA_RIGHT)

    bal_tbl = Table(
        [[Paragraph("Balance Due \u20b9", bal_l),
          Paragraph(f"{balance:,.2f}",    bal_v)]],
        colWidths=["55%", "45%"],
        rowHeights=[10*mm],
    )
    bal_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), GREY_BAL),
        ("BOX",        (0,0), (-1,-1), 0.8, colors.darkgrey),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING",  (0,0), (0,-1), 4),
        ("RIGHTPADDING", (1,0), (1,-1), 4),
    ]))

    right_fin = [fin_tbl, Spacer(1, 4*mm), bal_tbl]

    NOTES_W = PAGE_W * 0.52
    GAP2_W  = PAGE_W * 0.04
    FINS_W  = PAGE_W * 0.44

    footer_tbl = Table(
        [[notes_lines, Spacer(GAP2_W, 1), right_fin]],
        colWidths=[NOTES_W, GAP2_W, FINS_W],
    )
    footer_tbl.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP")]))
    els.append(KeepTogether(footer_tbl))

    # ── BUILD ─────────────────────────────────────────────────────────────
    doc.build(els)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    if output_path:
        parent = os.path.dirname(output_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

    return pdf_bytes
