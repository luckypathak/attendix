import re

with open("../frontend/src/pages/Employees.jsx", "r") as f:
    content = f.read()

old_chip = "`\${emp.shift_name} (\${emp.shift_start_time} - \${emp.shift_end_time})`"
new_chip = "emp.shift_name"

content = content.replace(old_chip, new_chip)

with open("../frontend/src/pages/Employees.jsx", "w") as f:
    f.write(content)
