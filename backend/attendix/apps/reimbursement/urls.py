from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReimbursementViewSet

router = DefaultRouter()
router.register('', ReimbursementViewSet, basename='reimbursement')

urlpatterns = [
    path('', include(router.urls)),
]
