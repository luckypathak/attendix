from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .models import Shift, Attendance, Overtime
from .serializers import (
    ShiftSerializer, AttendanceSerializer, OvertimeSerializer,
    CheckInSerializer, CheckOutSerializer
)
from .services import AttendanceService


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

    def get_queryset(self):
        user = self.request.user
        base_qs = self.queryset
        if user.role == 'SUPER_ADMIN':
            return base_qs
        if user.role == 'MANAGER':
            return base_qs.filter(employee__company=user.company, employee__firm=user.firm)
        if user.role == 'COMPANY_ADMIN':
            firm_id = self.request.query_params.get('firm')
            if firm_id and firm_id != 'ALL' and firm_id != 'undefined':
                return base_qs.filter(employee__company=user.company, employee__firm_id=firm_id)
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
                device_info=serializer.validated_data.get('device_info', '')
            )
            return Response(AttendanceSerializer(record).data, status=status.HTTP_201_CREATED)
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
                device_info=serializer.validated_data.get('device_info', '')
            )
            return Response(AttendanceSerializer(record).data, status=status.HTTP_200_OK)
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
        return Response(AttendanceSerializer(records, many=True).data)

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
        
        ot, created = Overtime.objects.update_or_create(
            employee=attendance.employee,
            attendance=attendance,
            date=attendance.date,
            defaults={
                'hours': hours,
                'status': 'APPROVED',
                'approved_by': request.user
            }
        )
        return Response(OvertimeSerializer(ot).data, status=status.HTTP_200_OK)


class OvertimeViewSet(viewsets.ModelViewSet):
    queryset = Overtime.objects.all()
    serializer_class = OvertimeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['employee', 'status', 'date']

    def get_queryset(self):
        user = self.request.user
        base_qs = self.queryset
        if user.role == 'SUPER_ADMIN':
            return base_qs
        if user.role == 'MANAGER':
            return base_qs.filter(employee__company=user.company, employee__firm=user.firm)
        if user.role == 'COMPANY_ADMIN':
            firm_id = self.request.query_params.get('firm')
            if firm_id and firm_id != 'ALL' and firm_id != 'undefined':
                return base_qs.filter(employee__company=user.company, employee__firm_id=firm_id)
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
        return Response(OvertimeSerializer(ot).data)

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        if request.user.role not in ['SUPER_ADMIN', 'COMPANY_ADMIN', 'MANAGER']:
            return Response({"detail": "Only managers/admins can reject overtime."}, status=status.HTTP_403_FORBIDDEN)
        
        ot = self.get_object()
        ot.status = 'REJECTED'
        ot.approved_by = request.user
        ot.save()
        return Response(OvertimeSerializer(ot).data)
