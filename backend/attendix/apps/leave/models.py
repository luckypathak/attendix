from django.db import models
from django.conf import settings
from attendix.apps.company.models import Company, SoftDeleteModel


class LeaveCategory(SoftDeleteModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='leave_categories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('company', 'name')

    def __str__(self):
        return f"{self.name} ({self.company.name})"


class LeaveRequest(SoftDeleteModel):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected')
    ]

    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='leave_requests'
    )
    leave_type = models.CharField(max_length=100) # Dynamic category string
    start_date = models.DateField()
    end_date = models.DateField()
    is_paid = models.BooleanField(default=True) # Decided by admin during approval
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    reason = models.TextField()
    manager_comments = models.TextField(blank=True, null=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_leaves'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee.username} - {self.leave_type} ({self.start_date} to {self.end_date})"


class LeaveBalance(SoftDeleteModel):
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='leave_balances'
    )
    leave_type = models.CharField(max_length=100)
    allocated = models.IntegerField(default=12)
    used = models.IntegerField(default=0)
    
    @property
    def remaining(self):
        return self.allocated - self.used

    class Meta:
        unique_together = ('employee', 'leave_type')

    def __str__(self):
        return f"{self.employee.username} - {self.leave_type} ({self.remaining} left)"


class Holiday(SoftDeleteModel):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='holidays'
    )
    date = models.DateField()
    name = models.CharField(max_length=100)
    is_paid = models.BooleanField(default=True)

    class Meta:
        unique_together = ('company', 'date')
        ordering = ['date']

    def __str__(self):
        return f"{self.name} on {self.date}"
