from django.db import models
from django.conf import settings
from attendix.apps.company.models import Company, SoftDeleteModel


class Shift(SoftDeleteModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='shifts')
    name = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    grace_period_minutes = models.IntegerField(default=15)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.start_time} - {self.end_time})"

    @property
    def duration_hours(self):
        import datetime
        start_dt = datetime.datetime.combine(datetime.date.today(), self.start_time)
        end_dt = datetime.datetime.combine(datetime.date.today(), self.end_time)
        if end_dt < start_dt:
            # Shift crosses midnight
            end_dt += datetime.timedelta(days=1)
        diff = end_dt - start_dt
        return diff.total_seconds() / 3600.0


class Attendance(SoftDeleteModel):
    class Statuses(models.TextChoices):
        PRESENT = 'PRESENT', 'Present'
        ABSENT = 'ABSENT', 'Absent'
        LATE = 'LATE', 'Late'
        HALF_DAY = 'HALF_DAY', 'Half Day'
        LEAVE = 'LEAVE', 'On Leave'
        HOLIDAY = 'HOLIDAY', 'Holiday'

    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    shift = models.ForeignKey(
        Shift,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    date = models.DateField()
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Statuses.choices,
        default=Statuses.PRESENT
    )
    captured_image = models.ImageField(upload_to='attendance_photos/', null=True, blank=True)
    total_worked_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    break_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Check-in GPS info
    check_in_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    check_in_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    check_in_accuracy = models.FloatField(null=True, blank=True)
    check_in_address = models.TextField(null=True, blank=True)
    check_in_device_info = models.CharField(max_length=255, null=True, blank=True)

    # Check-out GPS info
    check_out_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    check_out_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    check_out_accuracy = models.FloatField(null=True, blank=True)
    check_out_address = models.TextField(null=True, blank=True)
    check_out_device_info = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('employee', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.employee.username} - {self.date} - {self.status}"


class Overtime(SoftDeleteModel):
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='overtime_records'
    )
    attendance = models.ForeignKey(
        Attendance,
        on_delete=models.CASCADE,
        related_name='overtime_requests'
    )
    session = models.OneToOneField(
        'AttendanceSession',
        on_delete=models.CASCADE,
        related_name='overtime_request',
        null=True,
        blank=True
    )
    date = models.DateField()
    hours = models.DecimalField(max_digits=6, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending Approval'),
            ('APPROVED', 'Approved'),
            ('REJECTED', 'Rejected')
        ],
        default='PENDING'
    )
    shift_start = models.TimeField(null=True, blank=True)
    shift_end = models.TimeField(null=True, blank=True)
    actual_current_time = models.TimeField(null=True, blank=True)
    extra_working_time = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_overtimes'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee.username} - {self.date} - {self.hours} hrs"


class AttendanceSession(SoftDeleteModel):
    attendance = models.ForeignKey(
        Attendance,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    check_in_time = models.TimeField()
    check_out_time = models.TimeField(null=True, blank=True)
    captured_image = models.ImageField(upload_to='attendance_photos/', null=True, blank=True)
    check_out_captured_image = models.ImageField(upload_to='attendance_photos/', null=True, blank=True)
    
    # Overtime & Auto Checkout fields
    ot_request_created = models.BooleanField(default=False)
    ot_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending Approval'),
            ('APPROVED', 'Approved'),
            ('REJECTED', 'Rejected')
        ],
        null=True,
        blank=True
    )
    auto_checkout = models.BooleanField(default=False)
    checkout_reason = models.CharField(max_length=100, null=True, blank=True)
    regular_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    ot_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)

    # Check-in GPS
    check_in_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    check_in_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    check_in_accuracy = models.FloatField(null=True, blank=True)
    check_in_address = models.TextField(null=True, blank=True)
    check_in_device_info = models.CharField(max_length=255, null=True, blank=True)

    # Check-out GPS
    check_out_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    check_out_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    check_out_accuracy = models.FloatField(null=True, blank=True)
    check_out_address = models.TextField(null=True, blank=True)
    check_out_device_info = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Session of {self.attendance.employee.username} on {self.attendance.date}"


class StoredFile(models.Model):
    name = models.CharField(max_length=255, unique=True)
    content = models.BinaryField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'attendance_stored_file'

    def __str__(self):
        return self.name

