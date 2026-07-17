from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Reimbursement
from .serializers import ReimbursementSerializer


class ReimbursementViewSet(viewsets.ModelViewSet):
    queryset = Reimbursement.objects.all()
    serializer_class = ReimbursementSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['employee', 'status']

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
            return Response({"detail": "Only managers/admins can approve reimbursements."}, status=status.HTTP_403_FORBIDDEN)
        
        reimb = self.get_object()
        reimb.status = 'APPROVED'
        reimb.approved_by = request.user
        reimb.manager_comments = request.data.get('manager_comments', '')
        reimb.save()
        return Response(ReimbursementSerializer(reimb).data)

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        if request.user.role not in ['SUPER_ADMIN', 'COMPANY_ADMIN', 'MANAGER']:
            return Response({"detail": "Only managers/admins can reject reimbursements."}, status=status.HTTP_403_FORBIDDEN)
        
        reimb = self.get_object()
        reimb.status = 'REJECTED'
        reimb.approved_by = request.user
        reimb.manager_comments = request.data.get('manager_comments', '')
        reimb.save()
        return Response(ReimbursementSerializer(reimb).data)
