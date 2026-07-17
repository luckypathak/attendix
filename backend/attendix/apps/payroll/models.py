from django.db import models
from django.conf import settings
from attendix.apps.company.models import SoftDeleteModel


class AdvanceSalary(SoftDeleteModel):
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='advance_salaries'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    request_date = models.DateField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending Approval'),
            ('APPROVED', 'Approved'),
            ('DISBURSED', 'Disbursed/Paid'),
            ('REJECTED', 'Rejected'),
            ('COMPLETED', 'Fully Repaid')
        ],
        default='PENDING'
    )
    monthly_deduction = models.DecimalField(max_digits=10, decimal_places=2)
    repaid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_advances'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def remaining_amount(self):
        import decimal
        return decimal.Decimal(str(self.amount)) - decimal.Decimal(str(self.repaid_amount))

    def __str__(self):
        return f"{self.employee.username} - {self.amount} (Repaid: {self.repaid_amount})"


class Payroll(SoftDeleteModel):
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payrolls'
    )
    month = models.IntegerField()  # 1 to 12
    year = models.IntegerField()
    
    # Salary components
    base_salary = models.DecimalField(max_digits=12, decimal_places=2)
    worked_days = models.IntegerField(default=0)
    absent_days = models.IntegerField(default=0)
    unpaid_leaves = models.IntegerField(default=0)
    
    # Additions
    overtime_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    overtime_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Deductions
    advance_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    unpaid_leave_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    absent_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    pf_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    already_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    gross_salary = models.DecimalField(max_digits=12, decimal_places=2)
    net_salary = models.DecimalField(max_digits=12, decimal_places=2)
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('DRAFT', 'Draft'),
            ('APPROVED', 'Approved'),
            ('PAID', 'Paid')
        ],
        default='DRAFT'
    )
    
    payslip_pdf_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('employee', 'month', 'year')

    def __str__(self):
        return f"{self.employee.username} - {self.month}/{self.year} - Net: {self.net_salary}"


class PayrollBranchBreakdown(SoftDeleteModel):
    payroll = models.ForeignKey(
        Payroll,
        on_delete=models.CASCADE,
        related_name='branch_distributions'
    )
    firm = models.ForeignKey(
        'company.Firm',
        on_delete=models.CASCADE,
        related_name='payroll_distributions'
    )
    base_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    gross_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    pf_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    net_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('payroll', 'firm')

    def __str__(self):
        return f"Payroll Split for {self.payroll.employee.username} at {self.firm.name} ({self.payroll.month}/{self.payroll.year})"

