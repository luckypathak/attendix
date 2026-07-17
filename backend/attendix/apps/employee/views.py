from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import EmployeeProfile
from .serializers import EmployeeDetailsSerializer


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = EmployeeProfile.objects.all()
    serializer_class = EmployeeDetailsSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filter configurations
    filterset_fields = ['department', 'designation', 'manager']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    ordering_fields = ['joining_date', 'created_at']

    def get_queryset(self):
        user = self.request.user
        base_qs = self.queryset
        if user.role != 'SUPER_ADMIN':
            base_qs = base_qs.filter(user__company=user.company)

        if user.role == 'MANAGER':
            return base_qs.filter(user__firm=user.firm)

        # Admin optional query param scoping
        firm_id = self.request.query_params.get('firm')
        if firm_id and firm_id != 'ALL' and firm_id != 'undefined':
            try:
                base_qs = base_qs.filter(user__firm_id=int(firm_id))
            except ValueError:
                pass
            
        return base_qs


    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    from rest_framework.decorators import action
    from rest_framework.response import Response
    from rest_framework import status

    @action(detail=False, methods=['post'], url_path='bulk-transfer')
    def bulk_transfer(self, request):
        if request.user.role not in ['SUPER_ADMIN', 'COMPANY_ADMIN']:
            return Response({"detail": "Only admins can perform bulk transfers."}, status=status.HTTP_403_FORBIDDEN)
        
        employee_ids = request.data.get('employee_ids', [])
        firm_id = request.data.get('firm_id')

        if not employee_ids:
            return Response({"detail": "employee_ids are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Resolve target firm (firm_id can be None/null to clear firm assignment)
        firm = None
        if firm_id:
            from attendix.apps.company.models import Firm
            firm = Firm.objects.filter(id=firm_id).first()
            if not firm:
                return Response({"detail": "Target firm not found."}, status=status.HTTP_404_NOT_FOUND)

        # Resolve user IDs from employee profile IDs
        profiles = EmployeeProfile.objects.filter(id__in=employee_ids)
        user_ids = [p.user_id for p in profiles]
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        updated_count = User.objects.filter(id__in=user_ids).update(firm=firm)
        return Response({"detail": f"Successfully transferred {updated_count} employees."})
