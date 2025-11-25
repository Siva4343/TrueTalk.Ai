# meetings/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (MeetingViewSet, ParticipantViewSet, ChatMessageViewSet,
                    ReminderViewSet, NotepadViewSet, RecordingViewSet, process_due_reminders)

router = DefaultRouter()
router.register(r'meetings', MeetingViewSet, basename='meeting')
router.register(r'participants', ParticipantViewSet, basename='participant')
router.register(r'messages', ChatMessageViewSet, basename='message')
router.register(r'reminders', ReminderViewSet, basename='reminder')
router.register(r'notepads', NotepadViewSet, basename='notepad')
router.register(r'recordings', RecordingViewSet, basename='recording')

urlpatterns = [
    path('Abh/', process_due_reminders, name='process_due_reminders'),
    path('api/', include(router.urls)),
]
