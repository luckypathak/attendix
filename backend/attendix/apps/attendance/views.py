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
    filterset_fields = ['date', 'status']

    from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        user = self.request.user
        base_qs = self.queryset.filter(employee__is_deleted=False, employee__is_active=True)
        
        # Apply custom filters first
        emp_name = self.request.query_params.get('employee')
        if emp_name:
            from django.db.models import Q
            base_qs = base_qs.filter(
                Q(employee__first_name__icontains=emp_name) | 
                Q(employee__last_name__icontains=emp_name) | 
                Q(employee__username__icontains=emp_name)
            )
        
        auto_checkout = self.request.query_params.get('autoCheckout')
        if auto_checkout == 'true':
            base_qs = base_qs.filter(sessions__auto_checkout=True).distinct()
        elif auto_checkout == 'false':
            base_qs = base_qs.filter(sessions__auto_checkout=False).distinct()

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

    @action(detail=False, methods=['get'], url_path='tracking-history')
    def tracking_history(self, request):
        employee_id = request.query_params.get('employee_id')
        date_str = request.query_params.get('date')
        
        if not employee_id or not date_str:
            return Response({"detail": "employee_id and date are required."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            from datetime import datetime
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({"detail": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
            
        attendance = Attendance.objects.filter(employee_id=employee_id, date=date_obj).first()
        if not attendance:
            return Response({"detail": "No attendance record found."}, status=status.HTTP_404_NOT_FOUND)
            
        from .models import LocationPing
        pings = LocationPing.objects.filter(session__attendance=attendance).order_by('timestamp')
        
        data = []
        for p in pings:
            data.append({
                'latitude': p.latitude,
                'longitude': p.longitude,
                'accuracy': p.accuracy,
                'speed': p.speed,
                'timestamp': p.timestamp,
                'is_stop': p.is_stop
            })
            
        active_session = attendance.sessions.last()
            
        return Response({
            'attendance_id': attendance.id,
            'date': date_str,
            'check_in_lat': active_session.check_in_lat if active_session else attendance.check_in_lat,
            'check_in_lng': active_session.check_in_lng if active_session else attendance.check_in_lng,
            'check_in_time': active_session.check_in_time if active_session else attendance.check_in_time,
            'check_out_lat': active_session.check_out_lat if active_session else attendance.check_out_lat,
            'check_out_lng': active_session.check_out_lng if active_session else attendance.check_out_lng,
            'check_out_time': active_session.check_out_time if active_session else attendance.check_out_time,
            'pings': data
        }, status=status.HTTP_200_OK)

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
        from django.utils import timezone
        today = timezone.localtime(timezone.now()).date()
        start_of_month = today.replace(day=1)
        records = Attendance.objects.filter(
            employee=request.user,
            date__gte=start_of_month,
            date__lte=today
        ).order_by('-date')
        return Response(AttendanceSerializer(records, many=True, context={'request': request}).data)

    @action(detail=False, methods=['get'], url_path='current')
    def current(self, request):
        from django.utils import timezone
        today = timezone.localtime(timezone.now()).date()
        attendance = Attendance.objects.filter(employee=request.user, date=today).first()
        
        is_clocked_in = False
        active_session = None
        
        if attendance:
            active_session_obj = attendance.sessions.filter(check_out_time__isnull=True).first()
            if active_session_obj:
                from .serializers import AttendanceSessionSerializer
                is_clocked_in = True
                active_session = AttendanceSessionSerializer(active_session_obj, context={'request': request}).data
                
        attendance_data = AttendanceSerializer(attendance, context={'request': request}).data if attendance else None
        
        return Response({
            "is_clocked_in": is_clocked_in,
            "attendance_record": attendance_data,
            "active_session": active_session
        })

    @action(detail=False, methods=['post'], url_path='ping')
    def ping(self, request):
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        speed = request.data.get('speed')
        accuracy = request.data.get('accuracy')
        
        if not latitude or not longitude:
            return Response({"detail": "Latitude and longitude required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except ValueError:
            return Response({"detail": "Invalid coordinates."}, status=status.HTTP_400_BAD_REQUEST)
            
        today = timezone.localtime(timezone.now()).date()
        attendance = Attendance.objects.filter(employee=request.user, date=today).first()
        if not attendance:
            return Response({"detail": "No active attendance."}, status=status.HTTP_400_BAD_REQUEST)
            
        session = attendance.sessions.filter(check_out_time__isnull=True).first()
        if not session:
            return Response({"detail": "No active session."}, status=status.HTTP_400_BAD_REQUEST)
            
        profile = getattr(request.user, 'employee_profile', None)
        work_category = profile.work_category if profile else 'OFFICE'
        company = request.user.company
        
        # ALL STAFF MUST BE TRACKED IN DB
        from .models import LocationPing
        LocationPing.objects.create(
            session=session,
            latitude=latitude,
            longitude=longitude,
            speed=speed,
            accuracy=accuracy
        )
        
        if work_category == 'FIELD':
            return Response({"detail": "Location ping saved."}, status=status.HTTP_200_OK)
        else:
            # OFFICE STAFF logic
            if session.check_in_lat and session.check_in_lng:
                import math
                def haversine(lat1, lon1, lat2, lon2):
                    R = 6371000 # Earth radius in meters
                    phi1 = math.radians(lat1)
                    phi2 = math.radians(lat2)
                    delta_phi = math.radians(lat2 - lat1)
                    delta_lambda = math.radians(lon2 - lon1)
                    a = math.sin(delta_phi/2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2.0)**2
                    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                    return R * c
                
                distance = haversine(float(session.check_in_lat), float(session.check_in_lng), latitude, longitude)
                office_radius = company.office_radius_meters if company else 100
                grace_period_mins = company.geofence_grace_period_minutes if company else 5
                
                if distance > office_radius:
                    if not session.out_of_office_since:
                        session.out_of_office_since = timezone.now()
                        session.save(update_fields=['out_of_office_since'])
                    else:
                        elapsed = (timezone.now() - session.out_of_office_since).total_seconds() / 60.0
                        if elapsed > grace_period_mins:
                            # Auto checkout
                            try:
                                AttendanceService.check_out(
                                    employee=request.user,
                                    lat=latitude,
                                    lng=longitude,
                                    accuracy=accuracy,
                                    address='',
                                    device_info='Auto Checkout - Geofence',
                                    captured_image=None
                                )
                                session.refresh_from_db()
                                session.checkout_reason = 'LEFT_OFFICE_GEOFENCE'
                                session.auto_checkout = True
                                session.save(update_fields=['checkout_reason', 'auto_checkout'])
                                
                                # Send Notification to Admin
                                from attendix.apps.notifications.services import NotificationService
                                admins = User.objects.filter(company=company, role__in=['SUPER_ADMIN', 'COMPANY_ADMIN'])
                                for admin in admins:
                                    NotificationService.create_notification(
                                        recipient=admin,
                                        title="Auto Checkout Alert",
                                        message=f"Employee {request.user.get_full_name() or request.user.username} was auto-checked out for leaving the office.",
                                        notification_type='SYSTEM_ALERT'
                                    )
                                return Response({"detail": "Auto checked out due to geofence.", "auto_checked_out": True}, status=status.HTTP_200_OK)
                            except Exception as e:
                                pass
                else:
                    if session.out_of_office_since:
                        session.out_of_office_since = None
                        session.save(update_fields=['out_of_office_since'])
                        
            return Response({"detail": "In office."}, status=status.HTTP_200_OK)


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

    @action(detail=False, methods=['patch'], url_path='edit-session')
    def edit_session(self, request):
        if request.user.role not in ['SUPER_ADMIN', 'COMPANY_ADMIN', 'MANAGER']:
            return Response({"detail": "Only managers/admins can edit attendance sessions."}, status=status.HTTP_403_FORBIDDEN)
        
        session_id = request.data.get('session_id')
        if not session_id:
            return Response({"detail": "session_id is required."}, status=status.HTTP_400_BAD_REQUEST)
            
        reason = request.data.get('reason')
        if not reason:
            return Response({"detail": "Reason is required for editing attendance."}, status=status.HTTP_400_BAD_REQUEST)
            
        from .models import AttendanceSession, AttendanceAuditLog
        try:
            session = AttendanceSession.objects.select_related('attendance').get(id=session_id)
        except AttendanceSession.DoesNotExist:
            return Response({"detail": "Session not found."}, status=status.HTTP_404_NOT_FOUND)
            
        # Ensure the admin has permission to edit this employee
        employee = session.attendance.employee
        if request.user.role == 'MANAGER' and (employee.company != request.user.company or employee.firm != request.user.firm):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        if request.user.role == 'COMPANY_ADMIN' and employee.company != request.user.company:
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
            
        old_value = {
            'check_in_time': str(session.check_in_time) if session.check_in_time else None,
            'check_out_time': str(session.check_out_time) if session.check_out_time else None,
            'status': session.attendance.status,
            'ot_status': session.ot_status,
            'continue_shift': session.continue_shift,
            'auto_checkout': session.auto_checkout,
            'check_in_address': session.check_in_address,
            'check_out_address': session.check_out_address,
            'captured_image': session.captured_image.name if session.captured_image else None,
            'check_out_captured_image': session.check_out_captured_image.name if session.check_out_captured_image else None,
        }
        
        import datetime
        def parse_time(t_str):
            if not t_str: return None
            try:
                # Handle HH:MM:SS or HH:MM
                parts = t_str.split(':')
                if len(parts) >= 2:
                    return datetime.time(int(parts[0]), int(parts[1]), int(parts[2]) if len(parts)>2 else 0)
            except Exception:
                pass
            return None
            
        if 'check_in_time' in request.data:
            parsed = parse_time(request.data['check_in_time'])
            if not parsed:
                return Response({"success": False, "message": "Invalid check-in time format."}, status=status.HTTP_400_BAD_REQUEST)
            session.check_in_time = parsed
            
        if 'check_out_time' in request.data:
            parsed = parse_time(request.data['check_out_time'])
            session.check_out_time = parsed
            
        # Validate logic: check-out cannot be before check-in
        if session.check_in_time and session.check_out_time:
            if session.check_out_time < session.check_in_time:
                return Response({"success": False, "message": "Checkout time cannot be earlier than Check-in time."}, status=status.HTTP_400_BAD_REQUEST)
                
        if 'ot_status' in request.data:
            session.ot_status = request.data['ot_status']
        if 'continue_shift' in request.data:
            # Handle string boolean from multipart/form-data
            val = request.data['continue_shift']
            session.continue_shift = str(val).lower() == 'true' if isinstance(val, str) else bool(val)
        if 'auto_checkout' in request.data:
            val = request.data['auto_checkout']
            session.auto_checkout = str(val).lower() == 'true' if isinstance(val, str) else bool(val)
            
        if 'check_in_address' in request.data:
            addr = request.data['check_in_address']
            session.check_in_address = addr if addr != 'null' else ''
        if 'check_out_address' in request.data:
            addr = request.data['check_out_address']
            session.check_out_address = addr if addr != 'null' else ''
            
        if 'captured_image' in request.FILES:
            session.captured_image = request.FILES['captured_image']
        if 'check_out_captured_image' in request.FILES:
            session.check_out_captured_image = request.FILES['check_out_captured_image']
            
        try:
            session.save()
        except Exception as e:
            return Response({"success": False, "message": f"Validation failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Optionally allow forcing a specific status on the parent attendance
        if 'status' in request.data:
            session.attendance.status = request.data['status']
            try:
                session.attendance.save()
            except Exception as e:
                return Response({"success": False, "message": f"Failed to save attendance status: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
            
        # Also sync parent attendance checkout time if this is the last session
        last_session = session.attendance.sessions.order_by('-check_in_time').first()
        if session.id == last_session.id:
            session.attendance.check_in_time = last_session.check_in_time
            session.attendance.check_out_time = last_session.check_out_time
            session.attendance.save()
            
        # Log the audit
        new_value = {
            'check_in_time': str(session.check_in_time) if session.check_in_time else None,
            'check_out_time': str(session.check_out_time) if session.check_out_time else None,
            'status': session.attendance.status,
            'ot_status': session.ot_status,
            'continue_shift': session.continue_shift,
            'auto_checkout': session.auto_checkout,
            'check_in_address': session.check_in_address,
            'check_out_address': session.check_out_address,
            'captured_image': session.captured_image.name if session.captured_image else None,
            'check_out_captured_image': session.check_out_captured_image.name if session.check_out_captured_image else None,
        }
        AttendanceAuditLog.objects.create(
            session=session,
            edited_by=request.user,
            old_value=old_value,
            new_value=new_value,
            reason=reason
        )
        
        # Recalculate metrics
        from .services import AttendanceService
        try:
            AttendanceService._recalculate_attendance_metrics(
                session.attendance,
                session.attendance.shift or AttendanceService.get_active_shift(employee),
                session.attendance.date
            )
        except Exception as e:
            # Even if recalculation throws a weird error, don't fail the 200 response since save succeeded, but log it
            import logging
            logging.error(f"Recalculation error: {str(e)}")
        
        return Response({"success": True, "message": "Attendance session updated successfully"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['delete'], url_path='delete-session')
    def delete_session(self, request):
        if request.user.role not in ['SUPER_ADMIN', 'COMPANY_ADMIN', 'MANAGER']:
            return Response({"detail": "Only managers/admins can delete attendance sessions."}, status=status.HTTP_403_FORBIDDEN)
            
        session_id = request.data.get('session_id')
        if not session_id:
            return Response({"detail": "session_id is required."}, status=status.HTTP_400_BAD_REQUEST)
            
        from .models import AttendanceSession, AttendanceAuditLog
        try:
            session = AttendanceSession.objects.select_related('attendance').get(id=session_id)
        except AttendanceSession.DoesNotExist:
            return Response({"detail": "Session not found."}, status=status.HTTP_404_NOT_FOUND)
            
        employee = session.attendance.employee
        if request.user.role == 'MANAGER' and (employee.company != request.user.company or employee.firm != request.user.firm):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        if request.user.role == 'COMPANY_ADMIN' and employee.company != request.user.company:
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
            
        attendance = session.attendance
        old_value = {'deleted': True, 'check_in_time': str(session.check_in_time), 'check_out_time': str(session.check_out_time)}
        
        session.delete()
        
        AttendanceAuditLog.objects.create(
            session=None,  # session is deleted
            edited_by=request.user,
            old_value=old_value,
            new_value={'deleted': True},
            reason="Admin deleted session"
        )
        
        # Recalculate metrics for the parent attendance
        from .services import AttendanceService
        AttendanceService._recalculate_attendance_metrics(
            attendance,
            attendance.shift or AttendanceService.get_active_shift(employee),
            attendance.date
        )
        
        return Response({"detail": "Session deleted successfully."}, status=status.HTTP_200_OK)

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
            qs = Attendance.objects.all().prefetch_related('sessions')
            employees = User.objects.filter(role='EMPLOYEE', is_deleted=False, is_active=True)
        else:
            qs = Attendance.objects.filter(employee__company=request.user.company).prefetch_related('sessions')
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
            total_working_hours = 0.0
            total_break_hours = float(emp_qs.aggregate(total=Sum('break_hours'))['total'] or 0.0)
            total_overtime_hours = float(emp_qs.aggregate(total=Sum('overtime_hours'))['total'] or 0.0)

            records = []
            for record in emp_qs.order_by('-date'):
                computed_hrs = float(record.computed_worked_hours)
                total_working_hours += computed_hrs
                records.append(AttendanceSerializer(record, context={'request': request}).data)
                
            total_working_hours = round(total_working_hours, 2)

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
                from .services import AttendanceService
                from .models import AttendanceAuditLog
                now_dt = timezone.localtime(timezone.now())

                session.check_out_time = now_dt.time()
                session.auto_checkout = True
                session.save()

                attendance = session.attendance
                attendance.check_out_time = session.check_out_time
                attendance.save()
                
                # Recalculate metrics correctly based on shift
                AttendanceService._recalculate_attendance_metrics(
                    attendance,
                    attendance.shift or AttendanceService.get_active_shift(ot.employee),
                    attendance.date
                )
                
                # Add Audit Log
                AttendanceAuditLog.objects.create(
                    session=session,
                    user=request.user,
                    old_value={"check_out_time": None},
                    new_value={"check_out_time": str(session.check_out_time), "auto_checkout": True},
                    reason="ADMIN_REJECTED_AUTO_CHECKOUT"
                )

            else:
                session.save()

            from .services import AttendanceService
            AttendanceService._recalculate_attendance_metrics(
                session.attendance,
                session.attendance.shift or AttendanceService.get_active_shift(ot.employee),
                session.attendance.date
            )
        return Response(OvertimeSerializer(ot).data)
