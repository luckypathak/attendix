from rest_framework import viewsets, permissions
from django_filters.rest_framework import DjangoFilterBackend
from .models import AuditLog
from .serializers import AuditLogSerializer


class IsAdminUserRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['SUPER_ADMIN', 'COMPANY_ADMIN']


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdminUserRole]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['action', 'model_name', 'user']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'SUPER_ADMIN':
            return self.queryset
        # Filter logs for users that belong to company
        return self.queryset.filter(user__company=user.company)
