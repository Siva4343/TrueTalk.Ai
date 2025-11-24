from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BusinessProfileViewSet

router = DefaultRouter()
router.register(r'business-profiles', BusinessProfileViewSet)

urlpatterns = [
    path('', include(router.urls)),
]