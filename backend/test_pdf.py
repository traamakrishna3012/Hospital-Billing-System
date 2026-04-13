import os
import sys

# Setup django-like path
sys.path.insert(0, r"d:\Freelance\Hospital Bill System\backend")

from app.services.pdf_service import generate_receipt_pdf
from io import BytesIO

bill_data = {"bill_number": "INV-123", "created_at": "2026-04-12"}
tenant_data = {"name": "Test Clinic"}
patient_data = {"name": "Test Patient"}
items_data = [{"description": "Test Item", "quantity": 1, "unit_price": 100, "total": 100}]

try:
    pdf_bytes = generate_receipt_pdf(
        bill_data=bill_data,
        tenant_data=tenant_data,
        patient_data=patient_data,
        doctor_data=None,
        items_data=items_data
    )
    with open("test_receipt.pdf", "wb") as f:
        f.write(pdf_bytes)
    print("PDF generated successfully! Size:", len(pdf_bytes))
except Exception as e:
    import traceback
    print("Error generating PDF:", traceback.format_exc())
