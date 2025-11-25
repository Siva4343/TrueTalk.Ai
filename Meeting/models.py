# Meeting/models.py
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Meeting(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    organizer = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='organized_meetings')
    start_at = models.DateTimeField()
    end_at = models.DateTimeField(null=True, blank=True)
    timezone = models.CharField(max_length=64, default='UTC')
    is_public = models.BooleanField(default=True)
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Participant(models.Model):
    STATUS_CHOICES = [('waiting','waiting'), ('connected','connected'), ('left','left'), ('rejected','rejected')]
    ROLE_CHOICES = [('host','host'), ('guest','guest')]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting = models.ForeignKey(Meeting, related_name='participants', on_delete=models.CASCADE)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='meeting_participations')
    name = models.CharField(max_length=255, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='guest')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    joined_at = models.DateTimeField(null=True, blank=True)
    left_at = models.DateTimeField(null=True, blank=True)

class ChatMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting = models.ForeignKey(Meeting, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    content = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Reaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting = models.ForeignKey(Meeting, related_name='reactions', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    emoji = models.CharField(max_length=64)
    target_message = models.ForeignKey(ChatMessage, null=True, blank=True, related_name='reactions', on_delete=models.CASCADE)
    target_participant = models.ForeignKey(Participant, null=True, blank=True, related_name='reactions', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class Notepad(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting = models.OneToOneField(Meeting, related_name='notepad', on_delete=models.CASCADE)
    content = models.TextField(blank=True)
    last_edited_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    updated_at = models.DateTimeField(auto_now=True)

class ScreenShareSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting = models.ForeignKey(Meeting, related_name='screenshares', on_delete=models.CASCADE)
    owner = models.ForeignKey(Participant, null=True, blank=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=False)
    started_at = models.DateTimeField(null=True, blank=True)
    stopped_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

class Reminder(models.Model):
    STATUS_CHOICES = [('scheduled','scheduled'), ('sent','sent'), ('cancelled','cancelled')]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting = models.ForeignKey(Meeting, related_name='reminders', on_delete=models.CASCADE)
    absolute_at = models.DateTimeField(null=True, blank=True)
    offset_minutes = models.IntegerField(null=True, blank=True)
    methods = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class MeetingRecording(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting = models.ForeignKey(Meeting, related_name='recordings', on_delete=models.CASCADE)
    url = models.URLField()
    duration_seconds = models.IntegerField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
