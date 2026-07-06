from django.contrib.auth.models import AbstractUser
from django.db import models
from attendix.apps.company.models import Company


class User(AbstractUser):
    class Roles(models.TextChoices):
        SUPER_ADMIN = 'SUPER_ADMIN', 'Super Admin'
        COMPANY_ADMIN = 'COMPANY_ADMIN', 'Company Admin'
        MANAGER = 'MANAGER', 'Manager'
        EMPLOYEE = 'EMPLOYEE', 'Employee'

    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.EMPLOYEE
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    firm = models.ForeignKey(
        'company.Firm',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)

    # Resolve reverse accessor collisions
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='attendix_users',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='attendix_user_permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.is_active = False
        self.save()

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
