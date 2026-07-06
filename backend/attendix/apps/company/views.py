from rest_framework import viewsets, permissions
from .models import Company, Department, Designation, Firm
from .serializers import CompanySerializer, DepartmentSerializer, DesignationSerializer, FirmSerializer


class IsCompanyAdminOrSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['SUPER_ADMIN', 'COMPANY_ADMIN']


class TenantModelViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'SUPER_ADMIN':
            return self.queryset
        
        # If model is Company itself, filter by pk
        if self.queryset.model == Company:
            return self.queryset.filter(pk=user.company_id)
            
        return self.queryset.filter(company=user.company)

    def perform_create(self, serializer):
        # Automatically assign company from user if not super admin
        if self.request.user.role != 'SUPER_ADMIN':
            serializer.save(company=self.request.user.company)
        else:
            serializer.save()


class CompanyViewSet(TenantModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    
    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            return [permissions.IsAdminUser()] # Only django staff / absolute superadmins can create companies
        return [IsCompanyAdminOrSuperAdmin()]


class DepartmentViewSet(TenantModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


class DesignationViewSet(TenantModelViewSet):
    queryset = Designation.objects.all()
    serializer_class = DesignationSerializer


class FirmViewSet(TenantModelViewSet):
    queryset = Firm.objects.all()
    serializer_class = FirmSerializer


from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from attendix.apps.employee.models import EmployeeProfile
from attendix.apps.attendance.models import Attendance
from attendix.apps.leave.models import LeaveRequest, LeaveBalance
from attendix.apps.todo.models import Todo

class DashboardStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.localdate()

        if user.role in ['SUPER_ADMIN', 'COMPANY_ADMIN', 'MANAGER']:
            # Admin Dashboard Metrics
            total_employees = EmployeeProfile.objects.filter(user__company=user.company).count()
            
            # Real checked-in today count
            checked_in = Attendance.objects.filter(
                employee__company=user.company,
                date=today
            ).count()
            
            # Real late arrivals count today
            late = Attendance.objects.filter(
                employee__company=user.company,
                date=today,
                status='LATE'
            ).count()
            
            # Real pending leaves count
            pending_leaves = LeaveRequest.objects.filter(
                employee__company=user.company,
                status='PENDING'
            ).count()

            return Response({
                "role": user.role,
                "stats": {
                    "totalEmployees": total_employees,
                    "checkedIn": checked_in,
                    "late": late,
                    "pendingLeaves": pending_leaves
                }
            })
        else:
            # Employee Dashboard Metrics
            attendance_today = Attendance.objects.filter(
                employee=user,
                date=today
            ).first()
            
            checked_in_time = attendance_today.check_in_time.strftime('%I:%M %p') if (attendance_today and attendance_today.check_in_time) else 'Pending'
            checked_out_time = attendance_today.check_out_time.strftime('%I:%M %p') if (attendance_today and attendance_today.check_out_time) else 'Pending'
            
            # Tasks completeness
            todos_today = Todo.objects.filter(employee=user).filter(Q(due_date=today) | Q(created_at__date=today))
            total_tasks = todos_today.count()
            completed_tasks = todos_today.filter(is_completed=True).count()
            task_completeness = f"{completed_tasks}/{total_tasks} Tasks Done" if total_tasks > 0 else "No Tasks Assigned"

            # Leaves remaining
            balances = LeaveBalance.objects.filter(employee=user)
            remaining_leaves_sum = sum(b.allocated - b.used for b in balances)
            remaining_leaves = f"{remaining_leaves_sum} Days Left"

            return Response({
                "role": user.role,
                "stats": {
                    "checkedInTime": checked_in_time,
                    "checkedOutTime": checked_out_time,
                    "taskCompleteness": task_completeness,
                    "remainingLeaves": remaining_leaves
                }
            })
