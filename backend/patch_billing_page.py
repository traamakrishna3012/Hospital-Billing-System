"""Patch BillingPage.jsx: fix logo URL, remove brackets, Rs. currency, Total Bill, print=download"""
import re

path = r"d:\Freelance\Hospital Bill System\frontend\src\pages\BillingPage.jsx"
with open(path, encoding='utf-8') as f:
    src = f.read()

# 1. Logo img src: use full backend URL (logo_url is a relative path like uploads/logos/...)
src = src.replace(
    """<img src={clinicProfile.logo_url} alt="Logo" className="h-24 w-auto object-contain p-1 border border-black mb-4" />""",
    """<img
                            src={`${(import.meta.env.VITE_API_BASE_URL || 'https://hospital-billing-system-pccq.onrender.com/api/v1').replace('/api/v1', '')}/${clinicProfile.logo_url}`}
                            alt="Logo"
                            className="h-20 w-auto object-contain mb-4"
                            onError={(e) => { e.target.style.display='none'; }}
                          />"""
)

# 2. Logo placeholder size
src = src.replace(
    """<div className="w-32 h-32 bg-[#e6eff6] border border-black flex items-center justify-center text-center font-bold text-lg mb-4">""",
    """<div className="w-28 h-20 bg-[#e6eff6] border border-gray-400 flex items-center justify-center text-center font-bold text-sm mb-4">"""
)

# 3. Remove brackets from institution info 
src = src.replace(
    """<p className="text-sm font-semibold">[ {clinicProfile?.name || 'Medical Institution Name'} ]</p>""",
    """<p className="text-sm font-semibold">{clinicProfile?.name || 'Medical Institution Name'}</p>"""
)
src = src.replace(
    """<p className="text-xs text-gray-600">[ {clinicProfile?.address || 'Medical Institution Address'} ]</p>""",
    """<p className="text-xs text-gray-600">{clinicProfile?.address || 'Medical Institution Address'}</p>"""
)
src = src.replace(
    """<p className="text-xs text-gray-600">[ {clinicProfile?.email || 'Medical Institution Email'} ]</p>""",
    """<p className="text-xs text-gray-600">{clinicProfile?.email || 'Medical Institution Email'}</p>"""
)
src = src.replace(
    """<p className="text-xs text-gray-600">[ {clinicProfile?.phone || 'Medical Institution Contact No.'} ]</p>""",
    """<p className="text-xs text-gray-600">{clinicProfile?.phone || 'Medical Institution Contact No.'}</p>"""
)

# 4. Remove brackets from patient block
src = src.replace(
    """<p>[ {selectedBill.patient?.name || 'Customer Name'} ]</p>""",
    """<p>{selectedBill.patient?.name || 'Customer Name'}</p>"""
)
src = src.replace(
    """<p>[ {selectedBill.patient?.address || 'Customer Address'} ]</p>""",
    """<p>{selectedBill.patient?.address || 'Customer Address'}</p>"""
)
src = src.replace(
    """<p>[ {selectedBill.patient?.email || 'Customer Email'} ]</p>""",
    """<p>{selectedBill.patient?.email || 'Customer Email'}</p>"""
)
src = src.replace(
    """<p>[ {selectedBill.patient?.phone || 'Customer Contact No.'} ]</p>""",
    """<p>{selectedBill.patient?.phone || 'Customer Contact No.'}</p>"""
)

# 5. Remove brackets from doctor block
src = src.replace(
    """<p>[ {selectedBill.doctor?.name ? `Dr. ${selectedBill.doctor.name}` : 'Practitioner Name'} ]</p>""",
    """<p>{selectedBill.doctor?.name ? `Dr. ${selectedBill.doctor.name}` : 'Practitioner Name'}</p>"""
)
src = src.replace(
    """<p>[ {selectedBill.doctor?.id?.slice(0,8).toUpperCase() || 'Practitioner License'} ]</p>""",
    """<p>{selectedBill.doctor?.license_number || selectedBill.doctor?.id?.slice(0,8).toUpperCase() || 'Practitioner License'}</p>"""
)
src = src.replace(
    """<p>[ {selectedBill.doctor?.specialization || 'Practitioner Title'} ]</p>""",
    """<p>{selectedBill.doctor?.specialization || 'Practitioner Title'}</p>"""
)

