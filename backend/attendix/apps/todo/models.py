from django.db import models
from django.conf import settings
from django.utils import timezone
from attendix.apps.company.models import SoftDeleteModel


class Todo(SoftDeleteModel):
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='todos'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)
    postpone_reason = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.is_completed and not self.completed_at:
            self.completed_at = timezone.now()
        elif not self.is_completed:
            self.completed_at = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee.username} - {self.title} (Done: {self.is_completed})"
