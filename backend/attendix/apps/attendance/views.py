from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Shift, Attendance, Overtime
from .serializers import (
    ShiftSerializer, AttendanceSerializer, OvertimeSerializer,
    CheckInSerializer, CheckOutSerializer
)
from .services import AttendanceService

User = get_user_model()


class ShiftViewSet(viewsets.ModelViewSet):
    queryset = Shift.objects.all()
    serializer_class = ShiftSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'SUPER_ADMIN':
            return self.queryset
        return self.queryset.filter(company=user.company)

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['employee', 'date', 'status']

    from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        user = self.request.user
        base_qs = self.queryset.filter(employee__is_deleted=False, employee__is_active=True)
        if user.role == 'SUPER_ADMIN':
            firm_id = self.request.query_params.get('firm')
            if firm_id and firm_id != 'ALL' and firm_id != 'undefined':
                try:
                    base_qs = base_qs.filter(employee__firm_id=int(firm_id))
                except ValueError:
                    pass
            return base_qs
        if user.role == 'MANAGER':
            return base_qs.filter(employee__company=user.company, employee__firm=user.firm)
        if user.role == 'COMPANY_ADMIN':
            firm_id = self.request.query_params.get('firm')
            if firm_id and firm_id != 'ALL' and firm_id != 'undefined':
                try:
                    return base_qs.filter(employee__company=user.company, employee__firm_id=int(firm_id))
                except ValueError:
                    pass
            return base_qs.filter(employee__company=user.company)
        # Employee can only see their own attendance
        return base_qs.filter(employee=user)

    @action(detail=False, methods=['post'], url_path='check-in')
    def check_in(self, request):
        serializer = CheckInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            record = AttendanceService.check_in(
                employee=request.user,
                lat=serializer.validated_data['latitude'],
                lng=serializer.validated_data['longitude'],
                accuracy=serializer.validated_data.get('accuracy'),
                address=serializer.validated_data.get('address', ''),
                device_info=serializer.validated_data.get('device_info', ''),
                captured_image=serializer.validated_data['captured_image']
            )
            return Response(AttendanceSerializer(record, context={'request': request}).data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            msg = e.messages[0] if hasattr(e, 'messages') else str(e)
            if msg.startswith("['") and msg.endswith("']"):
                msg = msg[2:-2]
            return Response({"detail": msg}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='check-out')
    def check_out(self, request):
        serializer = CheckOutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            record = AttendanceService.check_out(
                employee=request.user,
                lat=serializer.validated_data['latitude'],
                lng=serializer.validated_data['longitude'],
                accuracy=serializer.validated_data.get('accuracy'),
                address=serializer.validated_data.get('address', ''),
                device_info=serializer.validated_data.get('device_info', ''),
                captured_image=serializer.validated_data['captured_image']
            )
            return Response(AttendanceSerializer(record, context={'request': request}).data, status=status.HTTP_200_OK)
        except ValidationError as e:
            msg = e.messages[0] if hasattr(e, 'messages') else str(e)
            if msg.startswith("['") and msg.endswith("']"):
                msg = msg[2:-2]
            return Response({"detail": msg}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='history')
    def history(self, request):
        # Fetch current month's history for current user
        today = timezone.localtime(timezone.now()).date()
        start_of_month = today.replace(day=1)
        records = Attendance.objects.filter(
            employee=request.user,
            date__gte=start_of_month,
            date__lte=today
        ).order_by('-date')
        return Response(AttendanceSerializer(records, many=True, context={'request': request}).data)

    @action(detail=True, methods=['post'], url_path='continue-shift')
    def continue_shift(self, request, pk=None):
        attendance = self.get_object()
        session = attendance.sessions.order_by('-created_at').first()
        if not session or session.check_out_time:
            return Response({"detail": "No active session found."}, status=status.HTTP_400_BAD_REQUEST)
        
        session.continue_shift = True
        session.continue_clicked_at = timezone.now()
        session.save()
        return Response({"detail": "Shift continued successfully."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='request-overtime')
    def request_overtime(self, request, pk=None):
        from attendix.apps.notifications.services import NotificationService
        attendance = self.get_object()
        session = attendance.sessions.order_by('-created_at').first()
        if not session or session.check_out_time:
            return Response({"detail": "No active session found."}, status=status.HTTP_400_BAD_REQUEST)
        
        if session.ot_requested:
             return Response({"detail": "Overtime already requested."}, status=status.HTTP_400_BAD_REQUEST)

        # We will create the OT request with 0 hours initially; the background checker updates it
        ot_req, created = Overtime.objects.get_or_create(
            employee=attendance.employee,
            attendance=attendance,
            session=session,
            date=attendance.date,
            defaults={
                'hours': 0.0,
                'status': 'PENDING',
                'shift_start': getattr(attendance.shift, 'start_time', None),
                'shift_end': getattr(attendance.shift, 'end_time', None),
                'actual_current_time': timezone.now().time(),
                'extra_working_time': 0.0
            }
        )

        session.ot_requested = True
        session.ot_requested_at = timezone.now()
        session.ot_request_created = True
        session.ot_status = 'PENDING'
        session.save()
        
        # Notify admins
        admins = User.objects.filter(company=attendance.employee.company, role__in=['SUPER_ADMIN', 'COMPANY_ADMIN', 'MANAGER'])
        profile = getattr(attendance.employee, 'employee_profile', None)
        if profile and profile.manager:
             admins = admins | User.objects.filter(id=profile.manager.id)
        
        for admin in admins.distinct():
            NotificationService.create_in_app_notification(
                recipient=admin,
                title="Overtime Request",
                body=f"Employee {attendance.employee.username} requested overtime approval."
            )
            
        return Response({"detail": "Overtime requested successfully."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='grant-ot')
    def grant_ot(self, request, pk=None):
        if request.user.role not in ['SUPER_ADMIN', 'COMPANY_ADMIN', 'MANAGER']:
            return Response({"detail": "Only managers/admins can pre-approve overtime."}, status=status.HTTP_403_FORBIDDEN)
        
        attendance = self.get_object()
        hours = request.data.get('hours', 2.0)
        
        try:
            hours = float(hours)
        except ValueError:
            return Response({"detail": "Invalid hours value."}, status=status.HTTP_400_BAD_REQUEST)
        
        session = attendance.sessions.order_by('-created_at').first()
        
        ot, created = Overtime.objects.update_or_create(
            employee=attendance.employee,
            attendance=attendance,
            session=session,
            date=attendance.date,
            defaults={
                'hours': hours,
                'status': 'APPROVED',
                'approved_by': request.user
            }
        )
        if session:
            session.ot_status = 'APPROVED'
            session.ot_request_created = True
            session.save()
            
            # Recalculate metrics on approval
            from .services import AttendanceService
            AttendanceService._recalculate_attendance_metrics(
                attendance,
                attendance.shift or AttendanceService.get_active_shift(attendance.employee),
                attendance.date
            )
        return Response(OvertimeSerializer(ot).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='analytics')
    def analytics(self, request):
        if request.user.role not in ['SUPER_ADMIN', 'COMPANY_ADMIN', 'MANAGER']:
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        employee_id = request.query_params.get('employee')
        branch_id = request.query_params.get('branch')
        month = request.query_params.get('month')
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')

        if request.user.role == 'SUPER_ADMIN':
            qs = Attendance.objects.all()
            employees = User.objects.filter(role='EMPLOYEE', is_deleted=False, is_active=True)
        else:
            qs = Attendance.objects.filter(employee__company=request.user.company)
            employees = User.objects.filter(company=request.user.company, role='EMPLOYEE', is_deleted=False, is_active=True)

        if request.user.role == 'MANAGER':
            qs = qs.filter(employee__firm=request.user.firm)
            employees = employees.filter(firm=request.user.firm)

        if employee_id and employee_id != 'ALL' and employee_id != 'undefined':
            try:
                qs = qs.filter(employee_id=int(employee_id))
            except ValueError:
                pass
        
        if branch_id and branch_id != 'ALL' and branch_id != 'undefined':
            try:
                qs = qs.filter(employee__firm_id=int(branch_id))
            except ValueError:
                pass

        import datetime
        if start_date_str:
            try:
                qs = qs.filter(date__gte=datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date())
            except ValueError:
                pass
        if end_date_str:
            try:
                qs = qs.filter(date__lte=datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date())
            except ValueError:
                pass
        
        if month:
            try:
                year_val, month_val = map(int, month.split('-'))
                qs = qs.filter(date__year=year_val, date__month=month_val)
            except ValueError:
                pass

        if request.user.role != 'MANAGER':
            if branch_id and branch_id != 'ALL' and branch_id != 'undefined':
                try:
                    employees = employees.filter(firm_id=int(branch_id))
                except ValueError:
                    pass

        if employee_id and employee_id != 'ALL' and employee_id != 'undefined':
            try:
                employees = employees.filter(id=int(employee_id))
            except ValueError:
                pass


        results = []
        for emp in employees:
            emp_qs = qs.filter(employee=emp)
            
            present_days = emp_qs.filter(status__in=[Attendance.Statuses.PRESENT, Attendance.Statuses.LATE, Attendance.Statuses.HALF_DAY]).count()
            absent_days = emp_qs.filter(status=Attendance.Statuses.ABSENT).count()
            leave_days = emp_qs.filter(status=Attendance.Statuses.LEAVE).count()

            from django.db.models import Sum
            total_working_hours = float(emp_qs.aggregate(total=Sum('total_worked_hours'))['total'] or 0.0)
            total_break_hours = float(emp_qs.aggregate(total=Sum('break_hours'))['total'] or 0.0)
            total_overtime_hours = float(emp_qs.aggregate(total=Sum('overtime_hours'))['total'] or 0.0)

            records = []
            for record in emp_qs.order_by('-date'):
                records.append(AttendanceSerializer(record, context={'request': request}).data)

            results.append({
                'employee_id': emp.id,
                'employee_username': emp.username,
                'employee_first_name': emp.first_name,
                'employee_last_name': emp.last_name,
                'branch_name': emp.firm.name if emp.firm else 'Default',
                'present_days': present_days,
                'absent_days': absent_days,
                'leave_days': leave_days,
                'total_working_hours': total_working_hours,
                'total_break_hours': total_break_hours,
                'total_overtime_hours': total_overtime_hours,
                'records': records
            })

        return Response(results)



class OvertimeViewSet(viewsets.ModelViewSet):
    queryset = Overtime.objects.all()
    serializer_class = OvertimeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['employee', 'status', 'date']

    def get_queryset(self):
        user = self.request.user
        base_qs = self.queryset.filter(employee__is_deleted=False, employee__is_active=True)
        if user.role == 'SUPER_ADMIN':
            firm_id = self.request.query_params.get('firm')
            if firm_id and firm_id != 'ALL' and firm_id != 'undefined':
                try:
                    base_qs = base_qs.filter(employee__firm_id=int(firm_id))
                except ValueError:
                    pass
            return base_qs
        if user.role == 'MANAGER':
            return base_qs.filter(employee__company=user.company, employee__firm=user.firm)
        if user.role == 'COMPANY_ADMIN':
            firm_id = self.request.query_params.get('firm')
            if firm_id and firm_id != 'ALL' and firm_id != 'undefined':
                try:
                    return base_qs.filter(employee__company=user.company, employee__firm_id=int(firm_id))
                except ValueError:
                    pass
            return base_qs.filter(employee__company=user.company)
        return base_qs.filter(employee=user)

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        if request.user.role not in ['SUPER_ADMIN', 'COMPANY_ADMIN', 'MANAGER']:
            return Response({"detail": "Only managers/admins can approve overtime."}, status=status.HTTP_403_FORBIDDEN)
        
        ot = self.get_object()
        ot.status = 'APPROVED'
        ot.approved_by = request.user
        ot.save()

        session = ot.session
        if session:
            session.ot_status = 'APPROVED'
            session.save()
            # Recalculate metrics on approval (especially if already checked out)
            from .services import AttendanceService
            AttendanceService._recalculate_attendance_metrics(
                session.attendance,
                session.attendance.shift or AttendanceService.get_active_shift(ot.employee),
                session.attendance.date
            )
        return Response(OvertimeSerializer(ot).data)

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        if request.user.role not in ['SUPER_ADMIN', 'COMPANY_ADMIN', 'MANAGER']:
            return Response({"detail": "Only managers/admins can reject overtime."}, status=status.HTTP_403_FORBIDDEN)
        
        ot = self.get_object()
        ot.status = 'REJECTED'
        ot.hours = 0.0
        ot.approved_by = request.user
        ot.save()

        session = ot.session
        if session:
            session.ot_status = 'REJECTED'
            
            # If still active, automatically check out employee
            if not session.check_out_time:
                from django.utils import timezone
                tz = timezone.get_current_timezone()
                now_dt = timezone.localtime(timezone.now())

                session.check_out_time = now_dt.time()
                session.auto_checkout = True
                session.checkout_reason = 'AUTO_CHECKOUT'
                session.save()

                attendance = session.attendance
                attendance.check_out_time = session.check_out_time
                attendance.save()
            else:
                session.save()

            from .services import AttendanceService
            AttendanceService._recalculate_attendance_metrics(
                session.attendance,
                session.attendance.shift or AttendanceService.get_active_shift(ot.employee),
                session.attendance.date
            )
        return Response(OvertimeSerializer(ot).data)
