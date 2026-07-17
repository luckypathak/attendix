from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from .models import LeaveCategory, LeaveRequest, LeaveBalance, Holiday
from .serializers import LeaveCategorySerializer, LeaveRequestSerializer, LeaveBalanceSerializer, HolidaySerializer
from .services import LeaveService


class LeaveCategoryViewSet(viewsets.ModelViewSet):
    queryset = LeaveCategory.objects.all()
    serializer_class = LeaveCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'SUPER_ADMIN':
            return self.queryset
        return self.queryset.filter(company=user.company)

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)


class LeaveRequestViewSet(viewsets.ModelViewSet):
    queryset = LeaveRequest.objects.all()
    serializer_class = LeaveRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['employee', 'status', 'leave_type']

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

    def perform_create(self, serializer):
        serializer.save(employee=self.request.user)

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        if request.user.role not in ['SUPER_ADMIN', 'COMPANY_ADMIN', 'MANAGER']:
            return Response({"detail": "Only managers/admins can approve leaves."}, status=status.HTTP_403_FORBIDDEN)
        
        leave_req = self.get_object()
        manager_comments = request.data.get('manager_comments', '')
        is_paid = request.data.get('is_paid', True)
        try:
            LeaveService.approve_leave(leave_req, request.user, manager_comments, is_paid=is_paid)
            return Response(LeaveRequestSerializer(leave_req).data)
        except ValidationError as e:
            return Response({"detail": str(e.message if hasattr(e, 'message') else e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        if request.user.role not in ['SUPER_ADMIN', 'COMPANY_ADMIN', 'MANAGER']:
            return Response({"detail": "Only managers/admins can reject leaves."}, status=status.HTTP_403_FORBIDDEN)
        
        leave_req = self.get_object()
        manager_comments = request.data.get('manager_comments', '')
        try:
            LeaveService.reject_leave(leave_req, request.user, manager_comments)
            return Response(LeaveRequestSerializer(leave_req).data)
        except ValidationError as e:
            return Response({"detail": str(e.message if hasattr(e, 'message') else e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='unapprove')
    def unapprove(self, request, pk=None):
        if request.user.role not in ['SUPER_ADMIN', 'COMPANY_ADMIN', 'MANAGER']:
            return Response({"detail": "Only managers/admins can revert leave actions."}, status=status.HTTP_403_FORBIDDEN)
        
        leave_req = self.get_object()
        try:
            LeaveService.unapprove_leave(leave_req, request.user)
            return Response(LeaveRequestSerializer(leave_req).data)
        except ValidationError as e:
            return Response({"detail": str(e.message if hasattr(e, 'message') else e)}, status=status.HTTP_400_BAD_REQUEST)


class LeaveBalanceViewSet(viewsets.ModelViewSet):
    queryset = LeaveBalance.objects.all()
    serializer_class = LeaveBalanceSerializer
    permission_classes = [permissions.IsAuthenticated]

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


class HolidayViewSet(viewsets.ModelViewSet):
    queryset = Holiday.objects.all()
    serializer_class = HolidaySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'SUPER_ADMIN':
            return self.queryset
        return self.queryset.filter(company=user.company)

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)
