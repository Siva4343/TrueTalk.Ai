from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CallSessionViewSet, CallLogViewSet, UserViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register('call-sessions', CallSessionViewSet, basename='call-sessions')
router.register('call-logs', CallLogViewSet, basename='call-logs')
router.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
