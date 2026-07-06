from django.db import models
from django.conf import settings
from attendix.apps.company.models import SoftDeleteModel


class Notification(SoftDeleteModel):
    TYPES = [
        ('PUSH', 'FCM Push Notification'),
        ('SMS', 'SMS Text Message'),
        ('IN_APP', 'In-App Notification')
    ]
    STATUSES = [
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('FAILED', 'Failed')
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=255)
    body = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPES, default='IN_APP')
    status = models.CharField(max_length=20, choices=STATUSES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.recipient.username} - {self.title} ({self.status})"


class SMSQueue(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Send'),
        ('SENT', 'Sent Successfully'),
        ('FAILED', 'Failed to Send')
    ]

    phone = models.CharField(max_length=20)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    retries = models.IntegerField(default=0)
    
    # Android Gateway specific fields
    sim_slot_used = models.IntegerField(null=True, blank=True) # 1 or 2
    error_message = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"SMS to {self.phone} - {self.status}"


class SMSGatewayDevice(models.Model):
    device_name = models.CharField(max_length=100)
    device_id = models.CharField(max_length=100, unique=True)
    api_key = models.CharField(max_length=255) # Custom security key for gateway verification
    
    # Active limits
    sim1_daily_limit = models.IntegerField(default=100)
    sim1_sent_today = models.IntegerField(default=0)
    sim2_daily_limit = models.IntegerField(default=100)
    sim2_sent_today = models.IntegerField(default=0)
    
    last_ping = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.device_name
