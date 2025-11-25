from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from contact import views as contacts_views

router = routers.DefaultRouter()
router.register(r'contacts', contacts_views.ContactViewSet)
router.register(r'shared-contact', contacts_views.SharedContactViewSet, basename='shared-contact')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/auth/', include('rest_framework.urls')),
    path('api/users/', contacts_views.UserListView.as_view(), name='user-list'),
]
