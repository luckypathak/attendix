from django.db import models
from django.conf import settings
from attendix.apps.company.models import SoftDeleteModel


class Reimbursement(SoftDeleteModel):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected')
    ]

    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reimbursements'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    receipt_url = models.URLField(blank=True, null=True) # Cloudinary storage path
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    manager_comments = models.TextField(blank=True, null=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_reimbursements'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee.username} - {self.title} ({self.amount})"
