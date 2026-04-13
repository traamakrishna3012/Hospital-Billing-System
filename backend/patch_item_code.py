"""Patch BillingPage.jsx: send test code in payload, display item.code in print layout"""

path = r"d:\Freelance\Hospital Bill System\frontend\src\pages\BillingPage.jsx"
with open(path, encoding='utf-8') as f:
    src = f.read()

# 1. Auto-fill code from test when selected
old = """    // Auto-fill from test selection
    if (field === 'medical_test_id' && value) {
      const test = tests.find((t) => t.id === value);
      if (test) {
        newItems[index].description = test.name;
        newItems[index].unit_price = String(test.price);
      }
    }"""

new = """    // Auto-fill from test selection
    if (field === 'medical_test_id' && value) {
      const test = tests.find((t) => t.id === value);
      if (test) {
        newItems[index].description = test.name;
        newItems[index].unit_price = String(test.price);
        newItems[index].code = test.code || '';   // store the test's code
      }
    }"""

if old in src:
    src = src.replace(old, new)
    print("✓ Patched updateItem auto-fill")
else:
    print("✗ updateItem block not found")

# 2. Include code in payload sent to backend
old = """      items: billForm.items.map((item) => ({
        description: item.description,
        unit_price: parseFloat(item.unit_price),
        quantity: parseInt(item.quantity),
        medical_test_id: item.medical_test_id || null,
      })),"""

new = """      items: billForm.items.map((item) => ({
        description: item.description,
        code: item.code || null,
        unit_price: parseFloat(item.unit_price),
        quantity: parseInt(item.quantity),
        medical_test_id: item.medical_test_id || null,
      })),"""

if old in src:
    src = src.replace(old, new)
    print("✓ Patched payload items")
else:
    print("✗ payload items block not found")

# 3. In print layout table: use item.code instead of medical_test_id slice
old = """                         <td className="p-2 border-r border-gray-300 text-xs text-gray-500">{item.medical_test_id?.slice(0,6).toUpperCase() || (item.description ? `CST-${i+1}` : '')}</td>"""
new = """                         <td className="p-2 border-r border-gray-300 text-xs text-gray-500">{item.code || (item.description ? `CST-${i+1}` : '')}</td>"""

if old in src:
    src = src.replace(old, new)
    print("✓ Patched print layout code column")
else:
    print("✗ print layout code column not found")

# Also initialise code in addItem / default items
old = """items: [...billForm.items, { description: '', unit_price: '', quantity: 1, medical_test_id: '' }],"""
new = """items: [...billForm.items, { description: '', unit_price: '', quantity: 1, medical_test_id: '', code: '' }],"""
if old in src:
    src = src.replace(old, new)
    print("✓ Patched addItem default")
else:
    print("✗ addItem default not found")

old = """items: [{ description: '', unit_price: '', quantity: 1, medical_test_id: '' }],"""
new = """items: [{ description: '', unit_price: '', quantity: 1, medical_test_id: '', code: '' }],"""
if old in src:
    src = src.replace(old, new)
    print("✓ Patched initial item default")
else:
    print("✗ initial item default not found")

with open(path, 'w', encoding='utf-8') as f:
    f.write(src)

print("\nDone patching BillingPage.jsx")
