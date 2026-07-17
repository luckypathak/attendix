import datetime
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import LeaveRequest, LeaveBalance
from attendix.apps.attendance.models import Attendance


class LeaveService:
    @staticmethod
    def calculate_work_days(start_date, end_date):
        # Return list of dates from start to end (inclusive)
        delta = end_date - start_date
        return [start_date + datetime.timedelta(days=i) for i in range(delta.days + 1)]

    @classmethod
    @transaction.atomic
    def approve_leave(cls, leave_request, approver, manager_comments="", is_paid=True):
        if leave_request.status != 'PENDING':
            raise ValidationError("This leave request has already been processed.")

        # Calculate days requested
        leave_days = cls.calculate_work_days(leave_request.start_date, leave_request.end_date)
        num_days = float(leave_request.get_leave_duration_days())

        # Deduct balance from EmployeeProfile if it is approved as a paid leave
        profile = leave_request.employee.employee_profile
        if is_paid:
            remaining = profile.allowed_leaves - profile.used_leaves
            if remaining < num_days:
                raise ValidationError(f"Insufficient leave balance. Remaining: {remaining}, Requested: {num_days}")
            profile.used_leaves = float(profile.used_leaves) + num_days
            profile.save()

        # Update request
        leave_request.status = 'APPROVED'
        leave_request.is_paid = is_paid
        leave_request.approved_by = approver
        leave_request.manager_comments = manager_comments
        leave_request.save()

        # Populate attendance records for the leave duration
        for date in leave_days:
            Attendance.objects.update_or_create(
                employee=leave_request.employee,
                date=date,
                defaults={
                    'status': Attendance.Statuses.LEAVE,
                    'check_in_address': f"Approved Leave: {leave_request.leave_type}"
                }
            )

        return leave_request

    @classmethod
    @transaction.atomic
    def reject_leave(cls, leave_request, approver, manager_comments=""):
        if leave_request.status != 'PENDING':
            raise ValidationError("This leave request has already been processed.")

        leave_request.status = 'REJECTED'
        leave_request.approved_by = approver
        leave_request.manager_comments = manager_comments
        leave_request.save()
        return leave_request

    @classmethod
    @transaction.atomic
    def unapprove_leave(cls, leave_request, approver):
        if leave_request.status not in ['APPROVED', 'REJECTED']:
            raise ValidationError("Only processed (Approved/Rejected) leave requests can be reverted.")

        if leave_request.status == 'APPROVED':
            # Calculate days requested
            leave_days = cls.calculate_work_days(leave_request.start_date, leave_request.end_date)
            num_days = float(leave_request.get_leave_duration_days())

            # Restore balance in EmployeeProfile if it was a paid leave
            if leave_request.is_paid:
                profile = leave_request.employee.employee_profile
                profile.used_leaves = max(0.0, float(profile.used_leaves) - num_days)
                profile.save()

            # Delete the attendance records that were marked as LEAVE for these dates
            Attendance.objects.filter(
                employee=leave_request.employee,
                date__in=leave_days,
                status=Attendance.Statuses.LEAVE
            ).delete()

        # Update request back to pending
        leave_request.status = 'PENDING'
        leave_request.approved_by = None
        leave_request.manager_comments = "Action reverted by manager"
        leave_request.save()

        return leave_request
