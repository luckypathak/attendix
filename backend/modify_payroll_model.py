import re

with open("../backend/attendix/apps/payroll/models.py", "r") as f:
    content = f.read()

new_fields = """    base_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    unpaid_leave_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    absent_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    advance_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    gross_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    pf_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    net_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)"""

content = re.sub(
    r"    base_salary = models.DecimalField\(max_digits=12, decimal_places=2, default=0.00\)\n    gross_salary = models.DecimalField\(max_digits=12, decimal_places=2, default=0.00\)\n    pf_deduction = models.DecimalField\(max_digits=10, decimal_places=2, default=0.00\)\n    net_salary = models.DecimalField\(max_digits=12, decimal_places=2, default=0.00\)",
    new_fields,
    content
)

with open("../backend/attendix/apps/payroll/models.py", "w") as f:
    f.write(content)
