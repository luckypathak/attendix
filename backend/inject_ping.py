import sys
import re

with open('../backend/attendix/apps/attendance/views.py', 'r') as f:
    content = f.read()

ping_code = """
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
        
        if work_category == 'FIELD':
            from .models import LocationPing
            LocationPing.objects.create(
                session=session,
                latitude=latitude,
                longitude=longitude,
                speed=speed,
                accuracy=accuracy
            )
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
"""

content = content.replace("    def history(self, request):", ping_code + "\n    def history(self, request):")

with open('../backend/attendix/apps/attendance/views.py', 'w') as f:
    f.write(content)

