from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from .models import Todo
from .serializers import TodoSerializer


class TodoViewSet(viewsets.ModelViewSet):
    queryset = Todo.objects.all()
    serializer_class = TodoSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['employee', 'is_completed']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'SUPER_ADMIN':
            return self.queryset
        if user.role in ['COMPANY_ADMIN', 'MANAGER']:
            return self.queryset.filter(employee__company=user.company)
        return self.queryset.filter(employee=user)

    def perform_create(self, serializer):
        # By default assign to current user
        employee_id = self.request.data.get('employee_id')
        if employee_id and self.request.user.role in ['SUPER_ADMIN', 'COMPANY_ADMIN', 'MANAGER']:
            # Managers can assign tasks to employees
            serializer.save(employee_id=employee_id)
        else:
            serializer.save(employee=self.request.user)

    @action(detail=True, methods=['post'], url_path='toggle-complete')
    def toggle_complete(self, request, pk=None):
        todo = self.get_object()
        todo.is_completed = not todo.is_completed
        todo.save()
        return Response(TodoSerializer(todo).data)
