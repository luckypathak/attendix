import re

with open("../frontend/src/pages/Attendance.jsx", "r") as f:
    content = f.read()

old_edit = """                                                const sessWithParentStatus = { ...sess, parent_status: empRec.status };"""
new_edit = """                                                const sessWithParentStatus = { ...sess, parent_status: empRec.status, employee_name: empRec.employee_name };"""

content = content.replace(old_edit, new_edit)

with open("../frontend/src/pages/Attendance.jsx", "w") as f:
    f.write(content)

