from django.db import models
from django.contrib.auth.models import User
import uuid
from django.utils import timezone

class ChatRoom(models.Model):
    ROOM_TYPE_CHOICES = [
        ('direct', 'Direct Message'),
        ('group', 'Group Chat'),
        ('channel', 'Channel'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    room_type = models.CharField(max_length=10, choices=ROOM_TYPE_CHOICES, default='direct')
    participants = models.ManyToManyField(User, related_name='chat_rooms')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_rooms')
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.name} ({self.room_type})"

class Message(models.Model):
    MESSAGE_TYPE_CHOICES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File'),
        ('voice', 'Voice Message'),
        ('location', 'Location'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE_CHOICES, default='text')
    content = models.TextField()
    file = models.FileField(upload_to='chat_files/', null=True, blank=True)
    voice_note = models.FileField(upload_to='voice_notes/', null=True, blank=True)
    
    # Location fields
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    location_name = models.CharField(max_length=255, null=True, blank=True)
    
    # Message status
    is_deleted = models.BooleanField(default=False)
    deleted_for_all = models.BooleanField(default=False)
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='deleted_messages')
    
    # Read receipts
    read_by = models.ManyToManyField(User, related_name='read_messages', blank=True)
    
    # Reactions
    reactions = models.JSONField(default=dict)  # {'user_id': 'emoji'}
    
    # Forwarding
    is_forwarded = models.BooleanField(default=False)
    original_sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='original_messages')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}"
    
    @property
    def is_read(self):
        return self.read_by.exists()

class MessageReaction(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='message_reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    emoji = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['message', 'user']

class UserStatus(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='status')
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)
    typing_in = models.ForeignKey(ChatRoom, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {'Online' if self.is_online else 'Offline'}"

class ArchivedChat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='archived_chats')
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    archived_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'room']

class ChatBackup(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_backups')
    backup_file = models.FileField(upload_to='chat_backups/')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], default='pending')