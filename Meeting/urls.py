"""
URL Configuration for Video Meeting System - Pure DRF API
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Main router
router = DefaultRouter()
router.register(r'meetings', views.MeetingViewSet, basename='meeting')
router.register(r'teams', views.TeamViewSet, basename='team')
router.register(r'channels', views.ChannelViewSet, basename='channel')
router.register(r'channel-tabs', views.ChannelTabViewSet, basename='channeltab')
router.register(r'organizations', views.OrganizationViewSet, basename='organization')
router.register(r'profiles', views.UserProfileViewSet, basename='profile')
router.register(r'audit-logs', views.AuditLogViewSet, basename='auditlog')

urlpatterns = [
    # DRF Router URLs
    path('', include(router.urls)),
    
    # Auth Routes
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/me/', views.CurrentUserView.as_view(), name='current-user'),
    
    # Nested routes for meeting-specific resources
    path('meetings/<uuid:meeting_pk>/participants/', 
         views.ParticipantViewSet.as_view({'get': 'list'}), 
         name='meeting-participants-list'),
    path('meetings/<uuid:meeting_pk>/participants/<uuid:pk>/admit/', 
         views.ParticipantViewSet.as_view({'post': 'admit'}), 
         name='meeting-participants-admit'),
    path('meetings/<uuid:meeting_pk>/participants/<uuid:pk>/remove/', 
         views.ParticipantViewSet.as_view({'post': 'remove'}), 
         name='meeting-participants-remove'),
    path('meetings/<uuid:meeting_pk>/participants/<uuid:pk>/mute/', 
         views.ParticipantViewSet.as_view({'post': 'mute'}), 
         name='meeting-participants-mute'),
    path('meetings/<uuid:meeting_pk>/participants/mute_all/', 
         views.ParticipantViewSet.as_view({'post': 'mute_all'}), 
         name='meeting-participants-mute-all'),
    path('meetings/<uuid:meeting_pk>/participants/<uuid:pk>/make_cohost/', 
         views.ParticipantViewSet.as_view({'post': 'make_cohost'}), 
         name='meeting-participants-make-cohost'),
    path('meetings/<uuid:meeting_pk>/participants/<uuid:pk>/raise_hand/', 
         views.ParticipantViewSet.as_view({'post': 'raise_hand'}), 
         name='meeting-participants-raise-hand'),
    
    # Chat routes
    path('meetings/<uuid:meeting_pk>/chat/', 
         views.ChatViewSet.as_view({'get': 'list', 'post': 'create'}), 
         name='meeting-chat'),
    
    # Recording routes
    path('meetings/<uuid:meeting_pk>/recordings/', 
         views.RecordingViewSet.as_view({'get': 'list'}), 
         name='meeting-recordings-list'),
    path('meetings/<uuid:meeting_pk>/recordings/start/', 
         views.RecordingViewSet.as_view({'post': 'start'}), 
         name='meeting-recordings-start'),
    path('meetings/<uuid:meeting_pk>/recordings/<uuid:pk>/stop/', 
         views.RecordingViewSet.as_view({'post': 'stop'}), 
         name='meeting-recordings-stop'),
    
    # Reaction routes
    path('meetings/<uuid:meeting_pk>/reactions/', 
         views.ReactionViewSet.as_view({'post': 'create'}), 
         name='meeting-reactions'),
    
    # Simplified endpoints (no auth)
    path('create/', views.create_meeting_simple, name='create-meeting-simple'),
    path('<uuid:meeting_id>/join/', views.join_meeting_simple, name='join-meeting-simple'),
]
