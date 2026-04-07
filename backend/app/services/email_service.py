"""
Email notification service using SMTP.
Sends registration confirmations and bill receipts.
"""

from __future__ import annotations

import asyncio
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import aiosmtplib
from jinja2 import Template
from loguru import logger

from app.core.config import get_settings

settings = get_settings()


async def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    attachment: Optional[bytes] = None,
    attachment_name: Optional[str] = None,
) -> bool:
    """
    Send an email via SMTP. Returns True on success.
    Non-blocking — runs in background if email is configured.
    """
    if not settings.email_enabled:
        logger.warning("Email not configured. Skipping email to {}", to_email)
        return False

    try:
        msg = MIMEMultipart()
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(html_body, "html"))

        # Attach PDF if provided
        if attachment and attachment_name:
            pdf_part = MIMEApplication(attachment, _subtype="pdf")
            pdf_part.add_header(
                "Content-Disposition", "attachment", filename=attachment_name
            )
            msg.attach(pdf_part)

        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            use_tls=settings.SMTP_TLS,
        )

        logger.info("Email sent successfully to {}", to_email)
        return True

    except Exception as e:
        logger.error("Failed to send email to {}: {}", to_email, str(e))
        return False


async def send_welcome_email(clinic_name: str, admin_name: str, admin_email: str) -> bool:
    """Send welcome email after clinic registration."""
    template = Template("""
    <div style="font-family: 'Inter', Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 32px;">
        <div style="background: linear-gradient(135deg, #4f46e5, #7c3aed); padding: 32px; border-radius: 16px 16px 0 0; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 24px;">Welcome to Hospital Billing System</h1>
        </div>
        <div style="background: #ffffff; padding: 32px; border: 1px solid #e2e8f0; border-top: none; border-radius: 0 0 16px 16px;">
            <p style="color: #1e293b; font-size: 16px;">Hi <strong>{{ admin_name }}</strong>,</p>
            <p style="color: #475569; font-size: 14px; line-height: 1.6;">
                Your clinic <strong>{{ clinic_name }}</strong> has been successfully registered!
                You can now start managing patients, doctors, tests, and billing.
            </p>
            <div style="background: #f8fafc; border-radius: 12px; padding: 20px; margin: 24px 0;">
                <p style="color: #64748b; font-size: 12px; margin: 0 0 8px 0;">QUICK START</p>
                <ul style="color: #475569; font-size: 14px; line-height: 2;">
                    <li>Add your clinic logo and details in Settings</li>
                    <li>Register doctors and their consultation fees</li>
                    <li>Add medical tests and services</li>
                    <li>Start creating bills for patients</li>
                </ul>
            </div>
            <p style="color: #94a3b8; font-size: 12px;">
                If you did not create this account, please ignore this email.
            </p>
        </div>
    </div>
    """)

    html_body = template.render(admin_name=admin_name, clinic_name=clinic_name)
    return await send_email(admin_email, f"Welcome to {clinic_name} — Hospital Billing", html_body)


async def send_bill_receipt_email(
    patient_email: str,
    patient_name: str,
    clinic_name: str,
    bill_number: str,
    total: float,
    currency: str,
    pdf_bytes: Optional[bytes] = None,
) -> bool:
    """Send bill receipt email with PDF attachment."""
    symbol = "₹" if currency == "INR" else currency

    template = Template("""
    <div style="font-family: 'Inter', Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 32px;">
        <div style="background: linear-gradient(135deg, #4f46e5, #7c3aed); padding: 32px; border-radius: 16px 16px 0 0; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 24px;">Payment Receipt</h1>
            <p style="color: #c7d2fe; margin: 8px 0 0 0;">{{ clinic_name }}</p>
        </div>
        <div style="background: #ffffff; padding: 32px; border: 1px solid #e2e8f0; border-top: none; border-radius: 0 0 16px 16px;">
            <p style="color: #1e293b; font-size: 16px;">Dear <strong>{{ patient_name }}</strong>,</p>
            <p style="color: #475569; font-size: 14px; line-height: 1.6;">
                Please find your payment receipt attached. Here are the details:
            </p>
            <div style="background: #f8fafc; border-radius: 12px; padding: 20px; margin: 24px 0; text-align: center;">
                <p style="color: #64748b; font-size: 12px; margin: 0;">Invoice Number</p>
                <p style="color: #1e293b; font-size: 18px; font-weight: bold; margin: 4px 0;">{{ bill_number }}</p>
                <p style="color: #64748b; font-size: 12px; margin: 16px 0 0 0;">Amount Paid</p>
                <p style="color: #4f46e5; font-size: 28px; font-weight: bold; margin: 4px 0;">{{ symbol }}{{ total }}</p>
            </div>
            <p style="color: #94a3b8; font-size: 12px; text-align: center;">
                Thank you for choosing {{ clinic_name }}!
            </p>
        </div>
    </div>
    """)

    html_body = template.render(
        patient_name=patient_name,
        clinic_name=clinic_name,
        bill_number=bill_number,
        total=f"{total:,.2f}",
        symbol=symbol,
    )

    return await send_email(
        patient_email,
        f"Payment Receipt — {bill_number} | {clinic_name}",
        html_body,
        attachment=pdf_bytes,
        attachment_name=f"{bill_number}.pdf",
    )
