from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views


router = DefaultRouter()
router.register(r'rooms', views.ChatRoomViewSet)
router.register(r'rooms/(?P<room_id>[^/.]+)/messages', views.MessageViewSet, basename='message')

urlpatterns = [
    path('', include(router.urls)),
    path('search/', views.SearchView.as_view(), name='search'),
    path('backup/', views.BackupChatsView.as_view(), name='backup'),
]