# 6. Rs. for price columns in table rows
src = src.replace(
    """<td className="p-2 border-r border-gray-300">{item.unit_price ? Number(item.unit_price).toFixed(2) : ''}</td>""",
    """<td className="p-2 border-r border-gray-300">{item.unit_price ? `Rs. ${Number(item.unit_price).toFixed(2)}` : ''}</td>"""
)
src = src.replace(
    """<td className="p-2">{item.total ? Number(item.total).toFixed(2) : ''}</td>""",
    """<td className="p-2">{item.total ? `Rs. ${Number(item.total).toFixed(2)}` : ''}</td>"""
)

# 7. Rs. for totals in financial rows
src = src.replace(
    """<div className="border-b border-gray-400 min-w-24 pb-0.5">{Number(selectedBill.subtotal || 0).toFixed(2)}</div>""",
    """<div className="border-b border-gray-400 min-w-24 pb-0.5">Rs. {Number(selectedBill.subtotal || 0).toFixed(2)}</div>"""
)
src = src.replace(
    """<div className="border-b border-gray-400 min-w-24 pb-0.5">{Number(selectedBill.discount_amount || 0).toFixed(2)}</div>""",
    """<div className="border-b border-gray-400 min-w-24 pb-0.5">Rs. {Number(selectedBill.discount_amount || 0).toFixed(2)}</div>"""
)
src = src.replace(
    """<div className="border-b border-gray-400 min-w-24 pb-0.5">{(Number(selectedBill.subtotal) - Number(selectedBill.discount_amount)).toFixed(2)}</div>""",
    """<div className="border-b border-gray-400 min-w-24 pb-0.5">Rs. {(Number(selectedBill.subtotal) - Number(selectedBill.discount_amount)).toFixed(2)}</div>"""
)
src = src.replace(
    """<div className="border-b border-gray-400 min-w-24 pb-0.5">{Number(selectedBill.tax_amount || 0).toFixed(2)}</div>""",
    """<div className="border-b border-gray-400 min-w-24 pb-0.5">Rs. {Number(selectedBill.tax_amount || 0).toFixed(2)}</div>"""
)

# 8. "Balance Due ₹" → "Total Bill" with Rs.
src = src.replace(
    """<span>Balance Due <span className="font-sans">\u20b9</span></span>
                           <span className="font-sans">{selectedBill.status === 'paid' ? '0.00' : Number(selectedBill.total || 0).toFixed(2)}</span>""",
    """<span>Total Bill</span>
                           <span>Rs. {Number(selectedBill.total || 0).toFixed(2)}</span>"""
)

# 9. Payment checkboxes: replace bullet format with [X]/[ ] style and add notes
src = src.replace(
    """<p className="mb-6 border-b border-gray-400 w-48">Notes</p>
                       <p className="pl-4 mb-2">Payment by:</p>
                       <ul className="space-y-1">
                         <li>\u2022 Cash {selectedBill.payment_mode === 'cash' ? '( \u2713 )' : ''}</li>
                         <li>\u2022 Cheque with number <span className="border-b border-[#103463] inline-block w-24"></span></li>
                         <li>\u2022 Credit card {selectedBill.payment_mode === 'card' ? '( \u2713 )' : ''}</li>
                         <li>\u2022 Insurance [ {selectedBill.payment_mode === 'insurance' ? '\u2713' : '      '} ]</li>
                         <li>\u2022 Others <span className="border-b border-[#103463] inline-block w-24">{['upi','online'].includes(selectedBill.payment_mode) ? selectedBill.payment_mode.toUpperCase() : ''}</span></li>
                       </ul>""",
    """<p className="font-bold mb-1">Notes</p>
                       <p className="border-b border-gray-300 w-48 mb-4 pb-1 text-xs text-gray-500">{selectedBill.notes || '\u2014'}</p>
                       <p className="font-bold mb-2">Payment by:</p>
                       <ul className="space-y-1">
                         <li>{selectedBill.payment_mode === 'cash' ? '[X]' : '[ ]'} Cash</li>
                         <li>{selectedBill.payment_mode === 'cheque' ? '[X]' : '[ ]'} Cheque  No: ______________</li>
                         <li>{['card','credit card'].includes(selectedBill.payment_mode) ? '[X]' : '[ ]'} Credit Card</li>
                         <li>{selectedBill.payment_mode === 'insurance' ? '[X]' : '[ ]'} Insurance  Carrier: ______________</li>
                         <li>{['upi','online'].includes(selectedBill.payment_mode) ? '[X]' : '[ ]'} Others: {['upi','online'].includes(selectedBill.payment_mode) ? selectedBill.payment_mode.toUpperCase() : '______________'}</li>
                       </ul>"""
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(src)

print("Done patching BillingPage.jsx")
