from django.db import models
from django.conf import settings
from attendix.apps.company.models import Department, Designation, SoftDeleteModel


class EmployeeProfile(SoftDeleteModel):
    WORK_CATEGORY_CHOICES = [
        ('OFFICE', 'Office Staff'),
        ('FIELD', 'Field Staff')
    ]
    
    work_category = models.CharField(
        max_length=20,
        choices=WORK_CATEGORY_CHOICES,
        default='OFFICE'
    )
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='employee_profile'
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees'
    )
    designation = models.ForeignKey(
        Designation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees'
    )
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subordinates'
    )
    
    # Financial details
    base_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    checkout_missed_count = models.IntegerField(default=0)
    
    shift = models.ForeignKey(
        'attendance.Shift',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employee_profiles'
    )
    pf_deduction = models.BooleanField(default=False)
    pf_type = models.CharField(
        max_length=20,
        choices=[('percentage', 'Percentage'), ('flat', 'Flat Amount'), ('disabled', 'Disabled')],
        default='disabled'
    )
    pf_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    allowed_leaves = models.IntegerField(default=12)
    used_leaves = models.IntegerField(default=0)

    # Personal & HR details
    joining_date = models.DateField(null=True, blank=True)
    pan_number = models.CharField(max_length=20, blank=True, null=True)
    bank_account_no = models.CharField(max_length=30, blank=True, null=True)
    bank_ifsc_code = models.CharField(max_length=20, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.base_salary and self.shift:
            # Shift duration in hours
            shift_hours = self.shift.duration_hours
            import decimal
            self.hourly_rate = round(decimal.Decimal(self.base_salary) / decimal.Decimal(22 * shift_hours), 2)
        elif self.base_salary:
            import decimal
            self.hourly_rate = round(decimal.Decimal(self.base_salary) / decimal.Decimal('176'), 2)
        else:
            self.hourly_rate = 0.00
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Profile of {self.user.username}"


class EmployeeFirmAllocation(SoftDeleteModel):
    employee_profile = models.ForeignKey(
        EmployeeProfile,
        on_delete=models.CASCADE,
        related_name='firm_allocations'
    )
    firm = models.ForeignKey(
        'company.Firm',
        on_delete=models.CASCADE,
        related_name='employee_allocations'
    )
    base_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    pf_type = models.CharField(
        max_length=20,
        choices=[('percentage', 'Percentage'), ('flat', 'Flat Amount'), ('disabled', 'Disabled')],
        default='disabled'
    )
    pf_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('employee_profile', 'firm')

    def __str__(self):
        return f"{self.employee_profile.user.username} Allocation at {self.firm.name}"

