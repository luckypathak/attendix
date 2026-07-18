from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import EmployeeProfile
from .serializers import EmployeeDetailsSerializer


from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = EmployeeProfile.objects.filter(user__is_deleted=False, user__is_active=True)
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
            from django.db.models import Q
            try:
                base_qs = base_qs.filter(
                    Q(user__firm_id=int(firm_id)) | Q(firm_allocations__firm_id=int(firm_id))
                ).distinct()
            except ValueError:
                pass
        return base_qs

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

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

    @action(detail=False, methods=['post'], url_path='bulk-delete')
    def bulk_delete(self, request):
        if request.user.role not in ['SUPER_ADMIN', 'COMPANY_ADMIN']:
            return Response({"detail": "Only admins can perform bulk delete."}, status=status.HTTP_403_FORBIDDEN)
        
        employee_ids = request.data.get('employee_ids', [])
        if not employee_ids:
            return Response({"detail": "employee_ids are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve profiles
        profiles = EmployeeProfile.objects.filter(id__in=employee_ids)
        user_ids = [p.user_id for p in profiles]

        # Import related models to delete
        from attendix.apps.attendance.models import Attendance, Overtime, AttendanceSession
        from attendix.apps.leave.models import LeaveRequest, LeaveBalance
        from attendix.apps.payroll.models import Payroll, PayrollBranchBreakdown, AdvanceSalary
        from attendix.apps.reimbursement.models import Reimbursement
        from attendix.apps.todo.models import Todo
        from attendix.apps.employee.models import EmployeeFirmAllocation
        from attendix.apps.notifications.models import Notification
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        users = User.objects.filter(id__in=user_ids)
        from django.db import transaction

        with transaction.atomic():
            # Perform cascade deletion of all related objects
            AttendanceSession.objects.filter(attendance__employee_id__in=user_ids).delete()
            Attendance.objects.filter(employee_id__in=user_ids).delete()
            Overtime.objects.filter(employee_id__in=user_ids).delete()
            LeaveRequest.objects.filter(employee_id__in=user_ids).delete()
            LeaveBalance.objects.filter(employee_id__in=user_ids).delete()
            
            PayrollBranchBreakdown.objects.filter(payroll__employee_id__in=user_ids).delete()
            Payroll.objects.filter(employee_id__in=user_ids).delete()
            AdvanceSalary.objects.filter(employee_id__in=user_ids).delete()
            
            Reimbursement.objects.filter(employee_id__in=user_ids).delete()
            Todo.objects.filter(employee_id__in=user_ids).delete()
            EmployeeFirmAllocation.objects.filter(employee_profile__id__in=employee_ids).delete()
            Notification.objects.filter(recipient_id__in=user_ids).delete()

            # Delete Profiles
            profiles.delete()

            # Soft-delete the User objects
            for user in users:
                user.delete()

        return Response({"detail": f"Successfully deleted {len(employee_ids)} employees and their related records."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='reset-missed-counter')
    def reset_missed_counter(self, request, pk=None):
        if request.user.role not in ['SUPER_ADMIN', 'COMPANY_ADMIN', 'MANAGER']:
            return Response({"detail": "Only admins can reset the missed checkout counter."}, status=status.HTTP_403_FORBIDDEN)
            
        profile = self.get_object()
        profile.checkout_missed_count = 0
        profile.save(update_fields=['checkout_missed_count'])
        return Response({"detail": "Missed checkout counter reset successfully."}, status=status.HTTP_200_OK)

    def perform_destroy(self, instance):
        if instance.user:
            user_id = instance.user_id
            from attendix.apps.attendance.models import Attendance, Overtime, AttendanceSession
            from attendix.apps.leave.models import LeaveRequest, LeaveBalance
            from attendix.apps.payroll.models import Payroll, PayrollBranchBreakdown, AdvanceSalary
            from attendix.apps.reimbursement.models import Reimbursement
            from attendix.apps.todo.models import Todo
            from attendix.apps.employee.models import EmployeeFirmAllocation
            from attendix.apps.notifications.models import Notification
            from django.db import transaction
            
            with transaction.atomic():
                AttendanceSession.objects.filter(attendance__employee_id=user_id).delete()
                Attendance.objects.filter(employee_id=user_id).delete()
                Overtime.objects.filter(employee_id=user_id).delete()
                LeaveRequest.objects.filter(employee_id=user_id).delete()
                LeaveBalance.objects.filter(employee_id=user_id).delete()
                
                PayrollBranchBreakdown.objects.filter(payroll__employee_id=user_id).delete()
                Payroll.objects.filter(employee_id=user_id).delete()
                AdvanceSalary.objects.filter(employee_id=user_id).delete()
                
                Reimbursement.objects.filter(employee_id=user_id).delete()
                Todo.objects.filter(employee_id=user_id).delete()
                EmployeeFirmAllocation.objects.filter(employee_profile=instance).delete()
                Notification.objects.filter(recipient_id=user_id).delete()
                
                instance.user.delete()
                instance.delete()
        else:
            instance.delete()

