from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from contact import views as contacts_views


router = DefaultRouter()
router.register(r'contacts', views.ContactViewSet)
router.register(r'shared-contacts', views.SharedContactViewSet, basename='shared-contacts')

urlpatterns = [
    path('', include(router.urls)),
]