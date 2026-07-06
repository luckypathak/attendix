from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CompanyViewSet, DepartmentViewSet, DesignationViewSet, FirmViewSet, DashboardStatsView

router = DefaultRouter()
router.register('companies', CompanyViewSet, basename='company')
router.register('departments', DepartmentViewSet, basename='department')
router.register('designations', DesignationViewSet, basename='designation')
router.register('firms', FirmViewSet, basename='firm')

urlpatterns = [
    path('dashboard-stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('', include(router.urls)),
]
