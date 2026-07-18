from django.db import models


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False)
    
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.save()


class Company(SoftDeleteModel):
    name = models.CharField(max_length=255)
    logo_url = models.URLField(blank=True, null=True)
    domain = models.CharField(max_length=100, unique=True, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)    
    # Company settings
    grace_period_minutes = models.IntegerField(default=15)
    late_limit_for_half_day = models.IntegerField(default=3)
    auto_checkout_hours = models.DecimalField(max_digits=4, decimal_places=2, default=10.00) # Auto checkout if forgot
    
    # Location tracking settings
    office_radius_meters = models.IntegerField(default=100)
    location_update_frequency_minutes = models.IntegerField(default=5)
    geofence_grace_period_minutes = models.IntegerField(default=5)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Department(SoftDeleteModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('company', 'name')

    def __str__(self):
        return f"{self.name} ({self.company.name})"


class Designation(SoftDeleteModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='designations')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('company', 'name')

    def __str__(self):
        return f"{self.name} ({self.company.name})"


class Firm(SoftDeleteModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='firms')
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('company', 'name')

    def __str__(self):
        return f"{self.name} ({self.company.name})"
