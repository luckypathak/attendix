import sys
import re

with open('../backend/attendix/apps/attendance/views.py', 'r') as f:
    content = f.read()

history_code = """
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
            
        return Response({
            'attendance_id': attendance.id,
            'date': date_str,
            'pings': data
        }, status=status.HTTP_200_OK)
"""

content = content.replace("    def check_out(self, request):", history_code + "\n    def check_out(self, request):")

with open('../backend/attendix/apps/attendance/views.py', 'w') as f:
    f.write(content)

