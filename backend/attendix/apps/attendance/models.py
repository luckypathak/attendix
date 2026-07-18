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

    @property
    def computed_worked_hours(self):
        from django.utils import timezone
        import datetime
        intervals = []
        now = timezone.localtime(timezone.now())
        
        # We must recompute from sessions to guarantee no double counting
        for session in self.sessions.all():
            if not session.check_in_time:
                continue
            checkin_dt = datetime.datetime.combine(self.date, session.check_in_time)
            
            if session.check_out_time:
                checkout_date = self.date
                if session.check_out_time < session.check_in_time:
                    checkout_date += datetime.timedelta(days=1)
                checkout_dt = datetime.datetime.combine(checkout_date, session.check_out_time)
            else:
                # Active session (running time)
                checkout_dt = timezone.make_naive(now) if timezone.is_aware(now) else now
                
            intervals.append((checkin_dt, checkout_dt))
            
        if not intervals:
            return 0.00
            
        # Merge overlapping intervals
        intervals.sort(key=lambda x: x[0])
        merged = [intervals[0]]
        for current in intervals[1:]:
            last = merged[-1]
            if current[0] <= last[1]:
                merged[-1] = (last[0], max(last[1], current[1]))
            else:
                merged.append(current)
                
        total_seconds = 0
        for start, end in merged:
            diff = (end - start).total_seconds()
            if diff >= 60: # Ignore invalid 0 duration sessions
                total_seconds += diff
                
        return round(total_seconds / 3600.0, 2)


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

    class Meta:
        ordering = ['check_in_time']

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

    # Shift Continuation & Overtime Request fields
    continue_shift = models.BooleanField(default=False)
    continue_clicked_at = models.DateTimeField(null=True, blank=True)
    ot_requested = models.BooleanField(default=False)
    ot_requested_at = models.DateTimeField(null=True, blank=True)
    checkout_missed_count = models.IntegerField(default=0)

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

    # Smart location tracking for Office Staff
    out_of_office_since = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Session of {self.attendance.employee.username} on {self.attendance.date}"


class LocationPing(models.Model):
    session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.CASCADE,
        related_name='location_pings'
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    accuracy = models.FloatField(null=True, blank=True)
    speed = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_stop = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Ping for Session {self.session.id} at {self.timestamp}"


class StoredFile(models.Model):
    name = models.CharField(max_length=255, unique=True)
    content = models.BinaryField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'attendance_stored_file'

    def __str__(self):
        return self.name

class AttendanceAuditLog(models.Model):
    session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )
    edited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='attendance_edits'
    )
    edited_at = models.DateTimeField(auto_now_add=True)
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    reason = models.TextField()

    class Meta:
        ordering = ['-edited_at']

    def __str__(self):
        return f"Edit by {self.edited_by.username if self.edited_by else 'Unknown'} on session {self.session.id}"


class AttendanceCorrectionRequest(SoftDeleteModel):
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='attendance_corrections'
    )
    date = models.DateField()
    request_type = models.CharField(
        max_length=20,
        choices=[
            ('MISSED_IN', 'Missed Check In'),
            ('MISSED_OUT', 'Missed Check Out'),
            ('MISSED_BOTH', 'Missed Both Check In & Check Out')
        ]
    )
    reason = models.TextField()
    requested_check_in = models.TimeField(null=True, blank=True)
    requested_check_out = models.TimeField(null=True, blank=True)
    check_in_photo = models.ImageField(upload_to='correction_photos/', null=True, blank=True)
    check_out_photo = models.ImageField(upload_to='correction_photos/', null=True, blank=True)
    location_address = models.TextField(null=True, blank=True)
    attachment = models.FileField(upload_to='correction_attachments/', null=True, blank=True)
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending Approval'),
            ('APPROVED', 'Approved'),
            ('REJECTED', 'Rejected')
        ],
        default='PENDING'
    )
    
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_corrections'
    )
    rejected_reason = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee.username} - {self.get_request_type_display()} on {self.date}"

